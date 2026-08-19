from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.analysis.road_environment import (
    DIRECTION_ORDER,
    LAND_USE_ORDER,
    ROAD_TYPE_ORDER,
    WEATHER_ORDER,
    analyze_road_environment,
    categorical_summary,
    extract_road_layout_components,
    rate_highlights,
    road_layout_component_by_year,
    road_layout_component_summary,
    stability_table,
    write_road_environment_tables,
)
from tcc_prf_severity.analysis.road_environment_plots import (
    write_road_environment_figures,
)


def _synthetic_dataset() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "source_year": [2021, 2021, 2021, 2022, 2022, 2022],
            "target_grave": [True, False, True, False, True, False],
            "tipo_pista": ["Simples", "Simples", "Dupla", "Dupla", "Múltipla", "Múltipla"],
            "uso_solo": ["Não", "Sim", "Não", "Sim", "Não", "Sim"],
            "sentido_via": [
                "Crescente",
                "Decrescente",
                "Não Informado",
                "Crescente",
                "Decrescente",
                "Não Informado",
            ],
            "condicao_metereologica": [
                "Chuva",
                "Céu Claro",
                "Ignorado",
                "Chuva",
                "Neve",
                "Céu Claro",
            ],
            "tracado_via": [
                "Reta;Curva",
                "Reta",
                "Aclive;Reta",
                "Ponte",
                "Túnel",
                "Reta;Curva",
            ],
        }
    )


def _large_synthetic_dataset() -> pl.DataFrame:
    return pl.concat([_synthetic_dataset()] * 500, rechunk=True)


def test_road_type_summary_calculates_classes_and_rate() -> None:
    summary = categorical_summary(_synthetic_dataset(), "tipo_pista", ROAD_TYPE_ORDER)
    simple = summary.filter(pl.col("tipo_pista") == "Simples").row(0, named=True)

    assert simple["total_occurrences"] == 2
    assert simple["severe_occurrences"] == 1
    assert simple["non_severe_occurrences"] == 1
    assert simple["severe_rate_percent"] == 50.0


def test_land_use_summary_reconciles_dataset() -> None:
    summary = categorical_summary(_synthetic_dataset(), "uso_solo", LAND_USE_ORDER)

    assert summary.get_column("total_occurrences").to_list() == [3, 3]
    assert int(summary.get_column("total_occurrences").sum()) == 6


def test_direction_summary_preserves_categories() -> None:
    summary = categorical_summary(_synthetic_dataset(), "sentido_via", DIRECTION_ORDER)

    assert summary.get_column("sentido_via").to_list() == list(DIRECTION_ORDER)


def test_weather_summary_calculates_all_present_categories() -> None:
    summary = categorical_summary(_synthetic_dataset(), "condicao_metereologica", WEATHER_ORDER)

    assert set(summary.get_column("condicao_metereologica").to_list()) == {
        "Chuva",
        "Céu Claro",
        "Ignorado",
        "Neve",
    }
    assert int(summary.get_column("total_occurrences").sum()) == 6


def test_ignored_weather_and_not_informed_direction_are_preserved() -> None:
    analysis = analyze_road_environment(_synthetic_dataset())

    assert (
        analysis.weather_summary.filter(pl.col("condicao_metereologica") == "Ignorado")
        .get_column("total_occurrences")
        .item()
        == 1
    )
    assert (
        analysis.direction_summary.filter(pl.col("sentido_via") == "Não Informado")
        .get_column("total_occurrences")
        .item()
        == 2
    )


def test_ignored_weather_is_preserved_but_excluded_from_rate_highlights() -> None:
    analysis = analyze_road_environment(_large_synthetic_dataset())

    assert "Ignorado" in analysis.weather_summary.get_column("condicao_metereologica").to_list()
    assert (
        analysis.environment_stability.filter(
            (pl.col("dimension") == "weather") & (pl.col("category") == "Ignorado")
        ).height
        == 1
    )
    highlighted = analysis.weather_rate_highlights.get_column("condicao_metereologica").to_list()
    assert "Ignorado" not in highlighted
    assert "Chuva" in highlighted


