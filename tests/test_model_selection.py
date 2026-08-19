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
)
from tcc_prf_severity.modeling.model_selection import (
    MODEL_CONTRACT_FILENAMES,
    ModelSelectionInputs,
    build_selection_checklist,
    run_model_selection,
    select_model,
    write_model_selection_tables,
)


def _key_values(table: pl.DataFrame) -> dict[str, str]:
    return {str(row["key"]): str(row["value"]) for row in table.iter_rows(named=True)}


def _inputs() -> ModelSelectionInputs:
    models = (
        {
            "model_id": LOGISTIC_MODEL_ID,
            "model_family": "logistic_regression",
            "ap": (0.36, 0.36, 0.36),
            "roc": (0.99, 0.99, 0.99),
            "brier": (0.01, 0.01, 0.01),
        },
        {
            "model_id": RANDOM_FOREST_MODEL_ID,
            "model_family": "random_forest",
            "ap": (0.40, 0.41, 0.42),
            "roc": (0.70, 0.71, 0.72),
            "brier": (0.20, 0.19, 0.18),
        },
        {
            "model_id": XGBOOST_MODEL_ID,
            "model_family": "xgboost_gradient_boosted_trees",
            "ap": (0.30, 0.31, 0.50),
            "roc": (0.80, 0.81, 0.82),
            "brier": (0.10, 0.09, 0.08),
        },
    )
    comparison_rows = []
    fold_rows = []
    stability_rows = []
    for model in models:
        ap = np.asarray(model["ap"], dtype=float)
        roc = np.asarray(model["roc"], dtype=float)
        brier = np.asarray(model["brier"], dtype=float)
        comparison_rows.append(
            {
                "model_id": model["model_id"],
                "model_family": model["model_family"],
                "ap_fold1": ap[0],
                "ap_fold2": ap[1],
                "ap_fold3": ap[2],
                "ap_unweighted_mean": np.mean(ap),
                "ap_population_std": np.std(ap, ddof=0),
                "mean_roc_auc": np.mean(roc),
                "mean_brier_score": np.mean(brier),
            }
        )
        for fold, year, ap_value, roc_value, brier_value in zip(
            (1, 2, 3), (2022, 2023, 2024), ap, roc, brier, strict=True
        ):
            fold_rows.append(
                {
                    "fold": fold,
                    "validation_year": year,
                    "model_id": model["model_id"],
                    "average_precision": ap_value,
                    "roc_auc": roc_value,
                    "brier_score": brier_value,
                    "validation_positive_rate": 0.28,
                }
            )
        stability_rows.append(
            {
                "model_id": model["model_id"],
                "ap_min": np.min(ap),
                "ap_max": np.max(ap),
                "ap_range": np.max(ap) - np.min(ap),
                "ap_population_std": np.std(ap, ddof=0),
                "fold1_to_fold2_delta": ap[1] - ap[0],
                "fold2_to_fold3_delta": ap[2] - ap[1],
            }
        )
    comparison = pl.DataFrame(comparison_rows).with_columns(
        pl.col("ap_unweighted_mean")
        .rank(method="min", descending=True)
        .cast(pl.Int64)
        .alias("primary_metric_rank"),
        pl.col("ap_fold3")
        .rank(method="min", descending=True)
        .cast(pl.Int64)
        .alias("ap_fold3_rank"),
        pl.col("ap_population_std").rank(method="min").cast(pl.Int64).alias("ap_std_rank"),
    )
    metrics = {str(row["model_id"]): row for row in comparison.iter_rows(named=True)}
    pairs = (
        (LOGISTIC_MODEL_ID, RANDOM_FOREST_MODEL_ID),
        (LOGISTIC_MODEL_ID, XGBOOST_MODEL_ID),
        (RANDOM_FOREST_MODEL_ID, XGBOOST_MODEL_ID),
    )
    delta_rows = []
    for model_a, model_b in pairs:
        a, b = metrics[model_a], metrics[model_b]
        delta_rows.append(
            {
                "model_a": model_a,
                "model_b": model_b,
                "ap_delta_fold1": float(b["ap_fold1"]) - float(a["ap_fold1"]),
                "ap_delta_fold2": float(b["ap_fold2"]) - float(a["ap_fold2"]),
                "ap_delta_fold3": float(b["ap_fold3"]) - float(a["ap_fold3"]),
                "ap_mean_delta": float(b["ap_unweighted_mean"]) - float(a["ap_unweighted_mean"]),
            }
        )
    contracts = {
        str(model["model_id"]): {
            "model_family": str(model["model_family"]),
            "role": "baseline" if model["model_id"] == LOGISTIC_MODEL_ID else "baseline_candidate",
            "preprocessing": "phase_3e",
            "validation": "expanding_window_3_folds",
            "primary_metric": "Average Precision",
            "model_selection_aggregation": "unweighted_fold_mean",
            "threshold_policy": "not_selected_0.5_reference_only",
            "final_test_year": "2025_reserved",
        }
        for model in models
    }
    return ModelSelectionInputs(
        comparison=comparison,
        fold_comparison=pl.DataFrame(fold_rows).sort("fold", "model_id"),
        pairwise_ap_deltas=pl.DataFrame(delta_rows),
        temporal_stability=pl.DataFrame(stability_rows),
        experimental_contract={
            "number_of_internal_folds": "3",
            "primary_metric": "Average Precision (AP)",
            "fold_aggregation": "unweighted_mean_AP_plus_std_and_latest_fold",
            "final_holdout_policy": "no_optimization_or_fit_on_2025",
        },
        model_contracts=contracts,
    )


