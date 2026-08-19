from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import pytest
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

import tcc_prf_severity.modeling.final_interpretation as final_interpretation_module
from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.modeling.final_interpretation import (
    ContributionAudit,
    FinalInterpretationResult,
    FinalInterpretationSources,
    InterpretationContract,
    align_holdout_to_predictions,
    build_contribution_tables,
    build_contributions_by_outcome,
    build_error_analysis,
    build_interpretation_checklist,
    build_interpretation_summary,
    build_transformed_feature_mapping,
    calculate_native_contributions,
    load_and_validate_final_predictions,
    load_final_interpretation_sources,
    stable_logistic,
    validate_final_interpretation_sources,
    write_final_interpretation_tables,
)
from tcc_prf_severity.modeling.preprocessing import PreprocessingGroups, build_preprocessor


@pytest.fixture(scope="module")
def synthetic_model() -> tuple[Pipeline, PreprocessingGroups, pl.DataFrame, Any, pl.DataFrame]:
    categorical = (
        "month_name",
        "dia_semana",
        "hour",
        "uf",
        "br",
        "sentido_via",
        "condicao_metereologica",
        "tipo_pista",
        "uso_solo",
    )
    numeric = ("km",)
    binary = tuple(f"tracado_{index}" for index in range(12))
    groups = PreprocessingGroups(categorical, numeric, binary)
    rows = 24
    data: dict[str, Any] = {
        "month_name": ["Janeiro", "Fevereiro"] * 12,
        "dia_semana": ["segunda_feira", "terça_feira"] * 12,
        "hour": [8, 18] * 12,
        "uf": ["PR", "SC"] * 12,
        "br": [101, 116] * 12,
        "sentido_via": ["Crescente", "Decrescente"] * 12,
        "condicao_metereologica": ["Chuva_forte", "Céu Claro"] * 12,
        "tipo_pista": ["Dupla", "Simples"] * 12,
        "uso_solo": ["Sim", "Não"] * 12,
        "km": np.linspace(0.0, 230.0, rows),
    }
    for index, column in enumerate(binary):
        data[column] = [int((row + index) % 3 == 0) for row in range(rows)]
    frame = pl.DataFrame(data)
    target = np.asarray([row % 2 == 0 or row % 5 == 0 for row in range(rows)])
    pipeline = Pipeline(
        (
            ("preprocessor", build_preprocessor(groups)),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=2,
                    max_depth=2,
                    learning_rate=0.2,
                    objective="binary:logistic",
                    eval_metric="logloss",
                    tree_method="hist",
                    random_state=42,
                    n_jobs=1,
                ),
            ),
        )
    )
    pipeline.fit(frame, target)
    transformed = pipeline.named_steps["preprocessor"].transform(frame)
    mapping = build_transformed_feature_mapping(
        pipeline.named_steps["preprocessor"], groups, expected_feature_count=31
    )
    return pipeline, groups, frame, transformed, mapping


def _sources() -> FinalInterpretationSources:
    model_id = "phase_4c_xgboost_baseline"
    family = "xgboost_gradient_boosted_trees"
    sha = "a" * 64
    threshold = "0.5"
    evaluation = {
        "evaluation_status": "completed",
        "selected_model_id": model_id,
        "selected_model_family": family,
        "model_training_period": "2021-2024",
        "final_test_year": "2025",
        "model_artifact_sha256": sha,
        "model_artifact_path": "artifacts/models/final.pkl",
        "frozen_threshold": threshold,
        "threshold_source": "phase_4f",
        "final_rows": "4",
        "final_unique_ids": "4",
        "final_positive": "2",
        "final_negative": "2",
        "frozen_threshold_tn": "1",
        "frozen_threshold_fp": "1",
        "frozen_threshold_fn": "1",
        "frozen_threshold_tp": "1",
        "final_predictions_path": "predictions.parquet",
        "final_predictions_sha256": "b" * 64,
        "model_retrained": "false",
        "threshold_reselected": "false",
        "hyperparameter_tuning": "false",
        "calibration_model_fitted": "false",
        "final_test_used": "true",
        "final_evaluation_performed": "true",
    }
    manifest = {
        "refit_status": "completed",
        "selected_model_id": model_id,
        "selected_model_family": family,
        "model_artifact_sha256": sha,
        "model_artifact_path": "artifacts/models/final.pkl",
        "frozen_threshold": threshold,
        "predictor_count": "22",
        "transformed_feature_count": "226",
        "completed_boosting_rounds": "300",
    }
    return FinalInterpretationSources(
        final_evaluation=evaluation,
        threshold_evaluation=pl.DataFrame(
            {
                "threshold_role": ["frozen_threshold"],
                "threshold": [0.5],
                "rows": [4],
                "actual_positive": [2],
                "actual_negative": [2],
                "tn": [1],
                "fp": [1],
                "fn": [1],
                "tp": [1],
            }
        ),
        evaluation_checklist=pl.DataFrame({"status": ["PASS"]}),
        final_model_manifest=manifest,
        refit_checklist=pl.DataFrame({"status": ["PASS"]}),
        threshold_selection={
            "selected_model_id": model_id,
            "selected_model_family": family,
            "selected_threshold": threshold,
        },
        model_selection={
            "selected_model_id": model_id,
            "selected_model_family": family,
        },
    )