def test_rate_highlight_applies_minimum_of_five_hundred() -> None:
    summary = pl.DataFrame(
        {
            "category": ["large", "small"],
            "total_occurrences": [500, 499],
            "severe_occurrences": [100, 499],
            "severe_rate_percent": [20.0, 100.0],
        }
    )

    highlights = rate_highlights(summary, "category")

    assert highlights.get_column("category").to_list() == ["large"]


def test_road_layout_is_split_on_semicolon() -> None:
    components = extract_road_layout_components(_synthetic_dataset())
    first = components.filter(pl.col("_occurrence_index") == 0)

    assert first.get_column("road_layout_component").to_list() == ["Reta", "Curva"]


def test_multivalued_occurrence_contributes_to_multiple_components() -> None:
    summary = road_layout_component_summary(_synthetic_dataset())

    assert (
        summary.filter(pl.col("road_layout_component") == "Reta")
        .get_column("total_occurrences")
        .item()
        == 4
    )
    assert (
        summary.filter(pl.col("road_layout_component") == "Curva")
        .get_column("total_occurrences")
        .item()
        == 2
    )


def test_component_counts_can_exceed_dataset_without_error() -> None:
    summary = road_layout_component_summary(_synthetic_dataset())

    assert int(summary.get_column("total_occurrences").sum()) > _synthetic_dataset().height


def test_unknown_road_layout_component_fails_clearly() -> None:
    df = _synthetic_dataset().with_columns(pl.lit("Reta;Desconhecido").alias("tracado_via"))

    with pytest.raises(ValueError, match=r"Componentes desconhecidos.*Desconhecido"):
        extract_road_layout_components(df)


def test_road_layout_component_by_year_calculates_each_year() -> None:
    summary = road_layout_component_by_year(_synthetic_dataset())
    straight = summary.filter(pl.col("road_layout_component") == "Reta")

    assert straight.get_column("source_year").to_list() == [2021, 2022]
    assert straight.get_column("total_occurrences").to_list() == [3, 1]


def test_stability_calculates_minimum_maximum_and_range() -> None:
    by_year = pl.DataFrame(
        {
            "source_year": [2021, 2022],
            "category": ["A", "A"],
            "severe_rate_percent": [20.0, 35.0],
        }
    )

    stability = stability_table((("test", by_year, "category"),)).row(0, named=True)

    assert stability["years_observed"] == 2
    assert stability["minimum_annual_rate_percent"] == 20.0
    assert stability["maximum_annual_rate_percent"] == 35.0
    assert stability["range_percentage_points"] == 15.0


def test_analysis_does_not_modify_input_dataframe() -> None:
    df = _synthetic_dataset()
    before = df.clone()

    analyze_road_environment(df)

    assert df.equals(before)


def test_road_environment_tables_are_written_to_tmp_path(tmp_path: Path) -> None:
    paths = write_road_environment_tables(analyze_road_environment(_synthetic_dataset()), tmp_path)

    assert len(paths) == 14
    assert {path.name for path in paths} >= {
        "phase_2d_road_type_summary.csv",
        "phase_2d_weather_summary.csv",
        "phase_2d_road_layout_component_by_year.csv",
        "phase_2d_environment_stability.csv",
    }
    assert all(path.is_file() for path in paths)


def test_road_environment_figures_are_written_to_tmp_path(tmp_path: Path) -> None:
    paths = write_road_environment_figures(
        analyze_road_environment(_large_synthetic_dataset()), tmp_path
    )

    assert len(paths) == 4
    assert {path.name for path in paths} == {
        "phase_2d_severe_rate_by_road_type.png",
        "phase_2d_severe_rate_by_land_use.png",
        "phase_2d_severe_rate_by_weather.png",
        "phase_2d_severe_rate_by_road_layout_component.png",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