def test_selects_unique_largest_ap_mean_not_a_hardcoded_family() -> None:
    result = select_model(_inputs())

    assert result.selected_model_id == RANDOM_FOREST_MODEL_ID
    selection = _key_values(result.selection)
    assert selection["selection_status"] == "selected"
    assert float(selection["selected_ap_unweighted_mean"]) == pytest.approx(0.41)
    assert selection["primary_metric_rank"] == "1"


def test_requires_exactly_three_models() -> None:
    inputs = _inputs()
    reduced = replace(
        inputs,
        comparison=inputs.comparison.filter(pl.col("model_id") != LOGISTIC_MODEL_ID),
    )

    with pytest.raises(ValueError, match="checks críticos"):
        select_model(reduced)


@pytest.mark.parametrize(
    ("key", "value"),
    (("primary_metric", "ROC-AUC"), ("fold_aggregation", "weighted_mean")),
)
def test_primary_metric_and_aggregation_are_frozen(key: str, value: str) -> None:
    inputs = _inputs()
    divergent = replace(inputs, experimental_contract=inputs.experimental_contract | {key: value})

    with pytest.raises(ValueError, match="checks críticos"):
        select_model(divergent)


def test_primary_rank_one_must_be_unique() -> None:
    inputs = _inputs()
    ranks = inputs.comparison.with_columns(
        pl.when(pl.col("model_id") == XGBOOST_MODEL_ID)
        .then(1)
        .otherwise(pl.col("primary_metric_rank"))
        .alias("primary_metric_rank")
    )

    with pytest.raises(ValueError, match="exatamente um modelo"):
        select_model(replace(inputs, comparison=ranks))


def test_argmax_and_rank_must_coincide() -> None:
    inputs = _inputs()
    ranks = inputs.comparison.with_columns(
        pl.when(pl.col("model_id") == XGBOOST_MODEL_ID)
        .then(1)
        .when(pl.col("model_id") == RANDOM_FOREST_MODEL_ID)
        .then(2)
        .otherwise(pl.col("primary_metric_rank"))
        .alias("primary_metric_rank")
    )

    with pytest.raises(ValueError, match="não coincidem"):
        select_model(replace(inputs, comparison=ranks))


def test_exact_tie_at_largest_ap_mean_stops_without_tiebreak() -> None:
    inputs = _inputs()
    tied = inputs.comparison.with_columns(
        pl.when(pl.col("model_id") == XGBOOST_MODEL_ID)
        .then(0.41)
        .otherwise(pl.col("ap_unweighted_mean"))
        .alias("ap_unweighted_mean")
    )

    with pytest.raises(ValueError, match="Empate exato"):
        select_model(replace(inputs, comparison=tied))


def test_std_fold3_roc_auc_and_brier_do_not_replace_ap_mean() -> None:
    inputs = _inputs()
    selected = select_model(inputs)
    rows = {str(row["model_id"]): row for row in inputs.comparison.iter_rows(named=True)}

    assert rows[LOGISTIC_MODEL_ID]["ap_std_rank"] == 1
    assert rows[XGBOOST_MODEL_ID]["ap_fold3_rank"] == 1
    assert rows[LOGISTIC_MODEL_ID]["mean_roc_auc"] > rows[RANDOM_FOREST_MODEL_ID]["mean_roc_auc"]
    assert (
        rows[LOGISTIC_MODEL_ID]["mean_brier_score"]
        < rows[RANDOM_FOREST_MODEL_ID]["mean_brier_score"]
    )
    assert selected.selected_model_id == RANDOM_FOREST_MODEL_ID


