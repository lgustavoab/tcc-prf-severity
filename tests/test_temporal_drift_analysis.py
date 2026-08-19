from datetime import date, time
from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.analysis.temporal_drift import (
    CATEGORICAL_VARIABLES,
    EXCLUDED_VARIABLES,
    analyze_temporal_drift,
    annual_cardinality_table,
    apply_numeric_bins,
    build_drift_inventory,
    calendar_coverage,
    categorical_drift_summary,
    development_quantile_bin_edges,
    horario_coverage,
    multilabel_drift_summary,
    numeric_drift_summary,
    numeric_statistics,
    total_variation_distance,
    unseen_categories_table,
    write_temporal_drift_tables,
)
from tcc_prf_severity.analysis.temporal_drift_plots import write_temporal_drift_figures

DRIFT_VARIABLES = (
    "data_inversa",
    "month_name",
    "dia_semana",
    "horario",
    "hour",
    "fase_dia",
    "uf",
    "br",
    "km",
    "municipio",
    "latitude",
    "longitude",
    "sentido_via",
    "condicao_metereologica",
    "tipo_pista",
    "uso_solo",
    "tracado_via",
    "tracado_via_components",
    "tipo_acidente",
    "causa_acidente",
    "pessoas",
    "veiculos",
)


def _eligibility_matrix() -> pl.DataFrame:
    rows = [
        {
            "variable": variable,
            "modeling_eligibility_status": (
                "requer_decisao_metodologica"
                if variable in ("tipo_acidente", "causa_acidente", "pessoas", "veiculos")
                else "candidata_com_cautela"
                if variable
                in (
                    "municipio",
                    "latitude",
                    "longitude",
                    "tracado_via",
                    "tracado_via_components",
                )
                else "candidata"
            ),
            "requires_temporal_drift_check": True,
        }
        for variable in DRIFT_VARIABLES
    ]
    rows.extend(
        {
            "variable": variable,
            "modeling_eligibility_status": "excluir_por_leakage",
            "requires_temporal_drift_check": False,
        }
        for variable in EXCLUDED_VARIABLES
    )
    return pl.DataFrame(rows)


def _synthetic_dataset() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for year in range(2021, 2025):
        for index in range(4):
            rows.append(
                {
                    "source_year": year,
                    "target_grave": index == 0,
                    "data_inversa": date(year, index + 1, index + 1),
                    "dia_semana": "segunda-feira" if index < 3 else "terça-feira",
                    "horario": time(8 + index, 15),
                    "fase_dia": "Pleno dia",
                    "uf": "SP" if index < 3 else "MG",
                    "br": 0 if index == 0 else 101,
                    "km": float(index * 10),
                    "municipio": "A" if index < 3 else "B",
                    "latitude": -20.0 - index,
                    "longitude": -45.0 - index,
                    "sentido_via": "Não Informado" if index == 0 else "Crescente",
                    "condicao_metereologica": "Ignorado" if index == 0 else "Sol",
                    "tipo_pista": "Simples" if index < 3 else "Dupla",
                    "uso_solo": "Sim" if index < 2 else "Não",
                    "tracado_via": "Reta;Reta;Curva" if index == 0 else "Reta",
                    "tipo_acidente": "Tipo antigo",
                    "causa_acidente": "Causa antiga",
                    "pessoas": index + 1,
                    "veiculos": 1 if index < 3 else 2,
                }
            )
    for index in range(4):
        rows.append(
            {
                "source_year": 2025,
                "target_grave": index == 0,
                "data_inversa": date(2025, index + 1, index + 1),
                "dia_semana": "quarta-feira" if index == 0 else "segunda-feira",
                "horario": time(8 + index, 15),
                "fase_dia": "Plena Noite" if index == 0 else "Pleno dia",
                "uf": "RJ" if index == 0 else "SP",
                "br": 0 if index == 0 else 101,
                "km": float(100 + index * 10),
                "municipio": "C" if index == 0 else "A",
                "latitude": -30.0 - index,
                "longitude": -55.0 - index,
                "sentido_via": "Decrescente" if index == 0 else "Crescente",
                "condicao_metereologica": "Chuva" if index == 0 else "Sol",
                "tipo_pista": "Múltipla" if index == 0 else "Simples",
                "uso_solo": "Não",
                "tracado_via": "Ponte" if index == 0 else "Reta",
                "tipo_acidente": "Tipo novo" if index == 0 else "Tipo antigo",
                "causa_acidente": "Causa nova" if index == 0 else "Causa antiga",
                "pessoas": 10 if index == 0 else index + 1,
                "veiculos": 5 if index == 0 else 1,
            }
        )
    return pl.DataFrame(rows)


