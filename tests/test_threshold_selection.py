from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from tcc_prf_severity.modeling.model_comparison import XGBOOST_MODEL_ID
from tcc_prf_severity.modeling.threshold_selection import (
    EXPECTED_COLUMNS,
    SELECTED_MODEL_FAMILY,
    ThresholdSelectionInputs,
    evaluate_threshold,
    load_threshold_selection_inputs,
    search_unique_probability_thresholds,
    select_threshold,
    validate_oof,
    validate_selected_model,
    write_threshold_selection_tables,
)


def _oof() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "id": ["a", "b", "c", "d", "e", "f"],
            "source_year": [2022, 2022, 2023, 2023, 2024, 2024],
            "fold": [1, 1, 2, 2, 3, 3],
            "target_grave": [True, False, True, False, True, False],
            "predicted_probability_grave": [0.9, 0.8, 0.8, 0.4, 0.2, 0.1],
        }
    )


def _inputs() -> ThresholdSelectionInputs:
    return ThresholdSelectionInputs(
        model_selection={
            "selection_status": "selected",
            "selected_model_id": XGBOOST_MODEL_ID,
            "selected_model_family": SELECTED_MODEL_FAMILY,
            "internal_validation_years": "2022,2023,2024",
            "final_test_year": "2025_reserved",
            "final_test_used": "false",
            "threshold_selected": "false",
            "refit_performed": "false",
        },
        model_contract={
            "model_family": SELECTED_MODEL_FAMILY,
            "preprocessing": "phase_3e",
            "validation": "expanding_window_3_folds",
            "primary_metric": "Average Precision",
            "model_selection_aggregation": "unweighted_fold_mean",
            "threshold_policy": "not_selected_0.5_reference_only",
            "final_test_year": "2025_reserved",
        },
        experimental_contract={
            "threshold_selection_source": "temporal_OOF_2022_2024",
            "threshold_objective": "maximize_positive_class_F1",
            "threshold_tie_break": "higher_recall_then_lower_threshold",
            "final_holdout_policy": "no_optimization_or_fit_on_2025",
        },
        fold_metrics=pl.DataFrame(
            {
                "fold": [1, 2, 3],
                "validation_year": [2022, 2023, 2024],
                "validation_rows": [2, 2, 2],
            }
        ),
        oof=_oof(),
        oof_sha256="a" * 64,
    )


def _arrays() -> tuple[np.ndarray, np.ndarray]:
    oof = _oof()
    return (
        oof["predicted_probability_grave"].to_numpy(),
        oof["target_grave"].to_numpy(),
    )


def test_selected_xgboost_and_frozen_contracts_are_accepted() -> None:
    validate_selected_model(_inputs())


def test_different_selected_model_is_rejected() -> None:
    inputs = _inputs()
    selection = inputs.model_selection | {"selected_model_id": "phase_4b_random_forest_baseline"}

    with pytest.raises(ValueError, match="não autoriza"):
        validate_selected_model(replace(inputs, model_selection=selection))


@pytest.mark.parametrize("forbidden_year", [2021, 2025])
def test_year_outside_2022_2024_is_rejected(forbidden_year: int) -> None:
    inputs = _inputs()
    divergent = inputs.oof.with_columns(
        pl.when(pl.col("id") == "a")
        .then(forbidden_year)
        .otherwise(pl.col("source_year"))
        .alias("source_year")
    )

    with pytest.raises(ValueError, match="2022-2024"):
        validate_oof(replace(inputs, oof=divergent))


def test_unique_ids_are_required() -> None:
    inputs = _inputs()
    divergent = inputs.oof.with_columns(
        pl.when(pl.col("id") == "f").then(pl.lit("a")).otherwise(pl.col("id")).alias("id")
    )

    with pytest.raises(ValueError, match="não são únicos"):
        validate_oof(replace(inputs, oof=divergent))


