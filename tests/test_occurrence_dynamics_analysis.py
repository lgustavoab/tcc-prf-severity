from pathlib import Path

import polars as pl

from tcc_prf_severity.analysis.occurrence_dynamics import (
    MIN_RATE_HIGHLIGHT_OCCURRENCES,
    analyze_occurrence_dynamics,
    categorical_summary,
    numeric_distribution,
    numeric_summary_statistics,
    severe_rate_ranking,
    write_occurrence_dynamics_tables,
)
from tcc_prf_severity.analysis.occurrence_dynamics_plots import (
    write_occurrence_dynamics_figures,
)


def _synthetic_dataset() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "source_year": [2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024, 2025, 2025],
            "target_grave": [True, False, True, False, True, False, True, False, True, False],
            "tipo_acidente": [
                "Estável",
                "Antigo",
                "Estável",
                "Antigo",
                "Estável",
                "Único",
                "Estável",
                "Novo",
                "Estável",
                "Novo",
            ],
            "causa_acidente": [
                "Comum",
                "Antiga",
                "Comum",
                "Só 2022",
                "Comum",
                "Antiga",
                "Comum",
                "Nova",
                "Comum",
                "Nova",
            ],
            "pessoas": [1, 2, 2, 3, 3, 4, 4, 5, 6, 20],
            "veiculos": [1, 1, 2, 2, 2, 3, 3, 4, 5, 30],
        }
    )


def _large_synthetic_dataset() -> pl.DataFrame:
    return pl.concat([_synthetic_dataset()] * 500, rechunk=True)


def _ranking_summary() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "categoria": ["Grande", "Pequena"],
            "total_occurrences": [500, 499],
            "severe_occurrences": [100, 499],
            "non_severe_occurrences": [400, 0],
            "severe_rate_percent": [20.0, 100.0],
            "dataset_share_percent": [50.05, 49.95],
        }
    )


def test_accident_type_summary_calculates_volume_and_rate() -> None:
    summary = categorical_summary(_synthetic_dataset(), "tipo_acidente")
    stable = summary.filter(pl.col("tipo_acidente") == "Estável").row(0, named=True)

    assert stable["total_occurrences"] == 5
    assert stable["severe_occurrences"] == 5
    assert stable["severe_rate_percent"] == 100.0


def test_cause_summary_preserves_original_categories() -> None:
    summary = categorical_summary(_synthetic_dataset(), "causa_acidente")

    assert set(summary.get_column("causa_acidente")) == {"Comum", "Antiga", "Só 2022", "Nova"}


def test_severe_and_non_severe_reconcile_with_total() -> None:
    summary = categorical_summary(_synthetic_dataset(), "causa_acidente")

    assert (
        summary.get_column("severe_occurrences") + summary.get_column("non_severe_occurrences")
    ).equals(summary.get_column("total_occurrences"))


def test_rate_ranking_applies_minimum_of_five_hundred() -> None:
    ranking = severe_rate_ranking(_ranking_summary(), "categoria")

    assert ranking.get_column("total_occurrences").min() == MIN_RATE_HIGHLIGHT_OCCURRENCES


def test_small_high_rate_category_is_not_highlighted() -> None:
    ranking = severe_rate_ranking(_ranking_summary(), "categoria")

    assert ranking.get_column("categoria").to_list() == ["Grande"]


def test_taxonomy_diagnostics_counts_categories_by_year() -> None:
    diagnostics = analyze_occurrence_dynamics(_synthetic_dataset()).taxonomy_diagnostics
    accident_type_2021 = diagnostics.filter(
        (pl.col("dimension") == "accident_type") & (pl.col("source_year") == 2021)
    ).row(0, named=True)

    assert accident_type_2021["distinct_categories"] == 2


def test_taxonomy_diagnostics_detects_category_in_all_years() -> None:
    analysis = analyze_occurrence_dynamics(_synthetic_dataset())
    stable = analysis.category_lifecycle.filter(
        (pl.col("dimension") == "accident_type") & (pl.col("category") == "Estável")
    ).row(0, named=True)

    assert stable["present_all_years"] is True
    assert stable["years_observed"] == 5