@pytest.fixture(scope="module")
def analysis():  # type: ignore[no-untyped-def]
    return analyze_temporal_drift(_synthetic_dataset(), _eligibility_matrix())


def test_tvd_identical_distributions_is_zero() -> None:
    assert total_variation_distance({"A": 3, "B": 1}, {"A": 6, "B": 2}) == 0.0


def test_tvd_disjoint_distributions_is_one() -> None:
    assert total_variation_distance({"A": 1}, {"B": 1}) == 1.0


def test_categorical_tvd_handles_categories_absent_on_either_side() -> None:
    table = categorical_drift_summary(_synthetic_dataset(), ("uf",))
    row = table.row(0, named=True)

    assert row["new_categories_2025"] == 1
    assert row["missing_categories_2025"] == 1
    assert row["tvd"] > 0


def test_unseen_category_and_share_are_reported() -> None:
    table = unseen_categories_table(_synthetic_dataset(), ("tipo_acidente",))
    row = table.row(0, named=True)

    assert row["category"] == "Tipo novo"
    assert row["occurrences_2025"] == 1
    assert row["share_2025_percent"] == 25.0
    assert row["first_year_observed"] == 2025


def test_largest_share_change_is_reported_in_percentage_points() -> None:
    row = categorical_drift_summary(_synthetic_dataset(), ("uf",)).row(0, named=True)

    assert row["largest_change_category"] == "MG"
    assert row["largest_absolute_share_change_percentage_points"] == 25.0


def test_annual_cardinality_records_each_year() -> None:
    dataset = _synthetic_dataset().with_columns(
        pl.col("data_inversa").dt.month().cast(pl.String).alias("month_name"),
        pl.col("horario").dt.hour().alias("hour"),
    )
    table = annual_cardinality_table(dataset, ("uf",))

    assert table.filter(pl.col("variable") == "uf").height == 5
    assert (
        table.filter((pl.col("variable") == "uf") & (pl.col("source_year") == 2025))
        .get_column("distinct_values")
        .item()
        == 2
    )


def test_numeric_bins_are_derived_only_from_development() -> None:
    development = pl.Series([0.0, 1.0, 2.0, 3.0])
    edges = development_quantile_bin_edges(development)

    assert edges[0] == -float("inf")
    assert edges[-1] == float("inf")
    assert 1000.0 not in edges


def test_same_numeric_bins_are_applied_to_2025_extremes() -> None:
    edges = development_quantile_bin_edges(pl.Series([0.0, 1.0, 2.0, 3.0]))
    counts = apply_numeric_bins(pl.Series([-100.0, 1000.0]), edges)

    assert sum(counts.values()) == 2
    assert counts[0] == 1
    assert counts[len(edges) - 2] == 1


def test_repeated_quantiles_reduce_bins_deterministically() -> None:
    first = development_quantile_bin_edges(pl.Series([1.0, 1.0, 1.0]))
    second = development_quantile_bin_edges(pl.Series([1.0, 1.0, 1.0]))

    assert first == second == (-float("inf"), 1.0, float("inf"))


def test_numeric_statistics_include_requested_quantiles() -> None:
    stats = numeric_statistics(pl.Series([1.0, 2.0, 3.0, 4.0]))

    assert stats["n"] == 4
    assert stats["median"] == 2.5
    assert stats["p95"] == pytest.approx(3.85)
    assert stats["maximum"] == 4.0


