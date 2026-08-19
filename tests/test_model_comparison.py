from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from tcc_prf_severity.modeling.model_comparison import (
    LOGISTIC_MODEL_ID,
    RANDOM_FOREST_MODEL_ID,
    XGBOOST_MODEL_ID,
    PublishedModel,
    compare_published_models,
    validate_model_comparability,
    write_model_comparison_tables,
)

STRUCTURE = {
    "fold": [1, 2, 3],
    "train_years": ["2021", "2021,2022", "2021,2022,2023"],
    "validation_year": [2022, 2023, 2024],
    "train_rows": [100, 200, 300],
    "validation_rows": [80, 90, 100],
    "output_feature_count": [40, 42, 43],
    "validation_positive_rate": [0.28, 0.29, 0.27],
}


def _experimental_contract() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "key": [
                "number_of_internal_folds",
                "primary_metric",
                "fold_aggregation",
                "final_holdout_policy",
            ],
            "value": [
                "3",
                "Average Precision (AP)",
                "unweighted_mean_AP_plus_std_and_latest_fold",
                "no_optimization_or_fit_on_2025",
            ],
        }
    )


def _model(
    model_id: str,
    family: str,
    ap: tuple[float, float, float],
    roc: tuple[float, float, float],
    brier: tuple[float, float, float],
) -> PublishedModel:
    folds = pl.DataFrame(
        {
            **STRUCTURE,
            "average_precision": ap,
            "roc_auc": roc,
            "brier_score": brier,
        }
    )
    return PublishedModel(
        model_id=model_id,
        model_family=family,
        fold_metrics=folds,
        summary={
            "model_id": model_id,
            "fold_count": "3",
            "primary_metric": "Average Precision (AP)",
            "ap_unweighted_mean": str(float(np.mean(ap))),
            "ap_population_std": str(float(np.std(ap, ddof=0))),
            "ap_fold3": str(ap[2]),
            "mean_roc_auc": str(float(np.mean(roc))),
            "mean_brier_score": str(float(np.mean(brier))),
            "final_test_used": "false",
            "threshold_selected": "false",
        },
        contract={
            "model_family": family,
            "primary_metric": "Average Precision",
            "model_selection_aggregation": "unweighted_fold_mean",
            "final_test_year": "2025_reserved",
        },
    )


@pytest.fixture
def models() -> tuple[PublishedModel, ...]:
    return (
        _model(
            LOGISTIC_MODEL_ID,
            "logistic_regression",
            (0.30, 0.32, 0.33),
            (0.60, 0.62, 0.63),
            (0.21, 0.20, 0.19),
        ),
        _model(
            RANDOM_FOREST_MODEL_ID,
            "random_forest",
            (0.31, 0.35, 0.36),
            (0.61, 0.64, 0.65),
            (0.20, 0.19, 0.18),
        ),
        _model(
            XGBOOST_MODEL_ID,
            "xgboost_gradient_boosted_trees",
            (0.32, 0.37, 0.40),
            (0.62, 0.66, 0.68),
            (0.19, 0.18, 0.17),
        ),
    )


def test_valid_comparison_has_three_models_three_folds_and_no_selection(
    models: tuple[PublishedModel, ...],
) -> None:
    result = compare_published_models(models, _experimental_contract())

    assert result.model_comparison.height == 3
    assert result.fold_comparison.height == 9
    assert result.fold_comparison.get_column("fold").unique().sort().to_list() == [1, 2, 3]
    assert result.fold_comparison.get_column("validation_year").unique().sort().to_list() == [
        2022,
        2023,
        2024,
    ]
    assert result.final_selection_performed is False
    assert result.final_test_used is False


def test_comparison_requires_exactly_three_expected_models(
    models: tuple[PublishedModel, ...],
) -> None:
    with pytest.raises(ValueError, match="exatamente três modelos"):
        validate_model_comparability(models[:2], _experimental_contract())

    duplicate = (models[0], models[1], replace(models[2], model_id="outro_modelo"))
    with pytest.raises(ValueError, match="Conjunto de modelos divergente"):
        validate_model_comparability(duplicate, _experimental_contract())


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("train_years", pl.Series(["2020", "2021,2022", "2021,2022,2023"])),
        ("validation_year", pl.Series([2022, 2023, 2025])),
        ("train_rows", pl.Series([101, 200, 300])),
        ("validation_rows", pl.Series([80, 91, 100])),
        ("validation_positive_rate", pl.Series([0.28, 0.2901, 0.27])),
        ("output_feature_count", pl.Series([40, 42, 44])),
    ),
)
def test_structural_divergence_fails_comparability(
    models: tuple[PublishedModel, ...],
    column: str,
    replacement: pl.Series,
) -> None:
    divergent_table = models[2].fold_metrics.with_columns(replacement.alias(column))
    divergent = (*models[:2], replace(models[2], fold_metrics=divergent_table))

    with pytest.raises(ValueError, match=r"divergentes|não é comparável|2025"):
        validate_model_comparability(divergent, _experimental_contract())


