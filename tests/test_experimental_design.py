from datetime import date
from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.modeling.experimental_design import (
    DEVELOPMENT_YEARS,
    FINAL_TEST_YEAR,
    METADATA_COLUMNS,
    PRIMARY_METRIC,
    TARGET_COLUMN,
    TemporalFold,
    analyze_experimental_design,
    build_experimental_contract,
    build_partition_summary,
    build_temporal_folds,
    load_predictors_from_schema,
    validate_temporal_design,
    write_experimental_design_tables,
)


def _dataset() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "id": ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
            "source_year": [2021, 2021, 2022, 2022, 2023, 2024, 2024, 2025, 2025],
            "data_inversa": [
                date(2021, 1, 1),
                date(2021, 2, 1),
                date(2022, 1, 1),
                date(2022, 2, 1),
                date(2023, 1, 1),
                date(2024, 1, 1),
                date(2024, 2, 1),
                date(2025, 1, 1),
                date(2025, 2, 1),
            ],
            "target_grave": [True, False, True, False, False, True, False, True, False],
            "feature_a": ["x"] * 9,
            "feature_b": list(range(9)),
        }
    )


def _write_schema(path: Path) -> None:
    pl.DataFrame(
        {
            "column": [*METADATA_COLUMNS, TARGET_COLUMN, "feature_a", "feature_b"],
            "role": ["metadata", "metadata", "metadata", "target", "predictor", "predictor"],
            "included_in_model_matrix": [False, False, False, False, True, True],
        }
    ).write_csv(path)


@pytest.fixture
def schema_path(tmp_path: Path) -> Path:
    path = tmp_path / "schema.csv"
    _write_schema(path)
    return path


def test_main_temporal_boundary_is_development_2021_2024_and_final_2025() -> None:
    df = _dataset()

    development = df.filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS))
    final_test = df.filter(pl.col("source_year") == FINAL_TEST_YEAR)

    assert set(development.get_column("source_year")) == {2021, 2022, 2023, 2024}
    assert set(final_test.get_column("source_year")) == {2025}
    assert development.height == 7
    assert final_test.height == 2


def test_expanding_window_folds_are_exact_and_exclude_2025() -> None:
    folds = build_temporal_folds()

    assert folds == (
        TemporalFold(1, (2021,), 2022),
        TemporalFold(2, (2021, 2022), 2023),
        TemporalFold(3, (2021, 2022, 2023), 2024),
    )
    assert all(2025 not in (*fold.train_years, fold.validation_year) for fold in folds)


def test_validation_year_never_appears_in_train_and_future_is_rejected() -> None:
    predictors = ("feature_a", "feature_b")
    folds = build_temporal_folds()
    validate_temporal_design(_dataset(), predictors, folds)
    assert all(fold.validation_year not in fold.train_years for fold in folds)
    assert all(max(fold.train_years) < fold.validation_year for fold in folds)

    invalid = (TemporalFold(1, (2021, 2023), 2022), *folds[1:])
    with pytest.raises(ValueError, match=r"folds divergem|futuro"):
        validate_temporal_design(_dataset(), predictors, invalid)


def test_main_partitions_preserve_all_rows_and_are_disjoint() -> None:
    df = _dataset()
    development = df.filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS))
    final_test = df.filter(pl.col("source_year") == FINAL_TEST_YEAR)

    assert development.height + final_test.height == df.height
    assert not (
        set(development.get_column("id").to_list()) & set(final_test.get_column("id").to_list())
    )


def test_predictors_come_only_from_schema_and_exclude_metadata_and_target(
    schema_path: Path,
) -> None:
    predictors = load_predictors_from_schema(schema_path)

    assert predictors == ("feature_a", "feature_b")
    assert not (set(METADATA_COLUMNS) & set(predictors))
    assert TARGET_COLUMN not in predictors


def test_schema_rejects_metadata_in_model_matrix(schema_path: Path) -> None:
    schema = pl.read_csv(schema_path).with_columns(
        pl.when(pl.col("column") == "source_year")
        .then(pl.lit(True))
        .otherwise(pl.col("included_in_model_matrix"))
        .alias("included_in_model_matrix")
    )
    schema.write_csv(schema_path)

    with pytest.raises(ValueError, match=r"metadata|não preditoras"):
        load_predictors_from_schema(schema_path)


def test_partition_summary_calculates_rows_classes_and_prevalence() -> None:
    summary = build_partition_summary(_dataset(), build_temporal_folds())
    year_2021 = summary.filter(pl.col("partition_id") == "year_2021").row(0, named=True)
    development = summary.filter(pl.col("partition_id") == "development").row(0, named=True)

    assert year_2021["rows"] == 2
    assert year_2021["severe"] == 1
    assert year_2021["non_severe"] == 1
    assert year_2021["severe_rate_percent"] == 50.0
    assert development["rows"] == 7


def test_positive_class_remains_true_and_target_is_not_reencoded() -> None:
    df = _dataset()
    before = df.get_column(TARGET_COLUMN).clone()

    design = analyze_experimental_design(df, ("feature_a", "feature_b"))

    assert df.get_column(TARGET_COLUMN).dtype == pl.Boolean
    assert df.get_column(TARGET_COLUMN).equals(before)
    assert int(df.get_column(TARGET_COLUMN).sum()) == 4
    assert design.partition_summary.get_column("severe").sum() > 0


def test_experimental_contract_freezes_metrics_threshold_and_refit() -> None:
    contract = build_experimental_contract(("feature_a", "feature_b"))
    values = {str(row["key"]): str(row["value"]) for row in contract.iter_rows(named=True)}

    assert values["primary_metric"] == PRIMARY_METRIC
    assert values["primary_metric"] == "Average Precision (AP)"
    assert values["fold_aggregation"] == "unweighted_mean_AP_plus_std_and_latest_fold"
    assert values["secondary_metrics"] == (
        "ROC-AUC; recall; precision; F1; confusion_matrix; calibration; Brier_score"
    )
    assert values["diagnostic_outputs"] == "Precision-Recall_curve"
    assert values["threshold_selection_source"] == "temporal_OOF_2022_2024"
    assert values["threshold_objective"] == "maximize_positive_class_F1"
    assert values["threshold_tie_break"] == "higher_recall_then_lower_threshold"
    assert values["final_refit_period"] == "2021-2024"
    assert values["final_holdout_policy"] == "no_optimization_or_fit_on_2025"


def test_design_uses_explicit_years_without_random_split(schema_path: Path) -> None:
    predictors = load_predictors_from_schema(schema_path)
    design = analyze_experimental_design(_dataset(), predictors)

    assert design.folds == build_temporal_folds()
    assert (
        design.experimental_contract.filter(pl.col("key") == "validation_strategy")
        .get_column("value")
        .item()
        == "expanding_window_by_source_year"
    )


def test_analysis_does_not_modify_source_dataframe(schema_path: Path) -> None:
    source = _dataset()
    before = source.clone()

    analyze_experimental_design(source, load_predictors_from_schema(schema_path))

    assert source.equals(before)


def test_three_tables_are_written_to_tmp_path(tmp_path: Path, schema_path: Path) -> None:
    design = analyze_experimental_design(_dataset(), load_predictors_from_schema(schema_path))
    output_dir = tmp_path / "tables"

    paths = write_experimental_design_tables(design, output_dir)

    assert {path.name for path in paths} == {
        "phase_3d_partition_summary.csv",
        "phase_3d_temporal_folds.csv",
        "phase_3d_experimental_contract.csv",
    }
    assert all(path.is_file() for path in paths)