def test_2025_remains_reserved_and_selection_flags_remain_false() -> None:
    selection = _key_values(select_model(_inputs()).selection)

    assert selection["development_period"] == "2021-2024"
    assert selection["internal_validation_years"] == "2022,2023,2024"
    assert selection["final_test_year"] == "2025_reserved"
    assert selection["final_test_used"] == "false"
    assert selection["threshold_selected"] == "false"
    assert selection["refit_performed"] == "false"
    assert selection["hyperparameter_tuning_after_comparison"] == "false"


def test_selected_model_contract_is_required_and_validated() -> None:
    inputs = _inputs()
    contracts = inputs.model_contracts | {
        RANDOM_FOREST_MODEL_ID: inputs.model_contracts[RANDOM_FOREST_MODEL_ID]
        | {"preprocessing": "outro"}
    }

    with pytest.raises(ValueError, match="checks críticos"):
        select_model(replace(inputs, model_contracts=contracts))


def test_selected_deltas_are_recalculated_from_comparison() -> None:
    selection = _key_values(select_model(_inputs()).selection)

    assert float(selection["delta_vs_logistic_ap_mean"]) == pytest.approx(0.05)
    assert float(selection["delta_vs_random_forest_ap_mean"]) == 0.0


def test_checklist_passes_when_integrity_is_complete() -> None:
    result = select_model(_inputs())

    assert result.checklist.height == 13
    assert result.checklist.get_column("status").unique().to_list() == ["PASS"]


def test_inconsistent_fold_summary_blocks_selection() -> None:
    inputs = _inputs()
    folds = inputs.fold_comparison.with_columns(
        pl.when((pl.col("model_id") == RANDOM_FOREST_MODEL_ID) & (pl.col("fold") == 2))
        .then(0.99)
        .otherwise(pl.col("average_precision"))
        .alias("average_precision")
    )

    checklist = build_selection_checklist(
        replace(inputs, fold_comparison=folds),
        inputs.comparison.filter(pl.col("model_id") == RANDOM_FOREST_MODEL_ID).row(0, named=True),
    )
    assert checklist.filter(pl.col("check_id") == "SEL008")["status"].item() == "FAIL"
    with pytest.raises(ValueError, match="checks críticos"):
        select_model(replace(inputs, fold_comparison=folds))


def test_writing_uses_tmp_path_and_persists_only_two_tables(tmp_path: Path) -> None:
    paths = write_model_selection_tables(select_model(_inputs()), tmp_path)

    assert {path.name for path in paths} == {
        "phase_4e_model_selection.csv",
        "phase_4e_selection_checklist.csv",
    }
    assert all(path.is_file() for path in paths)
    assert len(list(tmp_path.iterdir())) == 2


def test_run_needs_no_dataset_or_oof(tmp_path: Path) -> None:
    inputs = _inputs()
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    inputs.comparison.write_csv(source / "phase_4d_model_comparison.csv")
    inputs.fold_comparison.write_csv(source / "phase_4d_fold_comparison.csv")
    inputs.pairwise_ap_deltas.write_csv(source / "phase_4d_pairwise_ap_deltas.csv")
    inputs.temporal_stability.write_csv(source / "phase_4d_temporal_stability.csv")
    experimental_path = source / "phase_3d_experimental_contract.csv"
    pl.DataFrame(
        {
            "key": list(inputs.experimental_contract),
            "value": list(inputs.experimental_contract.values()),
        }
    ).write_csv(experimental_path)
    for model_id, filename in MODEL_CONTRACT_FILENAMES.items():
        contract = inputs.model_contracts[model_id]
        pl.DataFrame({"key": list(contract), "value": list(contract.values())}).write_csv(
            source / filename
        )
    acceptance = tmp_path / "acceptance.md"
    comparison_doc = tmp_path / "comparison.md"
    acceptance.write_text("aceite", encoding="utf-8")
    comparison_doc.write_text("comparação", encoding="utf-8")

    run = run_model_selection(
        source_tables_dir=source,
        output_tables_dir=output,
        experimental_contract_path=experimental_path,
        premodeling_acceptance_path=acceptance,
        model_comparison_document_path=comparison_doc,
    )

    assert run.result.selected_model_id == RANDOM_FOREST_MODEL_ID
    assert {path.name for path in run.table_paths} == {
        "phase_4e_model_selection.csv",
        "phase_4e_selection_checklist.csv",
    }
