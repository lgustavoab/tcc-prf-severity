from datetime import date, time
from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.analysis.severity_associations import (
    EXPECTED_MODELING_VARIABLES,
    SeverityAssociationsAnalysis,
    absolute_difference_percentage_points,
    analyze_severity_associations,
    validate_editorial_classifications,
    write_severity_association_tables,
)
from tcc_prf_severity.analysis.severity_associations_plots import (
    write_severity_association_figures,
)


def _synthetic_dataset() -> pl.DataFrame:
    weekdays = (
        "segunda-feira",
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "sábado",
        "domingo",
        "segunda-feira",
        "terça-feira",
    )
    ufs = ("SP", "SP", "SP", "BA", "BA", "BA", "RS", "PA", "DF")
    rows: list[dict[str, object]] = []
    for year in range(2021, 2026):
        for index in range(9):
            severe = index >= 5
            rows.append(
                {
                    "data_inversa": date(year, index + 1, index + 1),
                    "dia_semana": weekdays[index],
                    "horario": time((index * 2) % 24, 30),
                    "fase_dia": "Plena Noite" if severe else "Pleno dia",
                    "source_year": year,
                    "target_grave": severe,
                    "uf": ufs[index],
                    "municipio": f"MUNICIPIO {index}",
                    "br": 0 if index == 4 else 100 + index,
                    "km": float(index * 10),
                    "latitude": -10.0 - index,
                    "longitude": -40.0 - index,
                    "tipo_pista": ("Simples" if severe else "Dupla" if index < 3 else "Múltipla"),
                    "uso_solo": "Não" if severe else "Sim",
                    "sentido_via": (
                        "Não Informado"
                        if index == 4
                        else "Crescente"
                        if index % 2
                        else "Decrescente"
                    ),
                    "condicao_metereologica": (
                        "Chuva" if severe else "Ignorado" if index == 4 else "Céu Claro"
                    ),
                    "tracado_via": "Curva" if severe else "Reta;Curva" if index == 4 else "Reta",
                    "tipo_acidente": (
                        "Atropelamento de Pedestre"
                        if index >= 7
                        else "Colisão frontal"
                        if index == 6
                        else "Colisão traseira"
                    ),
                    "causa_acidente": (
                        "Transitar na contramão"
                        if index >= 6
                        else "Reação tardia ou ineficiente do condutor"
                    ),
                    "pessoas": index + 1,
                    "veiculos": index % 3 + 1,
                    "classificacao_acidente": "Com Vítimas Fatais" if severe else "Sem Vítimas",
                    "regional": "Regional sintética",
                    "delegacia": "Delegacia sintética",
                    "uop": "UOP sintética",
                }
            )
    base = pl.DataFrame(rows)
    return pl.concat([base] * 500, rechunk=True)


@pytest.fixture(scope="module")
def analysis() -> SeverityAssociationsAnalysis:
    return analyze_severity_associations(_synthetic_dataset())


def _eligibility_row(analysis: SeverityAssociationsAnalysis, variable: str) -> dict[str, object]:
    return analysis.modeling_eligibility_matrix.filter(pl.col("variable") == variable).row(
        0, named=True
    )


def test_absolute_difference_is_calculated_in_percentage_points() -> None:
    assert absolute_difference_percentage_points(33.71, 23.35) == pytest.approx(10.36)