def test_year_fold_mapping_is_required() -> None:
    inputs = _inputs()
    divergent = inputs.oof.with_columns(
        pl.when(pl.col("id") == "a").then(2).otherwise(pl.col("fold")).alias("fold")
    )

    with pytest.raises(ValueError, match="Mapeamento ano/fold"):
        validate_oof(replace(inputs, oof=divergent))


@pytest.mark.parametrize("invalid", [float("nan"), float("inf")])
def test_probabilities_must_be_finite(invalid: float) -> None:
    inputs = _inputs()
    divergent = inputs.oof.with_columns(
        pl.when(pl.col("id") == "a")
        .then(invalid)
        .otherwise(pl.col("predicted_probability_grave"))
        .alias("predicted_probability_grave")
    )

    with pytest.raises(ValueError, match="finitas"):
        validate_oof(replace(inputs, oof=divergent))


@pytest.mark.parametrize("invalid", [-0.01, 1.01])
def test_probabilities_must_be_in_unit_interval(invalid: float) -> None:
    inputs = _inputs()
    divergent = inputs.oof.with_columns(
        pl.when(pl.col("id") == "a")
        .then(invalid)
        .otherwise(pl.col("predicted_probability_grave"))
        .alias("predicted_probability_grave")
    )

    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        validate_oof(replace(inputs, oof=divergent))


def test_target_must_be_boolean() -> None:
    inputs = _inputs()

    with pytest.raises(ValueError, match="dtype booleano"):
        validate_oof(
            replace(inputs, oof=inputs.oof.with_columns(pl.col("target_grave").cast(pl.Int8)))
        )


def test_columns_must_be_exact_and_fold_counts_must_reconcile() -> None:
    inputs = _inputs()
    with pytest.raises(ValueError, match="Colunas do OOF"):
        validate_oof(replace(inputs, oof=inputs.oof.select(reversed(EXPECTED_COLUMNS))))

    divergent_metrics = inputs.fold_metrics.with_columns(
        pl.when(pl.col("fold") == 1)
        .then(3)
        .otherwise(pl.col("validation_rows"))
        .alias("validation_rows")
    )
    with pytest.raises(ValueError, match="não reconciliam"):
        validate_oof(replace(inputs, fold_metrics=divergent_metrics))


def test_unique_scores_are_candidates_and_repeated_scores_are_grouped() -> None:
    probabilities, targets = _arrays()
    search = search_unique_probability_thresholds(probabilities, targets)

    assert search.candidate_count == 5
    assert search.candidate_count == np.unique(probabilities).size


def test_prediction_rule_is_greater_than_or_equal_and_metrics_are_exact() -> None:
    metrics = evaluate_threshold(np.asarray([0.5, 0.5, 0.49]), np.asarray([True, False, True]), 0.5)

    assert (metrics.tp, metrics.fp, metrics.fn, metrics.tn) == (1, 1, 1, 0)
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5


def test_search_selects_the_exact_maximum_f1() -> None:
    probabilities, targets = _arrays()
    search = search_unique_probability_thresholds(probabilities, targets)

    observed = [
        evaluate_threshold(probabilities, targets, float(threshold)).f1
        for threshold in np.unique(probabilities)
    ]
    assert search.selected.f1 == max(observed)
    assert search.maximum_f1 == search.selected.f1


def test_exact_f1_tie_uses_higher_recall_without_tolerance() -> None:
    search = search_unique_probability_thresholds(
        np.asarray([0.9, 0.2, 0.2, 0.2]), np.asarray([True, True, False, False])
    )

    assert search.candidates_at_maximum_f1 == 2
    assert search.maximum_f1 == 2 / 3
    assert search.selected.threshold == 0.2
    assert search.selected.recall == 1.0
    assert search.tie_break_recall_applied
    assert not search.tie_break_lower_threshold_applied


