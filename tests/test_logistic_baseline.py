from __future__ import annotations

import warnings
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning, NotFittedError
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted

import tcc_prf_severity.modeling.logistic_baseline as logistic_baseline
from tcc_prf_severity.modeling.experimental_design import (
    TemporalFold,
    build_temporal_folds,
    load_predictors_from_schema,
)
from tcc_prf_severity.modeling.logistic_baseline import (
    REFERENCE_THRESHOLD,
    analyze_logistic_baseline,
    build_logistic_model_contract,
    build_logistic_pipeline,
    build_logistic_summary,
    calculate_binary_metrics,
    extract_positive_class_probability,
    run_logistic_fold,
    validate_oof_predictions,
    write_logistic_baseline_artifacts,
)
from tcc_prf_severity.modeling.preprocessing import (
    PreprocessingGroups,
    load_preprocessing_groups,
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


@pytest.fixture(scope="module")
def baseline_result() -> logistic_baseline.LogisticBaselineResult:
    return analyze_logistic_baseline(_dataset(), GROUPS, build_temporal_folds())


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
    original = logistic_baseline.build_preprocessor

    def spy(groups: PreprocessingGroups) -> ColumnTransformer:
        called.append(groups)
        return original(groups)

    monkeypatch.setattr(logistic_baseline, "build_preprocessor", spy)
    pipeline = build_logistic_pipeline(GROUPS)
    classifier = pipeline.named_steps["classifier"]

    assert called == [GROUPS]
    assert isinstance(pipeline.named_steps["preprocessor"], ColumnTransformer)
    assert isinstance(classifier, LogisticRegression)
    assert classifier.solver == "newton-cholesky"
    assert classifier.C == 1.0
    assert classifier.l1_ratio == 0.0
    assert classifier.class_weight is None
    assert classifier.fit_intercept is True
    assert classifier.tol == 1e-4
    assert classifier.max_iter == 500
    with pytest.raises(NotFittedError):
        check_is_fitted(pipeline)


def test_each_pipeline_instance_is_independent() -> None:
    first = build_logistic_pipeline(GROUPS)
    second = build_logistic_pipeline(GROUPS)

    assert first is not second
    assert first.named_steps["preprocessor"] is not second.named_steps["preprocessor"]
    assert first.named_steps["classifier"] is not second.named_steps["classifier"]


def test_fold_fit_scope_is_train_only_and_source_is_not_modified() -> None:
    source = _dataset()
    before = source.clone()

    result = run_logistic_fold(source, GROUPS, build_temporal_folds()[1])

    assert result.train_years == (2021, 2022)
    assert result.validation_year == 2023
    assert result.train_rows == 80
    assert result.validation_rows == 40
    assert source.equals(before)


def test_2025_is_rejected_before_modeling() -> None:
    with pytest.raises(ValueError, match="2025 é proibido"):
        run_logistic_fold(_dataset(), GROUPS, TemporalFold(4, (2021, 2022, 2023, 2024), 2025))


def test_positive_probability_is_located_from_classes_not_assumed_index() -> None:
    classifier = LogisticRegression()
    classifier.classes_ = np.array([True, False])
    raw = np.array([[0.8, 0.2], [0.3, 0.7]])

    probabilities = extract_positive_class_probability(classifier, raw)

    assert probabilities.tolist() == [0.8, 0.3]


@pytest.mark.parametrize(
    "raw",
    (np.array([[np.nan, 0.0]]), np.array([[1.1, -0.1]])),
)
def test_invalid_positive_probabilities_fail(raw: np.ndarray) -> None:
    classifier = LogisticRegression()
    classifier.classes_ = np.array([True, False])

    with pytest.raises(ValueError, match=r"finitas|\[0, 1\]"):
        extract_positive_class_probability(classifier, raw)


def test_metrics_use_probabilities_and_fixed_0_5_with_true_positive() -> None:
    target = np.array([False, True, False, True])
    probabilities = np.array([0.6, 0.7, 0.4, 0.2])

    metrics = calculate_binary_metrics(target, probabilities)

    assert REFERENCE_THRESHOLD == 0.5
    assert metrics["average_precision"] == pytest.approx(
        average_precision_score(target, probabilities)
    )
    assert metrics["average_precision"] != average_precision_score(
        target, probabilities >= REFERENCE_THRESHOLD
    )
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


def test_convergence_warning_is_a_hard_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    original_fit = Pipeline.fit

    def fit_with_warning(self: Pipeline, *args: Any, **kwargs: Any) -> Pipeline:
        fitted = original_fit(self, *args, **kwargs)
        warnings.warn("synthetic non-convergence", ConvergenceWarning, stacklevel=2)
        return fitted

    monkeypatch.setattr(Pipeline, "fit", fit_with_warning)
    with pytest.raises(RuntimeError, match="ConvergenceWarning"):
        run_logistic_fold(_dataset(), GROUPS, build_temporal_folds()[0])


def test_three_fold_metrics_and_population_std_are_recorded(
    baseline_result: logistic_baseline.LogisticBaselineResult,
) -> None:
    metrics = baseline_result.fold_metrics
    summary = {
        str(row["key"]): str(row["value"])
        for row in build_logistic_summary(metrics).iter_rows(named=True)
    }
    aps = metrics.get_column("average_precision").to_numpy()

    assert metrics.get_column("fold").to_list() == [1, 2, 3]
    assert float(summary["ap_unweighted_mean"]) == pytest.approx(float(np.mean(aps)))
    assert float(summary["ap_population_std"]) == pytest.approx(float(np.std(aps, ddof=0)))
    assert float(summary["ap_fold3"]) == pytest.approx(float(aps[2]))
    assert summary["primary_metric"] == "Average Precision (AP)"
    assert summary["final_test_used"] == "false"
    assert summary["threshold_selected"] == "false"


def test_secondary_metrics_prevalence_dimensions_and_convergence_are_valid(
    baseline_result: logistic_baseline.LogisticBaselineResult,
) -> None:
    metrics = baseline_result.fold_metrics

    output_feature_min = metrics.get_column("output_feature_count").min()
    iteration_min = metrics.get_column("iterations").min()
    iteration_max = metrics.get_column("iterations").max()
    assert isinstance(output_feature_min, int)
    assert isinstance(iteration_min, int)
    assert isinstance(iteration_max, int)
    assert output_feature_min > 22
    assert metrics.get_column("validation_positive_rate").is_between(0.0, 1.0).all()
    assert metrics.get_column("average_precision").is_between(0.0, 1.0).all()
    assert metrics.get_column("roc_auc").is_between(0.0, 1.0).all()
    assert metrics.get_column("brier_score").is_between(0.0, 1.0).all()
    assert iteration_min > 0
    assert iteration_max <= 500
    assert metrics.get_column("converged").all()


def test_oof_contains_only_validation_years_unique_ids_and_preserved_target(
    baseline_result: logistic_baseline.LogisticBaselineResult,
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
    validate_oof_predictions(oof, source, build_temporal_folds())


def test_oof_validation_rejects_2025_duplicates_wrong_target_and_probability(
    baseline_result: logistic_baseline.LogisticBaselineResult,
) -> None:
    source = _dataset()
    oof = baseline_result.oof_predictions
    invalid_variants = (
        oof.with_columns(
            pl.when(pl.arange(0, pl.len()) == 0)
            .then(pl.lit(2025))
            .otherwise(pl.col("source_year"))
            .alias("source_year")
        ),
        pl.concat([oof, oof.head(1)], how="vertical"),
        oof.with_columns(
            pl.when(pl.arange(0, pl.len()) == 0)
            .then(~pl.col("target_grave"))
            .otherwise(pl.col("target_grave"))
            .alias("target_grave")
        ),
        oof.with_columns(
            pl.when(pl.arange(0, pl.len()) == 0)
            .then(pl.lit(1.5))
            .otherwise(pl.col("predicted_probability_grave"))
            .alias("predicted_probability_grave")
        ),
    )
    for invalid in invalid_variants:
        with pytest.raises(ValueError, match="OOF inválidas"):
            validate_oof_predictions(invalid, source, build_temporal_folds())


def test_calibration_is_diagnostic_only_and_excludes_2025(
    baseline_result: logistic_baseline.LogisticBaselineResult,
) -> None:
    calibration = baseline_result.calibration

    assert set(calibration.get_column("validation_year")) == {2022, 2023, 2024}
    maximum_bins = calibration.group_by("fold").len().get_column("len").max()
    assert isinstance(maximum_bins, int)
    assert maximum_bins <= 10
    assert calibration.get_column("mean_predicted_probability").is_between(0.0, 1.0).all()
    assert calibration.get_column("observed_positive_rate").is_between(0.0, 1.0).all()


def test_model_contract_freezes_baseline_without_selection() -> None:
    contract = {
        str(row["key"]): str(row["value"])
        for row in build_logistic_model_contract().iter_rows(named=True)
    }

    assert contract["model_family"] == "logistic_regression"
    assert contract["role"] == "baseline"
    assert contract["solver"] == "newton-cholesky"
    assert contract["regularization"] == "L2"
    assert contract["threshold_policy"] == "not_selected_0.5_reference_only"
    assert contract["final_test_year"] == "2025_reserved"


def test_artifact_writing_uses_tmp_path_and_persists_no_model(
    tmp_path: Path,
    baseline_result: logistic_baseline.LogisticBaselineResult,
) -> None:
    tables_dir = tmp_path / "tables"
    oof_path = tmp_path / "processed" / "oof.parquet"

    table_paths, written_oof = write_logistic_baseline_artifacts(
        baseline_result,
        tables_dir,
        oof_path,
    )

    assert {path.name for path in table_paths} == {
        "phase_4a_logistic_fold_metrics.csv",
        "phase_4a_logistic_summary.csv",
        "phase_4a_logistic_model_contract.csv",
        "phase_4a_logistic_calibration.csv",
    }
    assert all(path.is_file() for path in table_paths)
    assert written_oof == oof_path
    assert pl.read_parquet(oof_path).equals(baseline_result.oof_predictions)
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.pickle"))
    assert not list(tmp_path.rglob("*.joblib"))
