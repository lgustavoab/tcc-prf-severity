from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.analysis.geographic import (
    MIN_RATE_RANKING_OCCURRENCES,
    UF_TO_MACROREGION,
    analyze_geographic,
    derive_geographic_columns,
    geographic_summary,
    severe_rate_ranking,
    threshold_diagnostics,
    uf_stability,
    volume_ranking,
    write_geographic_tables,
)
from tcc_prf_severity.analysis.geographic_plots import write_geographic_figures


def _synthetic_dataset() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "uf": ["SP", "SP", "MG", "BA", "BA", "RS"],
            "municipio": ["IGUAL", "SAO PAULO", "IGUAL", "SALVADOR", "SALVADOR", "PORTO"],
            "br": [116, 116, 0, 324, 324, 290],
            "source_year": [2021, 2022, 2021, 2021, 2022, 2022],
            "target_grave": [True, False, False, True, True, False],
            "latitude": [-23.5, -23.6, -19.9, -12.9, -12.8, -30.0],
            "longitude": [-46.6, -46.7, -44.0, -38.5, -38.4, -51.2],
        }
    )


def _ranking_summary() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "br": [0, 1, 2, 3],
            "br_label": ["Não identificada (BR 0)", "BR 1", "BR 2", "BR 3"],
            "total_occurrences": [2000, 1200, 600, 10],
            "severe_occurrences": [1000, 240, 300, 9],
            "severe_rate_percent": [50.0, 20.0, 50.0, 90.0],
        }
    )


def test_uf_is_mapped_to_macroregion() -> None:
    derived = derive_geographic_columns(_synthetic_dataset())

    assert derived.get_column("macroregion").to_list() == [
        "Sudeste",
        "Sudeste",
        "Sudeste",
        "Nordeste",
        "Nordeste",
        "Sul",
    ]


def test_all_twenty_seven_ufs_have_macroregion_mapping() -> None:
    assert len(UF_TO_MACROREGION) == 27
    assert set(UF_TO_MACROREGION.values()) == {
        "Norte",
        "Nordeste",
        "Centro-Oeste",
        "Sudeste",
        "Sul",
    }


def test_unknown_uf_fails_with_clear_message() -> None:
    df = _synthetic_dataset().with_columns(pl.lit("XX").alias("uf"))

    with pytest.raises(ValueError, match=r"UF sem mapeamento.*XX"):
        derive_geographic_columns(df)


def test_geographic_summary_reconciles_total() -> None:
    summary = geographic_summary(_synthetic_dataset(), "uf")

    assert int(summary.get_column("total_occurrences").sum()) == 6


def test_geographic_summary_reconciles_classes() -> None:
    summary = geographic_summary(_synthetic_dataset(), "uf")

    assert (
        summary.get_column("severe_occurrences") + summary.get_column("non_severe_occurrences")
    ).equals(summary.get_column("total_occurrences"))


def test_geographic_summary_calculates_rate() -> None:
    summary = geographic_summary(_synthetic_dataset(), "uf")
    sp = summary.filter(pl.col("uf") == "SP").row(0, named=True)

    assert sp["total_occurrences"] == 2
    assert sp["severe_occurrences"] == 1
    assert sp["severe_rate_percent"] == pytest.approx(50.0)


def test_municipality_grouping_uses_uf_and_name() -> None:
    analysis = analyze_geographic(_synthetic_dataset())
    same_name = analysis.municipality_summary.filter(pl.col("municipio") == "IGUAL")

    assert same_name.height == 2
    assert set(same_name.get_column("municipality_label").to_list()) == {
        "IGUAL - SP",
        "IGUAL - MG",
    }


def test_br_zero_remains_in_complete_summary() -> None:
    analysis = analyze_geographic(_synthetic_dataset())
    br_zero = analysis.br_summary.filter(pl.col("br") == 0).row(0, named=True)

    assert br_zero["total_occurrences"] == 1
    assert br_zero["br_label"] == "Não identificada (BR 0)"


def test_br_zero_is_excluded_from_volume_ranking() -> None:
    ranking = volume_ranking(_ranking_summary(), ("br", "br_label"), exclude_br_zero=True)

    assert 0 not in ranking.get_column("br").to_list()


def test_rate_ranking_applies_minimum_occurrences() -> None:
    ranking = severe_rate_ranking(_ranking_summary(), ("br", "br_label"), exclude_br_zero=True)

    minimum = ranking.get_column("total_occurrences").min()
    assert isinstance(minimum, int)
    assert minimum >= MIN_RATE_RANKING_OCCURRENCES


def test_high_rate_small_category_does_not_enter_rate_ranking() -> None:
    ranking = severe_rate_ranking(_ranking_summary(), ("br", "br_label"), exclude_br_zero=True)

    assert 3 not in ranking.get_column("br").to_list()
    assert ranking.get_column("br")[0] == 2


def test_volume_ranking_does_not_depend_on_rate_threshold() -> None:
    ranking = volume_ranking(_ranking_summary(), ("br", "br_label"), exclude_br_zero=True)

    assert 3 in ranking.get_column("br").to_list()
    assert ranking.get_column("br")[0] == 1


def test_threshold_diagnostics_counts_eligible_categories() -> None:
    br_summary = _ranking_summary()
    municipality_summary = pl.DataFrame(
        {
            "total_occurrences": [50, 100, 500, 1000],
        }
    )

    diagnostics = threshold_diagnostics(br_summary, municipality_summary)
    municipality = diagnostics.filter(pl.col("dimension") == "municipality")

    assert municipality.get_column("eligible_categories").to_list() == [3, 2, 1]
    assert diagnostics.filter(pl.col("dimension") == "br_excluding_zero").get_column(
        "eligible_categories"
    ).to_list() == [2, 2, 1]


def test_uf_stability_calculates_minimum_maximum_and_range() -> None:
    by_year = pl.DataFrame(
        {
            "source_year": [2021, 2022],
            "uf": ["SP", "SP"],
            "severe_rate_percent": [20.0, 32.5],
        }
    )

    stability = uf_stability(by_year).row(0, named=True)

    assert stability["years_observed"] == 2
    assert stability["minimum_annual_rate_percent"] == 20.0
    assert stability["maximum_annual_rate_percent"] == 32.5
    assert stability["range_percentage_points"] == 12.5


def test_geographic_analysis_does_not_modify_input_dataframe() -> None:
    df = _synthetic_dataset()
    before = df.clone()

    analyze_geographic(df)

    assert df.equals(before)


def test_geographic_tables_are_written_to_requested_directory(tmp_path: Path) -> None:
    paths = write_geographic_tables(analyze_geographic(_synthetic_dataset()), tmp_path)

    assert len(paths) == 15
    assert {path.name for path in paths} >= {
        "phase_2c_macroregion_summary.csv",
        "phase_2c_macroregion_stability.csv",
        "phase_2c_uf_volume_top15.csv",
        "phase_2c_br_summary.csv",
        "phase_2c_municipality_severe_rate_top15_n500.csv",
        "phase_2c_coordinate_coverage.csv",
    }
    assert all(path.is_file() for path in paths)


def test_geographic_figures_are_written_to_requested_directory(tmp_path: Path) -> None:
    paths = write_geographic_figures(analyze_geographic(_synthetic_dataset()), tmp_path)

    assert len(paths) == 6
    assert {path.name for path in paths} >= {
        "phase_2c_occurrences_by_macroregion.png",
        "phase_2c_severe_rate_by_uf.png",
        "phase_2c_municipality_volume_top15.png",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
