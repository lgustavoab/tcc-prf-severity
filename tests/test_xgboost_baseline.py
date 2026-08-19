from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import pytest
import xgboost
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import NotFittedError
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted
from xgboost import XGBClassifier

import tcc_prf_severity.modeling.xgboost_baseline as xgboost_baseline
from tcc_prf_severity.modeling.experimental_design import (
    TemporalFold,
    build_temporal_folds,
    load_predictors_from_schema,
)
from tcc_prf_severity.modeling.logistic_baseline import calculate_binary_metrics
from tcc_prf_severity.modeling.preprocessing import (
    PreprocessingGroups,
    build_preprocessor,
    load_preprocessing_groups,
)
from tcc_prf_severity.modeling.xgboost_baseline import (
    EXPECTED_XGBOOST_VERSION,
    analyze_xgboost_baseline,
    build_xgboost_model_contract,
    build_xgboost_pipeline,
    build_xgboost_summary,
    extract_xgboost_positive_probability,
    run_xgboost_fold,
    validate_xgboost_version,
    write_xgboost_artifacts,
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
BINARY = tuple(f"tracado_{suffix}" for suffix in "abcdefghijkl")
PREDICTORS = (*CATEGORICAL, "km", *BINARY)
GROUPS = PreprocessingGroups(CATEGORICAL, ("km",), BINARY)


def _write_schema(path: Path) -> None:
    columns = ["id", "source_year", "data_inversa", "target_grave", *PREDICTORS]
    pl.DataFrame(
        {
            "column": columns,
            "role": ["metadata"] * 3 + ["target"] + ["predictor"] * 22,
            "conceptual_feature": [
                "not_applicable",
                "not_applicable",
                "not_applicable",
                "target_grave",
                *CATEGORICAL,
                "km",
                *(["tracado_via_components"] * 12),
            ],
            "included_in_model_matrix": [False] * 4 + [True] * 22,
        }
    ).write_csv(path)


def _dataset() -> pl.DataFrame:
    rng = np.random.default_rng(20260819)
    rows_per_year = 40
    years = np.repeat(np.arange(2021, 2026), rows_per_year)
    total = len(years)
    hour = rng.integers(0, 24, total)
    first_binary = rng.integers(0, 2, total)
    logits = -1.1 + 0.035 * (hour - 12) + 0.35 * first_binary
    probabilities = 1.0 / (1.0 + np.exp(-logits))
    target = rng.random(total) < probabilities
    data: dict[str, object] = {
        "id": [f"{year}-{index:03d}" for year in range(2021, 2026) for index in range(40)],
        "source_year": years,
        "data_inversa": [date(int(year), 1, index % 28 + 1) for index, year in enumerate(years)],
        "target_grave": target,
        "month_name": rng.choice(["Janeiro", "Fevereiro", "Março"], total),
        "dia_semana": rng.choice(["segunda-feira", "terça-feira", "quarta-feira"], total),
        "hour": hour,
        "uf": rng.choice(["SP", "MG", "PR"], total),
        "br": rng.choice([0, 101, 116, 381], total),
        "sentido_via": rng.choice(["Crescente", "Decrescente", "Não Informado"], total),
        "condicao_metereologica": rng.choice(["Chuva", "Céu Claro", "Ignorado"], total),
        "tipo_pista": rng.choice(["Simples", "Dupla"], total),
        "uso_solo": rng.choice(["Sim", "Não"], total),
        "km": rng.uniform(0.0, 900.0, total),
    }
    for index, column in enumerate(BINARY):
        data[column] = first_binary if index == 0 else rng.integers(0, 2, total)
    return pl.DataFrame(data)


def _fast_pipeline(groups: PreprocessingGroups) -> Pipeline:
    return Pipeline(
        (
            ("preprocessor", build_preprocessor(groups)),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=8,
                    learning_rate=0.1,
                    max_depth=3,
                    min_child_weight=1.0,
                    gamma=0.0,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=0.0,
                    reg_lambda=1.0,
                    objective="binary:logistic",
                    eval_metric="logloss",
                    tree_method="hist",
                    device="cpu",
                    n_jobs=1,
                    random_state=42,
                    scale_pos_weight=1.0,
                    booster="gbtree",
                    enable_categorical=False,
                    verbosity=0,
                ),
            ),
        )
    )


