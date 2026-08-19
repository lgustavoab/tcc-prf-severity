from datetime import date, time
from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.analysis.temporal import (
    DAY_PHASE_ORDER,
    MONTH_ORDER,
    WEEKDAY_ORDER,
    analyze_temporal,
    derive_temporal_columns,
    temporal_by_year,
    temporal_stability,
    temporal_summary,
    weekday_group_summary,
    write_temporal_tables,
)
from tcc_prf_severity.analysis.temporal_plots import write_temporal_figures


def _synthetic_dataset() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "data_inversa": [
                date(2021, 12, 6),
                date(2021, 1, 9),
                date(2022, 2, 13),
                date(2022, 1, 4),
                date(2022, 12, 7),
                date(2022, 2, 10),
            ],
            "dia_semana": [
                "segunda-feira",
                "sábado",
                "domingo",
                "terça-feira",
                "quarta-feira",
                "quinta-feira",
            ],
            "horario": [
                time(23, 59),
                time(0, 1),
                time(12, 30),
                time(8),
                time(18),
                time(12),
            ],
            "fase_dia": [
                "Plena Noite",
                "Amanhecer",
                "Pleno dia",
                "Pleno dia",
                "Anoitecer",
                "Pleno dia",
            ],
            "source_year": [2021, 2021, 2022, 2022, 2022, 2022],
            "target_grave": [True, False, True, False, True, False],
        }
    )


def test_month_is_extracted_from_date() -> None:
    derived = derive_temporal_columns(_synthetic_dataset())

    assert derived.get_column("month_number").to_list() == [12, 1, 2, 1, 12, 2]
    assert derived.get_column("month_name").to_list() == [
        "Dezembro",
        "Janeiro",
        "Fevereiro",
        "Janeiro",
        "Dezembro",
        "Fevereiro",
    ]


def test_month_summary_uses_chronological_order() -> None:
    derived = derive_temporal_columns(_synthetic_dataset())

    summary = temporal_summary(derived, "month_name", MONTH_ORDER)

    assert summary.get_column("month_name").to_list() == ["Janeiro", "Fevereiro", "Dezembro"]


def test_weekday_summary_uses_monday_to_sunday_order() -> None:
    summary = temporal_summary(_synthetic_dataset(), "dia_semana", WEEKDAY_ORDER)

    assert summary.get_column("dia_semana").to_list() == [
        *WEEKDAY_ORDER[:4],
        "sábado",
        "domingo",
    ]


def test_hour_is_extracted_between_zero_and_twenty_three() -> None:
    hours = derive_temporal_columns(_synthetic_dataset()).get_column("hour")

    assert hours.min() == 0
    assert hours.max() == 23


def test_temporal_summary_calculates_total_and_classes() -> None:
    summary = temporal_summary(_synthetic_dataset(), "fase_dia", DAY_PHASE_ORDER)

    pleno_dia = summary.filter(pl.col("fase_dia") == "Pleno dia").row(0, named=True)
    assert pleno_dia["total_occurrences"] == 3
    assert pleno_dia["severe_occurrences"] == 1
    assert pleno_dia["non_severe_occurrences"] == 2


def test_temporal_summary_calculates_severe_rate() -> None:
    summary = temporal_summary(_synthetic_dataset(), "fase_dia", DAY_PHASE_ORDER)

    pleno_dia = summary.filter(pl.col("fase_dia") == "Pleno dia").row(0, named=True)
    assert pleno_dia["severe_rate_percent"] == pytest.approx(100 / 3)


def test_temporal_summary_shares_sum_to_one_hundred_percent() -> None:
    summary = temporal_summary(_synthetic_dataset(), "dia_semana", WEEKDAY_ORDER)

    assert summary.get_column("dataset_share_percent").sum() == pytest.approx(100.0)


def test_temporal_by_year_aggregates_year_and_category() -> None:
    derived = derive_temporal_columns(_synthetic_dataset())

    summary = temporal_by_year(derived, "month_name", MONTH_ORDER)

    assert summary.height == 5
    assert int(summary.get_column("total_occurrences").sum()) == 6
    assert summary.select("source_year").unique().sort("source_year").to_series().to_list() == [
        2021,
        2022,
    ]


def test_weekday_group_separates_workdays_and_weekend() -> None:
    summary = weekday_group_summary(_synthetic_dataset())

    assert summary.get_column("weekday_group").to_list() == ["Dias úteis", "Fim de semana"]
    assert summary.get_column("total_occurrences").to_list() == [4, 2]
    assert summary.get_column("severe_occurrences").to_list() == [2, 1]


def test_stability_calculates_minimum_maximum_and_range() -> None:
    by_year = pl.DataFrame(
        {
            "source_year": [2021, 2022],
            "category": ["A", "A"],
            "total_occurrences": [10, 10],
            "severe_occurrences": [2, 4],
            "severe_rate_percent": [20.0, 40.0],
        }
    )

    stability = temporal_stability((("test", by_year, "category"),)).row(0, named=True)

    assert stability["minimum_annual_rate_percent"] == 20.0
    assert stability["maximum_annual_rate_percent"] == 40.0
    assert stability["range_percentage_points"] == 20.0


def test_hour_summary_preserves_first_and_last_hour_order() -> None:
    derived = derive_temporal_columns(_synthetic_dataset())

    summary = temporal_summary(derived, "hour", tuple(range(24)))

    assert summary.get_column("hour")[0] == 0
    assert summary.get_column("hour")[-1] == 23


def test_temporal_analysis_does_not_modify_input_dataframe() -> None:
    df = _synthetic_dataset()
    before = df.clone()

    analyze_temporal(df)

    assert df.equals(before)


def test_temporal_tables_are_written_to_requested_directory(tmp_path: Path) -> None:
    paths = write_temporal_tables(analyze_temporal(_synthetic_dataset()), tmp_path)

    assert len(paths) == 10
    assert {path.name for path in paths} >= {
        "phase_2b_month_summary.csv",
        "phase_2b_hour_by_year.csv",
        "phase_2b_temporal_stability.csv",
    }
    assert all(path.is_file() for path in paths)


def test_temporal_figures_are_written_to_requested_directory(tmp_path: Path) -> None:
    paths = write_temporal_figures(analyze_temporal(_synthetic_dataset()), tmp_path)

    assert len(paths) == 7
    assert {path.name for path in paths} >= {
        "phase_2b_occurrences_by_month.png",
        "phase_2b_severe_rate_by_hour.png",
        "phase_2b_severe_rate_by_day_phase.png",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
