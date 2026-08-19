from __future__ import annotations

import platform
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import pytest
import sklearn
import xgboost
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.modeling import final_evaluation
from tcc_prf_severity.modeling.final_evaluation import (
    EXPECTED_FINAL_POSITIVE,
    EXPECTED_FINAL_ROWS,
    EXPECTED_MODEL_SHA256,
    FINAL_TEST_YEAR,
    FinalEvaluationInputs,
    FinalEvaluationResult,
    InternalReferences,
    build_calibration_table,
    build_development_comparison,
    build_final_evaluation_checklist,
    build_final_evaluation_table,
    build_final_predictions,
    calculate_probability_metrics,
    generate_final_probabilities,
    load_final_evaluation_inputs,
    load_final_holdout,
    load_validated_frozen_pipeline,
    persist_final_predictions,
    validate_final_holdout,
    validate_final_predictions,
    validate_pre_evaluation_sources,
    write_final_evaluation_tables,
)
from tcc_prf_severity.modeling.final_refit import (
    FROZEN_THRESHOLD_TEXT,
    persist_final_pipeline,
)
from tcc_prf_severity.modeling.model_comparison import XGBOOST_MODEL_ID
from tcc_prf_severity.modeling.preprocessing import PreprocessingGroups, build_preprocessor
from tcc_prf_severity.modeling.threshold_selection import (
    REFERENCE_THRESHOLD,
    SELECTED_MODEL_FAMILY,
    evaluate_threshold,
)

CATEGORICAL = (
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
BINARY = (
    "tracado_aclive",
    "tracado_curva",
    "tracado_declive",
    "tracado_desvio_temporario",
    "tracado_em_obras",
    "tracado_intersecao_de_vias",
    "tracado_ponte",
    "tracado_reta",
    "tracado_retorno_regulamentado",
    "tracado_rotatoria",
    "tracado_tunel",
    "tracado_viaduto",
)
GROUPS = PreprocessingGroups(CATEGORICAL, ("km",), BINARY)


def _dataset() -> pl.DataFrame:
    years = np.repeat(np.arange(2021, 2026), 12)
    total = len(years)
    data: dict[str, object] = {
        "id": [f"{year}-{index}" for year in range(2021, 2026) for index in range(12)],
        "source_year": years,
        "target_grave": np.asarray([(index % 3) == 0 for index in range(total)]),
        "month_name": np.resize(np.asarray(["Janeiro", "Fevereiro", "Março"]), total),
        "dia_semana": np.resize(
            np.asarray(["segunda-feira", "terça-feira", "quarta-feira"]), total
        ),
        "hour": np.arange(total) % 24,
        "uf": np.resize(np.asarray(["SP", "MG", "PR"]), total),
        "br": np.resize(np.asarray([101, 116, 381]), total),
        "sentido_via": np.resize(np.asarray(["Crescente", "Decrescente", "Não Informado"]), total),
        "condicao_metereologica": np.resize(np.asarray(["Chuva", "Céu Claro", "Nublado"]), total),
        "tipo_pista": np.resize(np.asarray(["Simples", "Dupla", "Múltipla"]), total),
        "uso_solo": np.resize(np.asarray(["Sim", "Não", "Não"]), total),
        "km": np.linspace(0.0, 500.0, total),
    }
    for index, column in enumerate(BINARY):
        data[column] = (np.arange(total) + index) % 2
    return pl.DataFrame(data)


def _holdout() -> pl.DataFrame:
    return _dataset().filter(pl.col("source_year") == FINAL_TEST_YEAR)


def _partition(holdout: pl.DataFrame | None = None) -> dict[str, Any]:
    if holdout is None:
        return {
            "partition_id": "final_test",
            "partition_role": "final_evaluation",
            "years": "2025",
            "rows": EXPECTED_FINAL_ROWS,
            "severe": EXPECTED_FINAL_POSITIVE,
            "non_severe": EXPECTED_FINAL_ROWS - EXPECTED_FINAL_POSITIVE,
        }
    positive = int(holdout["target_grave"].sum())
    return {
        "partition_id": "final_test",
        "partition_role": "final_evaluation",
        "years": "2025",
        "rows": holdout.height,
        "severe": positive,
        "non_severe": holdout.height - positive,
    }


def _pipeline() -> Pipeline:
    return Pipeline(
        (
            ("preprocessor", build_preprocessor(GROUPS)),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=2,
                    learning_rate=0.1,
                    max_depth=2,
                    objective="binary:logistic",
                    eval_metric="logloss",
                    tree_method="hist",
                    device="cpu",
                    n_jobs=1,
                    random_state=42,
                    verbosity=0,
                ),
            ),
        )
    )