def test_evidence_matrix_contains_scoped_dimensions(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    dimensions = set(analysis.association_evidence_matrix.get_column("dimension"))

    assert {
        "month_name",
        "weekday_group",
        "hour",
        "fase_dia",
        "macroregion",
        "uf",
        "tipo_pista",
        "uso_solo",
        "condicao_metereologica",
        "tracado_via_component",
        "tipo_acidente",
        "causa_acidente",
        "pessoas",
        "veiculos",
    } <= dimensions


def test_reference_comparison_records_absolute_difference(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    comparison = analysis.association_evidence_matrix.filter(
        (pl.col("dimension") == "tipo_pista") & (pl.col("reference_category_or_rate") == "Dupla")
    ).row(0, named=True)

    assert comparison["focal_category"] == "Simples"
    assert comparison["absolute_difference_percentage_points"] == pytest.approx(100.0)


def test_temporal_consistency_is_consolidated(analysis: SeverityAssociationsAnalysis) -> None:
    night = analysis.temporal_consistency_summary.filter(pl.col("dimension") == "fase_dia").row(
        0, named=True
    )

    assert night["years_observed"] == 5
    assert night["annual_range_percentage_points"] == pytest.approx(0.0)


def test_editorial_classification_rejects_unknown_value() -> None:
    table = pl.DataFrame({"scientific_priority": ["central", "score_alto"]})

    with pytest.raises(ValueError, match="Classificações editoriais inválidas"):
        validate_editorial_classifications(table)


def test_leakage_variables_are_excluded(analysis: SeverityAssociationsAnalysis) -> None:
    for variable in (
        "mortos",
        "feridos_graves",
        "feridos_leves",
        "feridos",
        "ilesos",
        "ignorados",
        "classificacao_acidente",
    ):
        assert _eligibility_row(analysis, variable)["modeling_eligibility_status"] == (
            "excluir_por_leakage"
        )


def test_administrative_variables_are_excluded(analysis: SeverityAssociationsAnalysis) -> None:
    for variable in ("regional", "delegacia", "uop"):
        assert _eligibility_row(analysis, variable)["modeling_eligibility_status"] == (
            "excluir_administrativa"
        )


def test_type_and_cause_require_separate_methodological_decision(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    for variable in ("tipo_acidente", "causa_acidente"):
        assert _eligibility_row(analysis, variable)["modeling_eligibility_status"] == (
            "requer_decisao_metodologica"
        )


def test_people_receives_mechanical_target_warning(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    people = _eligibility_row(analysis, "pessoas")
    evidence = analysis.association_evidence_matrix.filter(pl.col("dimension") == "pessoas")

    assert people["modeling_eligibility_status"] == "requer_decisao_metodologica"
    assert "mecânica" in str(people["rationale"])
    assert "oportunidades" in str(people["leakage_concern"])
    assert evidence.height == 1
    assert evidence.get_column("scientific_priority").item() == "secundário"
    assert "pessoas" not in analysis.core_findings.get_column("dimension").to_list()


def test_road_layout_representations_are_candidates_with_caution(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    for variable in ("tracado_via", "tracado_via_components"):
        assert _eligibility_row(analysis, variable)["modeling_eligibility_status"] == (
            "candidata_com_cautela"
        )

    component_evidence = analysis.association_evidence_matrix.filter(
        pl.col("dimension") == "tracado_via_component"
    )
    assert component_evidence.get_column("modeling_eligibility_status").item() == (
        "candidata_com_cautela"
    )


def test_special_categories_are_quality_not_substantive(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    specials = analysis.association_evidence_matrix.filter(
        pl.col("dimension").is_in(
            [
                "condicao_metereologica_qualidade",
                "sentido_via_qualidade",
                "br_qualidade",
            ]
        )
    )

    assert specials.height == 3
    assert not specials.get_column("substantive_evidence").any()
    assert set(specials.get_column("scientific_priority")) == {"qualidade/metodológico"}
    assert specials.get_column("modeling_eligibility_status").is_null().all()


def test_analytical_dimensions_do_not_invent_modeling_eligibility(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    analytical = analysis.association_evidence_matrix.filter(
        pl.col("dimension").is_in(["weekday_group", "macroregion"])
    )

    assert analytical.height == 2
    assert analytical.get_column("modeling_eligibility_status").is_null().all()


def test_eligibility_status_counts_match_canonical_inventory(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    counts = {
        str(row["modeling_eligibility_status"]): int(row["len"])
        for row in analysis.modeling_eligibility_matrix.group_by("modeling_eligibility_status")
        .len()
        .iter_rows(named=True)
    }

    assert counts == {
        "candidata": 13,
        "candidata_com_cautela": 5,
        "excluir_administrativa": 3,
        "excluir_por_leakage": 7,
        "requer_decisao_metodologica": 4,
    }


def test_eligibility_matrix_contains_all_expected_variables(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    assert set(EXPECTED_MODELING_VARIABLES) <= set(
        analysis.modeling_eligibility_matrix.get_column("variable")
    )


def test_drift_inventory_marks_taxonomy_variables(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    for variable in ("tipo_acidente", "causa_acidente"):
        row = _eligibility_row(analysis, variable)
        assert row["requires_temporal_drift_check"] is True
        assert "Taxonomia" in str(row["taxonomy_or_quality_note"])


def test_high_cardinality_geography_does_not_enter_global_evidence(
    analysis: SeverityAssociationsAnalysis,
) -> None:
    dimensions = set(analysis.association_evidence_matrix.get_column("dimension"))

    assert "municipio" not in dimensions
    assert "br" not in dimensions
    assert "br_qualidade" in dimensions


def test_analysis_does_not_modify_input_dataframe() -> None:
    dataset = _synthetic_dataset()
    before = dataset.clone()

    analyze_severity_associations(dataset)

    assert dataset.equals(before)


def test_tables_are_written_to_requested_directory(
    analysis: SeverityAssociationsAnalysis, tmp_path: Path
) -> None:
    paths = write_severity_association_tables(analysis, tmp_path)

    assert {path.name for path in paths} == {
        "phase_2f_association_evidence_matrix.csv",
        "phase_2f_modeling_eligibility_matrix.csv",
        "phase_2f_core_findings.csv",
        "phase_2f_temporal_consistency_summary.csv",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)


def test_figure_is_written_to_requested_directory(
    analysis: SeverityAssociationsAnalysis, tmp_path: Path
) -> None:
    paths = write_severity_association_figures(analysis, tmp_path)

    assert [path.name for path in paths] == ["phase_2f_selected_severe_rate_comparisons.png"]
    assert paths[0].is_file() and paths[0].stat().st_size > 0