def test_taxonomy_diagnostics_detects_one_year_category() -> None:
    analysis = analyze_occurrence_dynamics(_synthetic_dataset())
    one_year = analysis.category_lifecycle.filter(pl.col("category") == "Só 2022").row(
        0, named=True
    )

    assert one_year["exclusive_to_one_year"] is True


def test_lifecycle_calculates_first_last_and_observed_years() -> None:
    lifecycle = analyze_occurrence_dynamics(_synthetic_dataset()).category_lifecycle
    new_type = lifecycle.filter(pl.col("category") == "Novo").row(0, named=True)

    assert new_type["first_year"] == 2024
    assert new_type["last_year"] == 2025
    assert new_type["years_observed"] == 2


def test_stability_uses_only_years_actually_observed() -> None:
    stability = analyze_occurrence_dynamics(_synthetic_dataset()).category_stability

    assert "Estável" in stability.get_column("category").to_list()
    assert "Novo" not in stability.get_column("category").to_list()
    assert (
        stability.filter(pl.col("category") == "Estável").get_column("years_observed").item() == 5
    )


def test_people_distribution_preserves_exact_values() -> None:
    distribution = numeric_distribution(_synthetic_dataset(), "pessoas")

    assert distribution.get_column("pessoas").to_list() == [1, 2, 3, 4, 5, 6, 20]
    assert int(distribution.get_column("total_occurrences").sum()) == 10


def test_people_summary_statistics_calculates_required_metrics() -> None:
    statistics = numeric_summary_statistics(_synthetic_dataset(), "pessoas").row(0, named=True)

    assert statistics["minimum"] == 1.0
    assert statistics["median"] == 3.5
    assert statistics["maximum"] == 20.0
    assert statistics["p95"] >= statistics["p90"]


def test_vehicle_distribution_preserves_exact_values() -> None:
    distribution = numeric_distribution(_synthetic_dataset(), "veiculos")

    assert distribution.get_column("veiculos").to_list() == [1, 2, 3, 4, 5, 30]
    assert int(distribution.get_column("total_occurrences").sum()) == 10


def test_vehicle_summary_statistics_calculates_required_metrics() -> None:
    statistics = numeric_summary_statistics(_synthetic_dataset(), "veiculos").row(0, named=True)

    assert statistics["minimum"] == 1.0
    assert statistics["median"] == 2.5
    assert statistics["maximum"] == 30.0
    assert statistics["p99"] >= statistics["p95"]


def test_p99_and_count_above_p99_are_reported() -> None:
    df = pl.DataFrame({"pessoas": [1] * 100 + [100]})
    statistics = numeric_summary_statistics(df, "pessoas").row(0, named=True)

    assert statistics["p99"] == 1.0
    assert statistics["occurrences_above_p99"] == 1


def test_analysis_does_not_modify_input_dataframe() -> None:
    df = _synthetic_dataset()
    before = df.clone()

    analyze_occurrence_dynamics(df)

    assert df.equals(before)


def test_tables_are_written_to_requested_directory(tmp_path: Path) -> None:
    paths = write_occurrence_dynamics_tables(
        analyze_occurrence_dynamics(_synthetic_dataset()), tmp_path
    )

    assert len(paths) == 17
    assert {path.name for path in paths} >= {
        "phase_2e_accident_type_summary.csv",
        "phase_2e_cause_severe_rate_top15_n500.csv",
        "phase_2e_taxonomy_diagnostics.csv",
        "phase_2e_people_summary_statistics.csv",
        "phase_2e_vehicle_distribution.csv",
    }
    assert all(path.is_file() for path in paths)


def test_figures_are_written_to_requested_directory(tmp_path: Path) -> None:
    paths = write_occurrence_dynamics_figures(
        analyze_occurrence_dynamics(_large_synthetic_dataset()), tmp_path
    )

    assert len(paths) == 6
    assert {path.name for path in paths} >= {
        "phase_2e_accident_type_volume_top15.png",
        "phase_2e_cause_severe_rate_top15_n500.png",
        "phase_2e_people_distribution.png",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