def test_exact_f1_and_recall_tie_uses_lower_threshold() -> None:
    search = search_unique_probability_thresholds(
        np.asarray([0.9, 0.4, 0.1]), np.asarray([False, False, False])
    )

    assert search.candidates_at_maximum_f1 == 3
    assert search.selected.threshold == 0.1
    assert not search.tie_break_recall_applied
    assert search.tie_break_lower_threshold_applied


def test_reference_0_5_does_not_change_candidate_search() -> None:
    probabilities = np.asarray([0.9, 0.7, 0.2])
    targets = np.asarray([True, False, True])
    search = search_unique_probability_thresholds(probabilities, targets)
    reference = evaluate_threshold(probabilities, targets, 0.5)

    assert 0.5 not in probabilities
    assert search.candidate_count == 3
    assert search.selected.threshold == 0.2
    assert reference.threshold == 0.5


def test_pooled_and_annual_metrics_use_one_frozen_threshold() -> None:
    result = select_threshold(_inputs())
    evaluation = result.evaluation
    annual = evaluation.filter(pl.col("validation_year").is_not_null())

    assert evaluation.height == 5
    assert evaluation.filter(pl.col("scope") == "pooled_oof").height == 2
    assert annual["validation_year"].to_list() == [2022, 2023, 2024]
    assert annual["threshold"].n_unique() == 1
    assert annual["threshold"].item(0) == result.search.selected.threshold
    assert annual["rows"].sum() == result.search.selected.rows
    assert annual["tp"].sum() == result.search.selected.tp
    assert annual["fp"].sum() == result.search.selected.fp
    assert annual["fn"].sum() == result.search.selected.fn
    assert annual["tn"].sum() == result.search.selected.tn


def test_checklist_has_all_substantive_checks_and_passes() -> None:
    result = select_threshold(_inputs())

    assert result.checklist.height == 17
    assert result.checklist["status"].unique().to_list() == ["PASS"]
    assert (
        result.selection.filter(pl.col("key") == "selection_status")["value"].item() == "selected"
    )


def test_module_does_not_import_or_instantiate_classifiers() -> None:
    source = Path("src/tcc_prf_severity/modeling/threshold_selection.py").read_text(
        encoding="utf-8"
    )

    for forbidden in (
        "XGBClassifier",
        "RandomForestClassifier",
        "LogisticRegression",
        "predict_proba",
        "pipeline.fit",
        "sklearn",
        "import xgboost",
    ):
        assert forbidden not in source


def test_missing_oof_fails_without_silent_model_execution(tmp_path: Path) -> None:
    for filename in (
        "phase_4e_model_selection.csv",
        "phase_4c_xgboost_model_contract.csv",
        "phase_4c_xgboost_fold_metrics.csv",
        "phase_3d_experimental_contract.csv",
    ):
        (tmp_path / filename).write_text("key,value\na,b\n", encoding="utf-8")
    phase_4e_doc = tmp_path / "phase_4e.md"
    acceptance = tmp_path / "acceptance.md"
    phase_4e_doc.write_text("4E", encoding="utf-8")
    acceptance.write_text("3F", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="Reproduza explicitamente a Fase 4C"):
        load_threshold_selection_inputs(
            tables_dir=tmp_path,
            oof_path=tmp_path / "missing.parquet",
            experimental_contract_path=tmp_path / "phase_3d_experimental_contract.csv",
            phase_4e_document_path=phase_4e_doc,
            premodeling_acceptance_path=acceptance,
        )


def test_writing_uses_tmp_path_and_persists_only_four_tables(tmp_path: Path) -> None:
    paths = write_threshold_selection_tables(select_threshold(_inputs()), tmp_path)

    assert {path.name for path in paths} == {
        "phase_4f_threshold_selection.csv",
        "phase_4f_threshold_evaluation.csv",
        "phase_4f_threshold_search_summary.csv",
        "phase_4f_threshold_checklist.csv",
    }
    assert all(path.is_file() for path in paths)
    assert len(list(tmp_path.iterdir())) == 4