@pytest.fixture(scope="module")
def baseline_result() -> xgboost_baseline.XGBoostBaselineResult:
    return analyze_xgboost_baseline(
        _dataset(),
        GROUPS,
        build_temporal_folds(),
        pipeline_factory=_fast_pipeline,
    )


def test_xgboost_version_is_exactly_contracted() -> None:
    assert xgboost.__version__ == EXPECTED_XGBOOST_VERSION == "3.3.0"
    assert validate_xgboost_version() == "3.3.0"
    with pytest.raises(RuntimeError, match=r"esperado 3\.3\.0"):
        validate_xgboost_version("3.4.1")


def test_predictors_come_from_schema_and_exclude_metadata_and_target(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.csv"
    _write_schema(schema_path)

    predictors = load_predictors_from_schema(schema_path)
    groups = load_preprocessing_groups(schema_path)

    assert len(predictors) == 22
    assert set(predictors) == set(groups.predictors)
    assert not {"id", "source_year", "data_inversa", "target_grave"} & set(predictors)


def test_pipeline_reuses_phase_3e_factory_and_has_fixed_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[PreprocessingGroups] = []
    original = xgboost_baseline.build_preprocessor

    def spy(groups: PreprocessingGroups) -> ColumnTransformer:
        called.append(groups)
        return original(groups)

    monkeypatch.setattr(xgboost_baseline, "build_preprocessor", spy)
    pipeline = build_xgboost_pipeline(GROUPS)
    classifier = pipeline.named_steps["classifier"]
    params = classifier.get_params()

    assert called == [GROUPS]
    assert isinstance(pipeline.named_steps["preprocessor"], ColumnTransformer)
    assert isinstance(classifier, XGBClassifier)
    assert params["n_estimators"] == 300
    assert params["learning_rate"] == 0.05
    assert params["max_depth"] == 6
    assert params["min_child_weight"] == 1.0
    assert params["gamma"] == 0.0
    assert params["subsample"] == 0.8
    assert params["colsample_bytree"] == 0.8
    assert params["reg_alpha"] == 0.0
    assert params["reg_lambda"] == 1.0
    assert params["objective"] == "binary:logistic"
    assert params["eval_metric"] == "logloss"
    assert params["tree_method"] == "hist"
    assert params["device"] == "cpu"
    assert params["n_jobs"] == -1
    assert params["random_state"] == 42
    assert params["scale_pos_weight"] == 1.0
    assert params["booster"] == "gbtree"
    assert params["enable_categorical"] is False
    assert params["verbosity"] == 0
    assert params["early_stopping_rounds"] is None
    assert params["callbacks"] is None
    with pytest.raises(NotFittedError):
        check_is_fitted(pipeline)


def test_each_pipeline_instance_is_independent() -> None:
    first = build_xgboost_pipeline(GROUPS)
    second = build_xgboost_pipeline(GROUPS)

    assert first is not second
    assert first.named_steps["preprocessor"] is not second.named_steps["preprocessor"]
    assert first.named_steps["classifier"] is not second.named_steps["classifier"]


def test_fold_fit_scope_source_unchanged_sparse_and_rounds_completed() -> None:
    source = _dataset()
    before = source.clone()
    fold = build_temporal_folds()[1]

    result = run_xgboost_fold(source, GROUPS, fold, _fast_pipeline)
    train = source.filter(pl.col("source_year").is_in(fold.train_years)).select(GROUPS.predictors)
    pipeline = _fast_pipeline(GROUPS)
    train_target = source.filter(pl.col("source_year").is_in(fold.train_years))["target_grave"]
    pipeline.fit(train, train_target)
    transformed = pipeline.named_steps["preprocessor"].transform(train)

    assert result.train_years == (2021, 2022)
    assert result.validation_year == 2023
    assert result.train_rows == 80
    assert result.validation_rows == 40
    assert result.configured_boosting_rounds == 8
    assert result.completed_boosting_rounds == 8
    assert result.max_depth_configured == 3
    assert result.all_rounds_completed is True
    assert sparse.issparse(transformed)
    assert source.equals(before)


def test_2025_is_rejected_before_modeling() -> None:
    with pytest.raises(ValueError, match="2025 é proibido"):
        run_xgboost_fold(
            _dataset(),
            GROUPS,
            TemporalFold(4, (2021, 2022, 2023, 2024), 2025),
            _fast_pipeline,
        )


def test_bool_target_becomes_numeric_zero_one_and_probability_one_is_grave() -> None:
    source = _dataset().filter(pl.col("source_year") == 2021)
    pipeline = _fast_pipeline(GROUPS)
    pipeline.fit(source.select(GROUPS.predictors), source["target_grave"])
    classifier = pipeline.named_steps["classifier"]
    raw = np.asarray(pipeline.predict_proba(source.select(GROUPS.predictors)))

    assert isinstance(classifier, XGBClassifier)
    assert classifier.classes_.tolist() == [0, 1]
    assert extract_xgboost_positive_probability(classifier, raw).tolist() == raw[:, 1].tolist()


def test_invalid_classes_or_probabilities_fail() -> None:
    classifier = XGBClassifier()
    classifier.n_classes_ = 3
    with pytest.raises(ValueError, match="classes numéricas 0 e 1"):
        extract_xgboost_positive_probability(classifier, np.ones((2, 3)))

    classifier.n_classes_ = 2
    with pytest.raises(ValueError, match="uma coluna por classe"):
        extract_xgboost_positive_probability(classifier, np.ones(2))
    with pytest.raises(ValueError, match="finitas"):
        extract_xgboost_positive_probability(classifier, np.array([[0.0, np.nan]]))
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        extract_xgboost_positive_probability(classifier, np.array([[0.0, 1.1]]))


def test_metrics_use_probabilities_and_fixed_0_5_with_true_positive() -> None:
    target = np.array([False, True, False, True])
    probabilities = np.array([0.6, 0.7, 0.4, 0.2])

    metrics = calculate_binary_metrics(target, probabilities)

    assert metrics["average_precision"] == pytest.approx(
        average_precision_score(target, probabilities)
    )
    assert metrics["average_precision"] != average_precision_score(target, probabilities >= 0.5)
    assert metrics["roc_auc"] == pytest.approx(roc_auc_score(target, probabilities))
    assert metrics["brier_score"] == pytest.approx(
        brier_score_loss(target, probabilities, pos_label=True)
    )
    assert (
        metrics["tn_at_0_5"],
        metrics["fp_at_0_5"],
        metrics["fn_at_0_5"],
        metrics["tp_at_0_5"],
    ) == (1, 1, 1, 1)
    assert metrics["recall_at_0_5"] == 0.5
    assert metrics["precision_at_0_5"] == 0.5
    assert metrics["f1_at_0_5"] == 0.5


def test_three_fold_aggregation_rounds_and_frozen_flags(
    baseline_result: xgboost_baseline.XGBoostBaselineResult,
) -> None:
    metrics = baseline_result.fold_metrics
    summary = {
        str(row["key"]): str(row["value"])
        for row in build_xgboost_summary(metrics).iter_rows(named=True)
    }
    aps = metrics.get_column("average_precision").to_numpy()

    assert metrics.get_column("fold").to_list() == [1, 2, 3]
    assert float(summary["ap_unweighted_mean"]) == pytest.approx(float(np.mean(aps)))
    assert float(summary["ap_population_std"]) == pytest.approx(float(np.std(aps, ddof=0)))
    assert float(summary["ap_fold3"]) == pytest.approx(float(aps[2]))
    assert summary["primary_metric"] == "Average Precision (AP)"
    assert summary["all_folds_completed"] == "true"
    assert summary["all_boosting_rounds_completed"] == "true"
    assert summary["final_test_used"] == "false"
    assert summary["threshold_selected"] == "false"
    assert summary["hyperparameter_tuning_used"] == "false"
    assert summary["early_stopping_used"] == "false"
    assert metrics.get_column("completed_boosting_rounds").to_list() == [8, 8, 8]


def test_secondary_metrics_and_dimensions_are_valid(
    baseline_result: xgboost_baseline.XGBoostBaselineResult,
) -> None:
    metrics = baseline_result.fold_metrics
    output_feature_min = metrics.get_column("output_feature_count").min()
    assert isinstance(output_feature_min, int)
    assert output_feature_min > 22
    assert metrics.get_column("validation_positive_rate").is_between(0.0, 1.0).all()
    assert metrics.get_column("average_precision").is_between(0.0, 1.0).all()
    assert metrics.get_column("roc_auc").is_between(0.0, 1.0).all()
    assert metrics.get_column("brier_score").is_between(0.0, 1.0).all()
    assert "feature_importance" not in " ".join(metrics.columns)


def test_oof_contains_only_internal_validations_and_preserves_target(
    baseline_result: xgboost_baseline.XGBoostBaselineResult,
) -> None:
    source = _dataset()
    oof = baseline_result.oof_predictions

    assert oof.height == 120
    assert set(oof.get_column("source_year")) == {2022, 2023, 2024}
    assert 2021 not in set(oof.get_column("source_year"))
    assert 2025 not in set(oof.get_column("source_year"))
    assert oof.get_column("id").n_unique() == oof.height
    assert oof.get_column("predicted_probability_grave").is_finite().all()
    assert oof.get_column("predicted_probability_grave").is_between(0.0, 1.0).all()
    expected = source.select("id", "target_grave").rename({"target_grave": "expected"})
    checked = oof.join(expected, on="id", validate="1:1")
    assert checked.filter(pl.col("target_grave") != pl.col("expected")).is_empty()


def test_calibration_is_internal_and_diagnostic_only(
    baseline_result: xgboost_baseline.XGBoostBaselineResult,
) -> None:
    calibration = baseline_result.calibration

    assert set(calibration.get_column("validation_year")) == {2022, 2023, 2024}
    maximum_bins = calibration.group_by("fold").len().get_column("len").max()
    assert isinstance(maximum_bins, int)
    assert maximum_bins <= 10
    assert calibration.get_column("mean_predicted_probability").is_between(0.0, 1.0).all()
    assert calibration.get_column("observed_positive_rate").is_between(0.0, 1.0).all()


def test_model_contract_freezes_version_rounds_and_no_optimization() -> None:
    contract = {
        str(row["key"]): str(row["value"])
        for row in build_xgboost_model_contract().iter_rows(named=True)
    }

    assert contract["library"] == "xgboost"
    assert contract["library_version"] == "3.3.0"
    assert contract["model_family"] == "xgboost_gradient_boosted_trees"
    assert contract["role"] == "baseline_candidate"
    assert contract["n_estimators"] == "300"
    assert contract["max_depth"] == "6"
    assert contract["threshold_policy"] == "not_selected_0.5_reference_only"
    assert contract["early_stopping"] == "false"
    assert contract["hyperparameter_tuning"] == "false"
    assert contract["final_test_year"] == "2025_reserved"


def test_artifact_writing_uses_tmp_path_and_persists_no_model(
    tmp_path: Path,
    baseline_result: xgboost_baseline.XGBoostBaselineResult,
) -> None:
    tables_dir = tmp_path / "tables"
    oof_path = tmp_path / "processed" / "oof.parquet"

    table_paths, written_oof = write_xgboost_artifacts(baseline_result, tables_dir, oof_path)

    assert {path.name for path in table_paths} == {
        "phase_4c_xgboost_fold_metrics.csv",
        "phase_4c_xgboost_summary.csv",
        "phase_4c_xgboost_model_contract.csv",
        "phase_4c_xgboost_calibration.csv",
    }
    assert all(path.is_file() for path in table_paths)
    assert written_oof == oof_path
    assert pl.read_parquet(oof_path).equals(baseline_result.oof_predictions)
    for suffix in ("*.json", "*.ubj", "*.pkl", "*.pickle", "*.joblib"):
        assert not list(tmp_path.rglob(suffix))