def test_fold_count_and_contract_divergence_fail(
    models: tuple[PublishedModel, ...],
) -> None:
    missing_fold = (*models[:2], replace(models[2], fold_metrics=models[2].fold_metrics.head(2)))
    with pytest.raises(ValueError, match="três folds"):
        validate_model_comparability(missing_fold, _experimental_contract())

    wrong_metric = models[2].summary | {"primary_metric": "ROC-AUC"}
    divergent = (*models[:2], replace(models[2], summary=wrong_metric))
    with pytest.raises(ValueError, match="Métrica primária divergente"):
        validate_model_comparability(divergent, _experimental_contract())


def test_ap_mean_population_std_and_ranks_are_correct(
    models: tuple[PublishedModel, ...],
) -> None:
    table = compare_published_models(models, _experimental_contract()).model_comparison
    rows = {str(row["model_id"]): row for row in table.iter_rows(named=True)}

    assert rows[LOGISTIC_MODEL_ID]["ap_unweighted_mean"] == pytest.approx(
        np.mean([0.30, 0.32, 0.33])
    )
    assert rows[LOGISTIC_MODEL_ID]["ap_population_std"] == pytest.approx(
        np.std([0.30, 0.32, 0.33], ddof=0)
    )
    assert rows[XGBOOST_MODEL_ID]["primary_metric_rank"] == 1
    assert rows[RANDOM_FOREST_MODEL_ID]["primary_metric_rank"] == 2
    assert rows[LOGISTIC_MODEL_ID]["primary_metric_rank"] == 3
    assert rows[XGBOOST_MODEL_ID]["ap_fold3_rank"] == 1
    assert rows[LOGISTIC_MODEL_ID]["ap_std_rank"] == 1


def test_pairwise_deltas_use_model_b_minus_model_a(
    models: tuple[PublishedModel, ...],
) -> None:
    deltas = compare_published_models(models, _experimental_contract()).pairwise_ap_deltas
    logistic_xgboost = deltas.filter(
        (pl.col("model_a") == LOGISTIC_MODEL_ID) & (pl.col("model_b") == XGBOOST_MODEL_ID)
    ).row(0, named=True)

    assert logistic_xgboost["ap_delta_fold1"] == pytest.approx(0.02)
    assert logistic_xgboost["ap_delta_fold2"] == pytest.approx(0.05)
    assert logistic_xgboost["ap_delta_fold3"] == pytest.approx(0.07)
    assert logistic_xgboost["ap_mean_delta"] == pytest.approx(np.mean([0.02, 0.05, 0.07]))


def test_temporal_stability_uses_raw_folds_and_ddof_zero(
    models: tuple[PublishedModel, ...],
) -> None:
    stability = compare_published_models(models, _experimental_contract()).temporal_stability
    logistic = stability.filter(pl.col("model_id") == LOGISTIC_MODEL_ID).row(0, named=True)

    assert logistic["ap_min"] == 0.30
    assert logistic["ap_max"] == 0.33
    assert logistic["ap_range"] == pytest.approx(0.03)
    assert logistic["ap_population_std"] == pytest.approx(np.std([0.30, 0.32, 0.33], ddof=0))
    assert logistic["fold1_to_fold2_delta"] == pytest.approx(0.02)
    assert logistic["fold2_to_fold3_delta"] == pytest.approx(0.01)


def test_writing_uses_tmp_path_and_creates_only_comparison_tables(
    tmp_path: Path,
    models: tuple[PublishedModel, ...],
) -> None:
    result = compare_published_models(models, _experimental_contract())
    paths = write_model_comparison_tables(result, tmp_path)

    assert {path.name for path in paths} == {
        "phase_4d_model_comparison.csv",
        "phase_4d_fold_comparison.csv",
        "phase_4d_pairwise_ap_deltas.csv",
        "phase_4d_temporal_stability.csv",
    }
    assert all(path.is_file() for path in paths)
    assert len(list(tmp_path.iterdir())) == 4
