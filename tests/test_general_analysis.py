from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.analysis.general import (
    analyze_general,
    annual_summary,
    cardinality_table,
    data_quality_table,
    special_category_table,
    target_stability,
    write_analysis_tables,
)


def _synthetic_dataset() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "source_year": [2021, 2022, 2022, 2022],
            "target_grave": [True, False, False, False],
            "dia_semana": ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira"],
            "uf": ["SP", "SP", "MG", "MG"],
            "municipio": ["A", "A", "B", "B"],
            "causa_acidente": ["C1", "C1", "C2", "C2"],
            "tipo_acidente": ["T1", "T1", "T2", "T2"],
            "classificacao_acidente": [None, "Sem Vítimas", "Sem Vítimas", "Sem Vítimas"],
            "fase_dia": ["Pleno dia", "Pleno dia", "Anoitecer", "Anoitecer"],
            "sentido_via": ["Não Informado", "Crescente", "Crescente", "Decrescente"],
            "condicao_metereologica": ["Ignorado", "Sol", "Sol", "Chuva"],
            "tipo_pista": ["Dupla", "Dupla", "Simples", "Simples"],
            "tracado_via": ["Reta", "Reta", "Curva", "Curva"],
            "uso_solo": ["Sim", "Sim", "Não", "Não"],
            "regional": [None, "R1", "R1", "R2"],
            "delegacia": ["D1", "D1", "D2", "D2"],
            "uop": ["U1", "U1", "U2", "U2"],
        }
    )


def test_annual_summary_calculates_totals_and_classes() -> None:
    summary = annual_summary(_synthetic_dataset())

    assert summary.get_column("total_occurrences").to_list() == [1, 3]
    assert summary.get_column("severe_occurrences").to_list() == [1, 0]
    assert summary.get_column("non_severe_occurrences").to_list() == [0, 3]
    assert (
        summary.get_column("severe_occurrences") + summary.get_column("non_severe_occurrences")
    ).to_list() == summary.get_column("total_occurrences").to_list()


def test_annual_dataset_share_sums_to_one_hundred_percent() -> None:
    summary = annual_summary(_synthetic_dataset())

    assert summary.get_column("dataset_share_percent").sum() == pytest.approx(100.0)


def test_weighted_global_rate_is_not_simple_mean_of_annual_rates() -> None:
    stability = target_stability(annual_summary(_synthetic_dataset()))

    assert stability.simple_mean_annual_rate_percent == pytest.approx(50.0)
    assert stability.weighted_global_rate_percent == pytest.approx(25.0)
    assert stability.simple_mean_annual_rate_percent != stability.weighted_global_rate_percent


def test_first_year_change_is_not_applicable() -> None:
    changes = annual_summary(_synthetic_dataset()).get_column("occurrences_yoy_percent")

    assert changes[0] is None
    assert changes[1] == pytest.approx(200.0)


def test_annual_rate_range_is_in_percentage_points() -> None:
    stability = target_stability(annual_summary(_synthetic_dataset()))

    assert stability.minimum_annual_rate_percent == pytest.approx(0.0)
    assert stability.maximum_annual_rate_percent == pytest.approx(100.0)
    assert stability.range_percentage_points == pytest.approx(100.0)


def test_data_quality_calculates_nulls_and_distinct_values() -> None:
    quality = data_quality_table(_synthetic_dataset())
    classification = quality.filter(pl.col("column") == "classificacao_acidente").row(0, named=True)

    assert classification["null_count"] == 1
    assert classification["null_percent"] == pytest.approx(25.0)
    assert classification["distinct_non_null"] == 1


def test_cardinality_counts_non_null_distinct_values() -> None:
    cardinality = cardinality_table(_synthetic_dataset())
    municipality = cardinality.filter(pl.col("column") == "municipio").row(0, named=True)

    assert municipality["distinct_non_null"] == 2
    assert municipality["null_count"] == 0


def test_special_categories_are_counted_without_transformation() -> None:
    df = _synthetic_dataset()
    before = df.clone()
    special = special_category_table(df)

    not_informed = special.filter(
        (pl.col("column") == "sentido_via") & (pl.col("special_category") == "Não Informado")
    ).row(0, named=True)
    ignored_weather = special.filter(
        (pl.col("column") == "condicao_metereologica") & (pl.col("special_category") == "Ignorado")
    ).row(0, named=True)

    assert not_informed["count"] == 1
    assert ignored_weather["count"] == 1
    assert df.equals(before)


def test_analysis_pipeline_does_not_modify_input_dataframe() -> None:
    df = _synthetic_dataset()
    before = df.clone()

    analyze_general(df)

    assert df.equals(before)


def test_analysis_tables_are_written_to_requested_directory(tmp_path: Path) -> None:
    paths = write_analysis_tables(analyze_general(_synthetic_dataset()), tmp_path)

    assert {path.name for path in paths} == {
        "phase_2a_year_summary.csv",
        "phase_2a_data_quality.csv",
        "phase_2a_cardinality.csv",
        "phase_2a_special_categories.csv",
    }
    assert all(path.is_file() for path in paths)