def test_people_and_vehicles_use_exact_discrete_distribution() -> None:
    summary = categorical_drift_summary(_synthetic_dataset(), ("pessoas", "veiculos"))
    numeric = numeric_drift_summary(_synthetic_dataset(), (), ("pessoas", "veiculos"))

    assert set(summary.get_column("audit_method")) == {"discrete_exact_tvd"}
    assert set(numeric.get_column("audit_method")) == {"discrete_exact_tvd"}
    assert numeric.get_column("development_internal_bin_boundaries").is_null().all()


def test_multilabel_components_are_deduplicated_and_do_not_receive_tvd() -> None:
    table, unseen = multilabel_drift_summary(_synthetic_dataset())
    straight = table.filter(pl.col("component") == "Reta").row(0, named=True)

    assert straight["development_occurrences"] == 16
    assert set(table.get_column("audit_method")) == {"multilabel_prevalence_shift"}
    assert "tvd" not in table.columns
    assert unseen.filter(pl.col("category") == "Ponte").height == 1


def test_calendar_coverage_checks_parseability_and_month_derivation() -> None:
    dataset = _synthetic_dataset().with_columns(
        pl.col("data_inversa")
        .dt.month()
        .replace_strict({1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril"})
        .alias("month_name")
    )
    table = calendar_coverage(dataset)

    assert table.get_column("parseable_occurrences").sum() == dataset.height
    assert table.get_column("derivation_consistent_occurrences").sum() == dataset.height


def test_horario_is_audited_through_hour() -> None:
    dataset = _synthetic_dataset().with_columns(pl.col("horario").dt.hour().alias("hour"))
    table = horario_coverage(dataset)

    assert table.get_column("parseable_occurrences").sum() == dataset.height
    assert table.get_column("derivation_consistent_occurrences").sum() == dataset.height


def test_inventory_matches_all_drift_true_and_excludes_blocked_variables() -> None:
    inventory = build_drift_inventory(_eligibility_matrix())

    assert inventory.height == len(DRIFT_VARIABLES)
    assert set(inventory.get_column("variable")) == set(DRIFT_VARIABLES)
    assert not (set(inventory.get_column("variable")) & set(EXCLUDED_VARIABLES))
    assert inventory.filter(pl.col("variable") == "horario").get_column("audit_method").item() == (
        "derived_hour_proxy"
    )


def test_analysis_does_not_modify_original_dataframe() -> None:
    dataset = _synthetic_dataset()
    before = dataset.clone()

    analyze_temporal_drift(dataset, _eligibility_matrix())

    assert dataset.equals(before)


def test_analysis_audits_every_scoped_variable(analysis) -> None:  # type: ignore[no-untyped-def]
    assert analysis.drift_inventory.height == len(DRIFT_VARIABLES)
    assert analysis.drift_decision_summary.height == len(DRIFT_VARIABLES)
    assert not analysis.drift_decision_summary.get_column("final_inclusion_decided").any()
    assert set(analysis.categorical_drift_summary.get_column("variable")) == set(
        CATEGORICAL_VARIABLES
    )


def test_tables_are_written_to_tmp_path(analysis, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    paths = write_temporal_drift_tables(analysis, tmp_path)

    assert len(paths) == 7
    assert {path.name for path in paths} == {
        "phase_3a_drift_inventory.csv",
        "phase_3a_categorical_drift_summary.csv",
        "phase_3a_numeric_drift_summary.csv",
        "phase_3a_unseen_categories_2025.csv",
        "phase_3a_annual_cardinality.csv",
        "phase_3a_multilabel_drift_summary.csv",
        "phase_3a_drift_decision_summary.csv",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)


def test_figures_are_written_to_tmp_path(analysis, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    paths = write_temporal_drift_figures(analysis, tmp_path)

    assert 2 <= len(paths) <= 3
    assert {path.name for path in paths} >= {
        "phase_3a_categorical_tvd.png",
        "phase_3a_numeric_binned_tvd.png",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
