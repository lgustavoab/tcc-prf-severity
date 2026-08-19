from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import pytest
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import NotFittedError
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted

import tcc_prf_severity.modeling.random_forest_baseline as random_forest_baseline
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
from tcc_prf_severity.modeling.random_forest_baseline import (
    analyze_random_forest_baseline,
    build_random_forest_model_contract,
    build_random_forest_pipeline,
    build_random_forest_summary,
    extract_positive_class_probability,
    run_random_forest_fold,
    write_random_forest_artifacts,
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
                RandomForestClassifier(
                    n_estimators=12,
                    criterion="gini",
                    max_depth=6,
                    min_samples_leaf=2,
                    max_features="sqrt",
                    bootstrap=True,
                    oob_score=False,
                    n_jobs=1,
                    random_state=42,
                    class_weight=None,
                ),
            ),
        )
    )


@pytest.fixture(scope="module")
def baseline_result() -> random_forest_baseline.RandomForestBaselineResult:
    return analyze_random_forest_baseline(
        _dataset(),
        GROUPS,
        build_temporal_folds(),
        pipeline_factory=_fast_pipeline,
    )


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
    original = random_forest_baseline.build_preprocessor

    def spy(groups: PreprocessingGroups) -> ColumnTransformer:
        called.append(groups)
        return original(groups)

    monkeypatch.setattr(random_forest_baseline, "build_preprocessor", spy)
    pipeline = build_random_forest_pipeline(GROUPS)
    classifier = pipeline.named_steps["classifier"]

    assert called == [GROUPS]
    assert isinstance(pipeline.named_steps["preprocessor"], ColumnTransformer)
    assert isinstance(classifier, RandomForestClassifier)
    assert classifier.n_estimators == 300
    assert classifier.criterion == "gini"
    assert classifier.max_depth == 20
    assert classifier.min_samples_split == 2
    assert classifier.min_samples_leaf == 5
    assert classifier.max_features == "sqrt"
    assert classifier.bootstrap is True
    assert classifier.oob_score is False
    assert classifier.n_jobs == -1
    assert classifier.random_state == 42
    assert classifier.class_weight is None
    assert classifier.max_samples is None
    with pytest.raises(NotFittedError):
        check_is_fitted(pipeline)


def test_each_pipeline_instance_is_independent() -> None:
    first = build_random_forest_pipeline(GROUPS)
    second = build_random_forest_pipeline(GROUPS)

    assert first is not second
    assert first.named_steps["preprocessor"] is not second.named_steps["preprocessor"]
    assert first.named_steps["classifier"] is not second.named_steps["classifier"]


def test_fold_fit_scope_is_train_only_source_unchanged_and_sparse_preserved() -> None:
    source = _dataset()
    before = source.clone()
    fold = build_temporal_folds()[1]

    result = run_random_forest_fold(source, GROUPS, fold, _fast_pipeline)
    train = source.filter(pl.col("source_year").is_in(fold.train_years)).select(GROUPS.predictors)
    pipeline = _fast_pipeline(GROUPS)
    pipeline.fit(
        train, source.filter(pl.col("source_year").is_in(fold.train_years))["target_grave"]
    )
    transformed = pipeline.named_steps["preprocessor"].transform(train)

    assert result.train_years == (2021, 2022)
    assert result.validation_year == 2023
    assert result.train_rows == 80
    assert result.validation_rows == 40
    assert sparse.issparse(transformed)
    assert source.equals(before)


def test_2025_is_rejected_before_modeling() -> None:
    with pytest.raises(ValueError, match="2025 é proibido"):
        run_random_forest_fold(
            _dataset(),
            GROUPS,
            TemporalFold(4, (2021, 2022, 2023, 2024), 2025),
            _fast_pipeline,
        )


def test_positive_probability_is_located_from_classes_not_assumed_index() -> None:
    classifier = RandomForestClassifier()
    classifier.classes_ = [True, False]
    raw = np.array([[0.8, 0.2], [0.3, 0.7]])

    probabilities = extract_positive_class_probability(classifier, raw)

    assert probabilities.tolist() == [0.8, 0.3]


@pytest.mark.parametrize(
    "raw",
    (np.array([[np.nan, 0.0]]), np.array([[1.1, -0.1]])),
)
def test_invalid_positive_probabilities_fail(raw: np.ndarray) -> None:
    classifier = RandomForestClassifier()
    classifier.classes_ = [True, False]

    with pytest.raises(ValueError, match=r"finitas|\[0, 1\]"):
        extract_positive_class_probability(classifier, raw)


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