@pytest.fixture(scope="module")
def frozen_bundle(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Pipeline, Path, dict[str, str]]:
    source = _dataset().filter(pl.col("source_year") < FINAL_TEST_YEAR)
    pipeline = _pipeline()
    pipeline.fit(source.select(GROUPS.predictors), source["target_grave"])
    path = tmp_path_factory.mktemp("frozen") / "models" / "pipeline.pkl"
    sha256, size = persist_final_pipeline(pipeline, path)
    preprocessor = pipeline.named_steps["preprocessor"]
    manifest = {
        "model_artifact_path": "models/pipeline.pkl",
        "model_artifact_sha256": sha256,
        "model_artifact_size_bytes": str(size),
        "completed_boosting_rounds": "2",
        "transformed_feature_count": str(len(preprocessor.get_feature_names_out())),
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "xgboost_version": xgboost.__version__,
        "polars_version": pl.__version__,
    }
    return pipeline, path, manifest


def _inputs() -> FinalEvaluationInputs:
    ap = np.asarray([0.3, 0.4, 0.5])
    roc = np.asarray([0.6, 0.7, 0.8])
    brier = np.asarray([0.22, 0.20, 0.18])
    return FinalEvaluationInputs(
        final_model_manifest={
            "refit_status": "completed",
            "selected_model_id": XGBOOST_MODEL_ID,
            "selected_model_family": SELECTED_MODEL_FAMILY,
            "training_period": "2021-2024",
            "predictor_count": "22",
            "completed_boosting_rounds": "300",
            "all_rounds_completed": "true",
            "transformed_feature_count": "226",
            "threshold_source": "phase_4f",
            "frozen_threshold": FROZEN_THRESHOLD_TEXT,
            "model_artifact_path": "artifacts/models/phase_4g_xgboost_final_pipeline.pkl",
            "model_artifact_sha256": EXPECTED_MODEL_SHA256,
            "final_test_year": "2025_reserved",
            "final_test_used": "false",
            "final_evaluation_performed": "false",
            "hyperparameter_tuning": "false",
            "early_stopping": "false",
        },
        refit_checklist=pl.DataFrame(
            {"check_id": [f"REF{index:03d}" for index in range(1, 17)], "status": ["PASS"] * 16}
        ),
        threshold_selection={
            "selection_status": "selected",
            "selected_model_id": XGBOOST_MODEL_ID,
            "selected_model_family": SELECTED_MODEL_FAMILY,
            "selected_threshold": FROZEN_THRESHOLD_TEXT,
            "selected_precision": "0.33",
            "selected_recall": "0.77",
            "selected_f1": "0.46",
            "final_test_used": "false",
            "refit_performed": "false",
        },
        model_selection={
            "selection_status": "selected",
            "selected_model_id": XGBOOST_MODEL_ID,
            "selected_model_family": SELECTED_MODEL_FAMILY,
            "final_test_used": "false",
            "refit_performed": "false",
        },
        model_comparison=pl.DataFrame(
            {
                "model_id": [XGBOOST_MODEL_ID],
                "ap_unweighted_mean": [float(np.mean(ap))],
                "ap_fold3": [0.5],
                "mean_roc_auc": [float(np.mean(roc))],
                "mean_brier_score": [float(np.mean(brier))],
            }
        ),
        fold_metrics=pl.DataFrame(
            {
                "fold": [1, 2, 3],
                "validation_year": [2022, 2023, 2024],
                "average_precision": ap,
                "roc_auc": roc,
                "brier_score": brier,
            }
        ),
        final_partition=_partition(),
    )


def test_manifest_4g_is_mandatory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="manifesto 4G"):
        load_final_evaluation_inputs(tmp_path)


def test_pre_evaluation_sources_are_validated_and_references_are_derived() -> None:
    references = validate_pre_evaluation_sources(_inputs())

    assert references.ap_mean == pytest.approx(0.4)
    assert references.ap_fold3 == 0.5
    assert references.mean_roc_auc == pytest.approx(0.7)
    assert references.mean_brier_score == pytest.approx(0.2)
    assert references.oof_f1 == 0.46