def _prediction_frame(year: int = 2025) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "id": ["a", "b", "c", "d"],
            "source_year": [year] * 4,
            "target_grave": [True, False, True, False],
            "predicted_probability_grave": [0.8, 0.7, 0.2, 0.1],
            "predicted_grave_frozen_threshold": [True, True, False, False],
        }
    )


def _contract(path: str, sha256: str) -> InterpretationContract:
    return InterpretationContract(
        selected_model_id="model",
        selected_model_family="family",
        final_rows=4,
        final_positive=2,
        final_negative=2,
        frozen_threshold=0.5,
        pipeline_sha256="a" * 64,
        predictions_path=path,
        predictions_sha256=sha256,
        tp=1,
        fp=1,
        fn=1,
        tn=1,
    )


def test_phase_4h_sources_are_required(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Fontes autoritativas ausentes"):
        load_final_interpretation_sources(tmp_path, required_documents=())


def test_valid_frozen_sources_are_accepted() -> None:
    contract = validate_final_interpretation_sources(_sources())
    assert contract.final_rows == 4
    assert contract.frozen_threshold == 0.5


def test_pipeline_sha_divergence_between_4g_and_4h_is_rejected() -> None:
    sources = _sources()
    sources.final_model_manifest["model_artifact_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="pipeline_sha256"):
        validate_final_interpretation_sources(sources)


def test_retrospective_change_flags_are_rejected() -> None:
    sources = _sources()
    sources.final_evaluation["threshold_reselected"] = "true"
    with pytest.raises(ValueError, match="threshold_reselected"):
        validate_final_interpretation_sources(sources)


def test_predictions_sha_divergence_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "predictions.parquet"
    _prediction_frame().write_parquet(path)
    with pytest.raises(ValueError, match="SHA-256 das predictions"):
        load_and_validate_final_predictions(_contract(path.name, "0" * 64), tmp_path)


def test_valid_predictions_are_loaded_from_tmp_path(tmp_path: Path) -> None:
    path = tmp_path / "predictions.parquet"
    _prediction_frame().write_parquet(path)
    loaded = load_and_validate_final_predictions(_contract(path.name, sha256_file(path)), tmp_path)
    assert loaded.equals(_prediction_frame())


@pytest.mark.parametrize("year", [2021, 2022, 2023, 2024])
def test_only_2025_is_permitted_in_predictions(tmp_path: Path, year: int) -> None:
    path = tmp_path / f"predictions-{year}.parquet"
    _prediction_frame(year).write_parquet(path)
    contract = _contract(path.name, sha256_file(path))
    with pytest.raises(ValueError, match="somente 2025"):
        load_and_validate_final_predictions(contract, tmp_path)


def test_frozen_threshold_decisions_cannot_change(tmp_path: Path) -> None:
    path = tmp_path / "predictions.parquet"
    changed = _prediction_frame().with_columns(
        pl.Series("predicted_grave_frozen_threshold", [False, True, False, False])
    )
    changed.write_parquet(path)
    with pytest.raises(ValueError, match="threshold 4F"):
        load_and_validate_final_predictions(_contract(path.name, sha256_file(path)), tmp_path)


def test_holdout_is_aligned_by_id_with_frozen_predictions() -> None:
    predictions = _prediction_frame()
    holdout = predictions.select("id", "source_year", "target_grave")
    aligned = align_holdout_to_predictions(holdout.reverse(), predictions)
    assert aligned.equals(holdout)


def test_holdout_target_divergence_is_rejected() -> None:
    predictions = _prediction_frame()
    holdout = predictions.select("id", "source_year", "target_grave").with_columns(
        pl.when(pl.col("id") == "a")
        .then(False)
        .otherwise(pl.col("target_grave"))
        .alias("target_grave")
    )
    with pytest.raises(ValueError, match="Ano/target"):
        align_holdout_to_predictions(holdout, predictions)


def test_ohe_mapping_is_robust_to_underscores(
    synthetic_model: tuple[Pipeline, PreprocessingGroups, pl.DataFrame, Any, pl.DataFrame],
) -> None:
    _, groups, _, _, mapping = synthetic_model
    row = mapping.filter(
        (pl.col("source_predictor") == "condicao_metereologica")
        & (pl.col("category_or_level") == "Chuva_forte")
    )
    assert row.height == 1
    assert mapping["source_predictor"].n_unique() == len(groups.predictors) == 22


def test_numeric_and_binary_features_are_mapped_correctly(
    synthetic_model: tuple[Pipeline, PreprocessingGroups, pl.DataFrame, Any, pl.DataFrame],
) -> None:
    _, _, _, _, mapping = synthetic_model
    assert mapping.filter(pl.col("predictor_group") == "numeric")["source_predictor"].to_list() == [
        "km"
    ]
    binary = mapping.filter(pl.col("predictor_group") == "binary")
    assert binary.height == 12
    assert set(binary["category_or_level"]) == {""}


def test_total_mapped_features_is_enforced(
    synthetic_model: tuple[Pipeline, PreprocessingGroups, pl.DataFrame, Any, pl.DataFrame],
) -> None:
    pipeline, groups, _, _, _ = synthetic_model
    with pytest.raises(ValueError, match="Mapeamento transformado incompleto"):
        build_transformed_feature_mapping(
            pipeline.named_steps["preprocessor"], groups, expected_feature_count=32
        )


def test_stable_logistic_handles_extreme_margins() -> None:
    probabilities = stable_logistic(np.asarray([-1000.0, 0.0, 1000.0]))
    assert probabilities[0] == 0.0
    assert probabilities[1] == 0.5
    assert probabilities[2] == 1.0


def test_native_contributions_include_and_separate_bias(
    synthetic_model: tuple[Pipeline, PreprocessingGroups, pl.DataFrame, Any, pl.DataFrame],
) -> None:
    pipeline, _, frame, transformed, mapping = synthetic_model
    probabilities = pipeline.predict_proba(frame)[:, 1]
    audit = calculate_native_contributions(
        pipeline,
        transformed,
        probabilities,
        expected_feature_count=mapping.height,
    )
    assert audit.feature_contributions.shape == (frame.height, mapping.height)
    assert audit.bias.shape == (frame.height,)
    margins = audit.bias + audit.feature_contributions.sum(axis=1)
    np.testing.assert_allclose(stable_logistic(margins), probabilities, atol=1e-6, rtol=0)


def test_probability_divergence_blocks_interpretation(
    synthetic_model: tuple[Pipeline, PreprocessingGroups, pl.DataFrame, Any, pl.DataFrame],
) -> None:
    pipeline, _, frame, transformed, mapping = synthetic_model
    probabilities = pipeline.predict_proba(frame)[:, 1] + 0.01
    with pytest.raises(ValueError, match="não reconciliam"):
        calculate_native_contributions(
            pipeline,
            transformed,
            probabilities,
            expected_feature_count=mapping.height,
        )


def test_global_aggregation_ranks_by_absolute_magnitude_and_shares_sum_to_one() -> None:
    mapping = pl.DataFrame(
        {
            "transformed_feature": ["a_1", "a_2", "b"],
            "source_predictor": ["a", "a", "b"],
            "predictor_group": ["categorical", "categorical", "numeric"],
            "category_or_level": ["1", "2", ""],
        }
    )
    contributions = np.asarray([[2.0, -2.0, 1.0], [-2.0, 2.0, 1.0]])
    global_table, transformed = build_contribution_tables(contributions, mapping)
    assert global_table["source_predictor"].to_list() == ["a", "b"]
    assert global_table["mean_signed_margin_contribution"][0] == 0.0
    assert np.isclose(float(global_table["share_of_total_mean_abs_contribution"].sum()), 1.0)
    assert transformed.height == mapping.height
    assert transformed["rank"].to_list() == [1, 2, 3]


def test_error_analysis_reconciles_all_outcomes_and_percentiles() -> None:
    table, outcomes = build_error_analysis(_prediction_frame())
    assert table["outcome"].to_list() == ["TP", "FP", "FN", "TN"]
    assert table["rows"].to_list() == [1, 1, 1, 1]
    assert outcomes.tolist() == ["TP", "FP", "FN", "TN"]
    assert table["median_probability"].to_list() == [0.8, 0.7, 0.2, 0.1]
    assert np.isclose(float(table["share_of_final_rows"].sum()), 1.0)


def test_contributions_by_outcome_has_predictor_outcome_cartesian_product() -> None:
    mapping = pl.DataFrame(
        {
            "transformed_feature": ["a", "b"],
            "source_predictor": ["a", "b"],
            "predictor_group": ["numeric", "binary"],
            "category_or_level": ["", ""],
        }
    )
    contributions = np.asarray([[1.0, -1.0], [2.0, -2.0], [3.0, -3.0], [4.0, -4.0]])
    _, outcomes = build_error_analysis(_prediction_frame())
    table = build_contributions_by_outcome(contributions, mapping, outcomes)
    assert table.height == 8
    assert set(table["outcome"]) == {"TP", "FP", "FN", "TN"}


def _checklist_inputs() -> tuple[
    InterpretationContract,
    ContributionAudit,
    pl.DataFrame,
    pl.DataFrame,
    pl.DataFrame,
    pl.DataFrame,
]:
    contract = _contract("predictions.parquet", "b" * 64)
    audit = ContributionAudit(
        feature_contributions=np.zeros((4, 226)),
        bias=np.zeros(4),
        reconstructed_probabilities=np.full(4, 0.5),
        maximum_probability_error=0.0,
        mean_probability_error=0.0,
    )
    sources = [f"p{index % 22}" for index in range(226)]
    mapping = pl.DataFrame(
        {
            "transformed_feature": [f"f{index}" for index in range(226)],
            "source_predictor": sources,
            "predictor_group": ["categorical"] * 226,
            "category_or_level": [""] * 226,
        }
    )
    global_table = pl.DataFrame(
        {
            "rank": list(range(1, 23)),
            "source_predictor": [f"p{index}" for index in range(22)],
            "predictor_group": ["categorical"] * 22,
            "transformed_feature_count": [1] * 22,
            "mean_abs_margin_contribution": [1.0] * 22,
            "mean_signed_margin_contribution": [0.0] * 22,
            "share_of_total_mean_abs_contribution": [1 / 22] * 22,
        }
    )
    transformed = mapping.with_columns(
        pl.int_range(1, 227).alias("rank"),
        pl.lit(0.0).alias("mean_abs_margin_contribution"),
        pl.lit(0.0).alias("mean_signed_margin_contribution"),
    )
    errors, _ = build_error_analysis(_prediction_frame())
    return contract, audit, mapping, global_table, transformed, errors


def test_low_performance_does_not_create_checklist_failure() -> None:
    inputs = _checklist_inputs()
    checklist = build_interpretation_checklist(*inputs)
    assert checklist.height == 25
    assert set(checklist["status"]) == {"PASS"}


def test_summary_is_explicitly_post_evaluation_and_non_causal() -> None:
    contract, audit, _, global_table, _, _ = _checklist_inputs()
    summary = {
        row["key"]: row["value"]
        for row in build_interpretation_summary(contract, audit, global_table).iter_rows(named=True)
    }
    assert summary["post_final_evaluation_interpretation"] == "true"
    assert summary["causal_interpretation"] == "false"
    assert summary["features_modified"] == "false"


def test_production_flow_contains_no_training_or_new_prediction_calls() -> None:
    source = Path(final_interpretation_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_attributes = {"fit", "fit_transform", "partial_fit", "predict_proba"}
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called.isdisjoint(forbidden_attributes)
    assert "build_xgboost_pipeline" not in source
    assert "run_final_refit" not in source
    assert "run_final_evaluation" not in source


def test_tables_are_written_only_inside_tmp_path(tmp_path: Path) -> None:
    contract, audit, mapping, global_table, transformed, errors = _checklist_inputs()
    checklist = build_interpretation_checklist(
        contract, audit, mapping, global_table, transformed, errors
    )
    result = FinalInterpretationResult(
        contract=contract,
        global_contributions=global_table,
        transformed_contributions=transformed,
        error_analysis=errors,
        contributions_by_outcome=pl.DataFrame(
            {
                "source_predictor": ["p0"],
                "outcome": ["TP"],
                "rows": [1],
                "mean_abs_margin_contribution": [0.0],
                "mean_signed_margin_contribution": [0.0],
            }
        ),
        summary=build_interpretation_summary(contract, audit, global_table),
        checklist=checklist,
    )
    output = tmp_path / "tables"
    paths = write_final_interpretation_tables(result, output)
    assert len(paths) == 6
    assert all(path.parent == output for path in paths)
    assert not list(output.glob("*.tmp"))