def test_three_fold_metrics_and_population_std_are_recorded(
    baseline_result: random_forest_baseline.RandomForestBaselineResult,
) -> None:
    metrics = baseline_result.fold_metrics
    summary = {
        str(row["key"]): str(row["value"])
        for row in build_random_forest_summary(metrics).iter_rows(named=True)
    }
    aps = metrics.get_column("average_precision").to_numpy()

    assert metrics.get_column("fold").to_list() == [1, 2, 3]
    assert float(summary["ap_unweighted_mean"]) == pytest.approx(float(np.mean(aps)))
    assert float(summary["ap_population_std"]) == pytest.approx(float(np.std(aps, ddof=0)))
    assert float(summary["ap_fold3"]) == pytest.approx(float(aps[2]))
    assert summary["primary_metric"] == "Average Precision (AP)"
    assert summary["all_folds_completed"] == "true"
    assert summary["final_test_used"] == "false"
    assert summary["threshold_selected"] == "false"
    assert summary["hyperparameter_tuning_used"] == "false"


def test_secondary_metrics_dimensions_and_tree_structure_are_valid(
    baseline_result: random_forest_baseline.RandomForestBaselineResult,
) -> None:
    metrics = baseline_result.fold_metrics
    output_feature_min = metrics.get_column("output_feature_count").min()
    max_depth = metrics.get_column("max_tree_depth_observed").max()
    min_nodes = metrics.get_column("mean_tree_node_count").min()
    assert isinstance(output_feature_min, int)
    assert isinstance(max_depth, int)
    assert isinstance(min_nodes, float)
    assert output_feature_min > 22
    assert metrics.get_column("validation_positive_rate").is_between(0.0, 1.0).all()
    assert metrics.get_column("average_precision").is_between(0.0, 1.0).all()
    assert metrics.get_column("roc_auc").is_between(0.0, 1.0).all()
    assert metrics.get_column("brier_score").is_between(0.0, 1.0).all()
    assert metrics.get_column("n_estimators").to_list() == [12, 12, 12]
    assert max_depth <= 6
    assert min_nodes > 0.0
    assert "feature_importance" not in " ".join(metrics.columns)


def test_oof_contains_only_validation_years_unique_ids_and_preserved_target(
    baseline_result: random_forest_baseline.RandomForestBaselineResult,
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


def test_calibration_is_diagnostic_only_and_excludes_2025(
    baseline_result: random_forest_baseline.RandomForestBaselineResult,
) -> None:
    calibration = baseline_result.calibration

    assert set(calibration.get_column("validation_year")) == {2022, 2023, 2024}
    maximum_bins = calibration.group_by("fold").len().get_column("len").max()
    assert isinstance(maximum_bins, int)
    assert maximum_bins <= 10
    assert calibration.get_column("mean_predicted_probability").is_between(0.0, 1.0).all()
    assert calibration.get_column("observed_positive_rate").is_between(0.0, 1.0).all()


def test_model_contract_freezes_baseline_without_tuning_or_selection() -> None:
    contract = {
        str(row["key"]): str(row["value"])
        for row in build_random_forest_model_contract().iter_rows(named=True)
    }

    assert contract["model_family"] == "random_forest"
    assert contract["role"] == "baseline_candidate"
    assert contract["n_estimators"] == "300"
    assert contract["max_depth"] == "20"
    assert contract["min_samples_leaf"] == "5"
    assert contract["threshold_policy"] == "not_selected_0.5_reference_only"
    assert contract["final_test_year"] == "2025_reserved"
    assert contract["hyperparameter_tuning"] == "false"


def test_artifact_writing_uses_tmp_path_and_persists_no_model(
    tmp_path: Path,
    baseline_result: random_forest_baseline.RandomForestBaselineResult,
) -> None:
    tables_dir = tmp_path / "tables"
    oof_path = tmp_path / "processed" / "oof.parquet"

    table_paths, written_oof = write_random_forest_artifacts(
        baseline_result,
        tables_dir,
        oof_path,
    )

    assert {path.name for path in table_paths} == {
        "phase_4b_random_forest_fold_metrics.csv",
        "phase_4b_random_forest_summary.csv",
        "phase_4b_random_forest_model_contract.csv",
        "phase_4b_random_forest_calibration.csv",
    }
    assert all(path.is_file() for path in table_paths)
    assert written_oof == oof_path
    assert pl.read_parquet(oof_path).equals(baseline_result.oof_predictions)
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.pickle"))
    assert not list(tmp_path.rglob("*.joblib"))