def test_threshold_divergence_is_rejected_before_evaluation() -> None:
    inputs = _inputs()
    divergent = inputs.threshold_selection | {"selected_threshold": "0.24"}

    with pytest.raises(ValueError, match="Estado congelado"):
        validate_pre_evaluation_sources(replace(inputs, threshold_selection=divergent))


def test_sha_divergence_blocks_before_loader(
    frozen_bundle: tuple[Pipeline, Path, dict[str, str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, path, manifest = frozen_bundle
    divergent = manifest | {"model_artifact_sha256": "0" * 64}
    called = False

    def forbidden_loader(path: Path, expected_sha256: str) -> Pipeline:
        nonlocal called
        called = True
        raise AssertionError((path, expected_sha256))

    monkeypatch.setattr(final_evaluation, "load_final_pipeline", forbidden_loader)
    with pytest.raises(ValueError, match="antes do load"):
        load_validated_frozen_pipeline(divergent, path.parents[1])
    assert not called


def test_correct_fitted_pipeline_is_accepted(
    frozen_bundle: tuple[Pipeline, Path, dict[str, str]],
) -> None:
    _, path, manifest = frozen_bundle

    loaded, loaded_path = load_validated_frozen_pipeline(manifest, path.parents[1])

    assert loaded_path == path
    assert isinstance(loaded, Pipeline)
    assert isinstance(loaded.named_steps["classifier"], XGBClassifier)
    assert loaded.named_steps["classifier"].classes_.tolist() == [0, 1]


def test_lazy_holdout_load_materializes_only_2025(tmp_path: Path) -> None:
    analytical = tmp_path / "analytical.parquet"
    _dataset().write_parquet(analytical)

    holdout = load_final_holdout(analytical, GROUPS.predictors)

    assert holdout.height == 12
    assert set(holdout["source_year"]) == {2025}
    assert set(holdout.columns) == {"id", "source_year", "target_grave", *GROUPS.predictors}


@pytest.mark.parametrize("forbidden_year", [2021, 2022, 2023, 2024])
def test_development_years_are_rejected(forbidden_year: int) -> None:
    holdout = _holdout().with_columns(pl.lit(forbidden_year).alias("source_year"))

    with pytest.raises(ValueError, match="somente 2025"):
        validate_final_holdout(holdout, GROUPS, _partition(_holdout()))


def test_holdout_requires_unique_ids_22_predictors_and_boolean_target() -> None:
    holdout = _holdout()
    validate_final_holdout(holdout, GROUPS, _partition(holdout))
    duplicated = holdout.with_columns(
        pl.when(pl.col("id") == holdout["id"][-1])
        .then(pl.lit(holdout["id"][0]))
        .otherwise(pl.col("id"))
        .alias("id")
    )
    with pytest.raises(ValueError, match="não são únicos"):
        validate_final_holdout(duplicated, GROUPS, _partition(holdout))
    with pytest.raises(ValueError, match="booleano"):
        validate_final_holdout(
            holdout.with_columns(pl.col("target_grave").cast(pl.Int8)),
            GROUPS,
            _partition(holdout),
        )


def test_predict_proba_is_called_once_without_fit_and_positive_class_is_extracted(
    frozen_bundle: tuple[Pipeline, Path, dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, path, manifest = frozen_bundle
    pipeline, _ = load_validated_frozen_pipeline(manifest, path.parents[1])
    original_predict_proba = pipeline.predict_proba
    calls = 0

    def spy(X: Any) -> Any:
        nonlocal calls
        calls += 1
        return original_predict_proba(X)

    monkeypatch.setattr(pipeline, "predict_proba", spy)

    probabilities = generate_final_probabilities(pipeline, _holdout(), GROUPS.predictors)

    assert calls == 1
    raw = pipeline.named_steps["classifier"].predict_proba(
        pipeline.named_steps["preprocessor"].transform(_holdout().select(GROUPS.predictors))
    )
    assert probabilities.tolist() == raw[:, 1].tolist()


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_probabilities_are_rejected(
    invalid: float,
    frozen_bundle: tuple[Pipeline, Path, dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, path, manifest = frozen_bundle
    pipeline, _ = load_validated_frozen_pipeline(manifest, path.parents[1])
    monkeypatch.setattr(
        final_evaluation,
        "extract_xgboost_positive_probability",
        lambda classifier, raw: np.full(_holdout().height, invalid),
    )

    with pytest.raises(ValueError, match="Probabilidades finais"):
        generate_final_probabilities(pipeline, _holdout(), GROUPS.predictors)


def test_probability_metrics_match_official_sklearn_functions() -> None:
    target = np.asarray([False, True, False, True, True])
    probabilities = np.asarray([0.1, 0.8, 0.4, 0.7, 0.3])

    metrics = calculate_probability_metrics(target, probabilities)

    assert metrics.average_precision == average_precision_score(target, probabilities)
    assert metrics.roc_auc == roc_auc_score(target, probabilities)
    assert metrics.brier_score == brier_score_loss(target, probabilities, pos_label=True)


def test_frozen_threshold_uses_greater_equal_and_reference_does_not_replace_it() -> None:
    threshold = float(FROZEN_THRESHOLD_TEXT)
    probabilities = np.asarray([threshold, threshold - 0.01, 0.5, 0.9])
    target = np.asarray([True, True, False, True])

    frozen = evaluate_threshold(probabilities, target, threshold)
    reference = evaluate_threshold(probabilities, target, REFERENCE_THRESHOLD)

    assert frozen.threshold == threshold
    assert (frozen.tn, frozen.fp, frozen.fn, frozen.tp) == (0, 1, 1, 2)
    assert reference.threshold == 0.5
    assert frozen.threshold != reference.threshold


def test_calibration_is_descriptive_deterministic_and_handles_repeated_scores() -> None:
    target = np.asarray([False, True] * 10)
    probabilities = np.asarray([0.1] * 10 + [0.9] * 10)

    first = build_calibration_table(target, probabilities)
    second = build_calibration_table(target, probabilities)

    assert first.equals(second)
    assert first["rows"].sum() == len(target)
    assert first.height <= 10
    assert first.columns == [
        "bin",
        "rows",
        "probability_min",
        "probability_max",
        "mean_predicted_probability",
        "observed_positive_rate",
    ]


def test_predictions_have_exact_columns_only_2025_and_boolean_decision() -> None:
    holdout = _holdout()
    probabilities = np.linspace(0.1, 0.9, holdout.height)

    predictions = build_final_predictions(holdout, probabilities, float(FROZEN_THRESHOLD_TEXT))
    validate_final_predictions(predictions, holdout.height)

    assert predictions.columns == [
        "id",
        "source_year",
        "target_grave",
        "predicted_probability_grave",
        "predicted_grave_frozen_threshold",
    ]
    assert set(predictions["source_year"]) == {2025}
    assert predictions["predicted_grave_frozen_threshold"].dtype == pl.Boolean


def test_predictions_persistence_calculates_sha_in_tmp_path(tmp_path: Path) -> None:
    predictions = build_final_predictions(
        _holdout(), np.linspace(0.1, 0.9, _holdout().height), float(FROZEN_THRESHOLD_TEXT)
    )
    path = tmp_path / "predictions.parquet"

    sha256, size = persist_final_predictions(predictions, path)

    assert path.is_file()
    assert sha256 == sha256_file(path)
    assert size == path.stat().st_size > 0
    validate_final_predictions(pl.read_parquet(path), predictions.height)


def test_development_comparison_calculates_descriptive_deltas() -> None:
    target = np.asarray([False, True, False, True])
    probabilities = np.asarray([0.2, 0.8, 0.4, 0.6])
    metrics = calculate_probability_metrics(target, probabilities)
    frozen = evaluate_threshold(probabilities, target, float(FROZEN_THRESHOLD_TEXT))
    references = InternalReferences(0.4, 0.41, 0.7, 0.2, 0.3, 0.7, 0.42)

    comparison = build_development_comparison(metrics, frozen, references)

    assert comparison.height == 7
    assert np.allclose(
        comparison["delta_final_minus_development"],
        comparison["final_2025_value"] - comparison["development_value"],
    )
    assert "status" not in comparison.columns


def test_low_performance_never_causes_checklist_failure(
    tmp_path: Path, frozen_bundle: tuple[Pipeline, Path, dict[str, str]]
) -> None:
    _, model_path, manifest = frozen_bundle
    holdout = _holdout()
    probabilities = np.zeros(holdout.height)
    frozen = evaluate_threshold(
        probabilities, holdout["target_grave"].to_numpy(), float(FROZEN_THRESHOLD_TEXT)
    )
    predictions_path = tmp_path / "predictions.parquet"
    predictions_path.write_bytes("materialização sintética".encode())

    checklist = build_final_evaluation_checklist(
        holdout,
        probabilities,
        frozen,
        model_path,
        predictions_path,
        "a" * 64,
        expected_model_sha256=manifest["model_artifact_sha256"],
        expected_final_rows=holdout.height,
    )

    assert checklist.height == 25
    assert checklist["status"].unique().to_list() == ["PASS"]
    assert not any("AP >=" in str(value) for value in checklist["check"])


def test_production_module_contains_no_fit_tuning_or_calibrator() -> None:
    source = Path("src/tcc_prf_severity/modeling/final_evaluation.py").read_text(encoding="utf-8")

    for forbidden in (
        ".fit(",
        "fit_transform",
        "partial_fit",
        "build_xgboost_pipeline",
        "fit_final_pipeline",
        "run_final_refit",
        "GridSearchCV",
        "RandomizedSearchCV",
        "CalibratedClassifierCV",
    ):
        assert forbidden not in source


def test_all_tables_are_written_only_to_tmp_path(
    tmp_path: Path, frozen_bundle: tuple[Pipeline, Path, dict[str, str]]
) -> None:
    _, model_path, model_manifest = frozen_bundle
    holdout = _holdout()
    probabilities = np.linspace(0.1, 0.9, holdout.height)
    target = holdout["target_grave"].to_numpy()
    metrics = calculate_probability_metrics(target, probabilities)
    frozen = evaluate_threshold(probabilities, target, float(FROZEN_THRESHOLD_TEXT))
    reference = evaluate_threshold(probabilities, target, REFERENCE_THRESHOLD)
    references = InternalReferences(0.4, 0.41, 0.7, 0.2, 0.3, 0.7, 0.42)
    predictions = build_final_predictions(holdout, probabilities, float(FROZEN_THRESHOLD_TEXT))
    predictions_path = tmp_path / "predictions.parquet"
    predictions_sha, predictions_size = persist_final_predictions(predictions, predictions_path)
    checklist = build_final_evaluation_checklist(
        holdout,
        probabilities,
        frozen,
        model_path,
        predictions_path,
        predictions_sha,
        expected_model_sha256=model_manifest["model_artifact_sha256"],
        expected_final_rows=holdout.height,
    )
    evaluation_manifest = model_manifest | {
        "model_artifact_path": str(model_path),
        "model_artifact_sha256": model_manifest["model_artifact_sha256"],
    }
    result = FinalEvaluationResult(
        model_sha256=model_manifest["model_artifact_sha256"],
        probability_metrics=metrics,
        frozen_threshold_metrics=frozen,
        reference_threshold_metrics=reference,
        references=references,
        predictions=predictions,
        predictions_path=predictions_path,
        predictions_sha256=predictions_sha,
        predictions_size_bytes=predictions_size,
        final_evaluation=build_final_evaluation_table(
            evaluation_manifest,
            holdout,
            metrics,
            frozen,
            reference,
            references,
            predictions_path,
            predictions_sha,
            predictions_size,
        ),
        threshold_evaluation=pl.DataFrame(
            {
                "threshold_role": ["frozen_threshold", "reference_0_5"],
                "threshold": [frozen.threshold, reference.threshold],
            }
        ),
        development_comparison=build_development_comparison(metrics, frozen, references),
        calibration=build_calibration_table(target, probabilities),
        checklist=checklist,
    )
    tables_dir = tmp_path / "tables"

    paths = write_final_evaluation_tables(result, tables_dir)

    assert len(paths) == 5
    assert {path.name for path in paths} == {
        "phase_4h_final_evaluation.csv",
        "phase_4h_threshold_evaluation.csv",
        "phase_4h_development_comparison.csv",
        "phase_4h_calibration.csv",
        "phase_4h_final_evaluation_checklist.csv",
    }
    assert len(list(tables_dir.iterdir())) == 5
