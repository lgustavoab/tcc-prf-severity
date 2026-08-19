from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from tcc_prf_severity.analysis.general import analyze_general
from tcc_prf_severity.analysis.geographic import analyze_geographic
from tcc_prf_severity.analysis.occurrence_dynamics import (
    OccurrenceDynamicsAnalysis,
    analyze_occurrence_dynamics,
)
from tcc_prf_severity.analysis.road_environment import analyze_road_environment
from tcc_prf_severity.analysis.temporal import WEEKDAY_ORDER, analyze_temporal
from tcc_prf_severity.config import (
    FIGURES_DIR,
    INTERIM_MANIFEST_PATH,
    INTERIM_PARQUET_PATH,
    RAW_DIR,
    TABLES_DIR,
)
from tcc_prf_severity.data.interim import verify_interim_dataset

SCIENTIFIC_PRIORITIES = ("central", "secundário", "contextual", "qualidade/metodológico")
MODELING_ELIGIBILITY_STATUSES = (
    "candidata",
    "candidata_com_cautela",
    "excluir_por_leakage",
    "excluir_por_disponibilidade_pos_ocorrencia",
    "excluir_administrativa",
    "requer_decisao_metodologica",
)
MIN_SUBSTANTIVE_SAMPLE = 500

EXPECTED_MODELING_VARIABLES = (
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
    "tracado_via",
    "tracado_via_components",
    "uso_solo",
    "tipo_acidente",
    "causa_acidente",
    "pessoas",
    "veiculos",
    "regional",
    "delegacia",
    "uop",
    "mortos",
    "feridos_graves",
    "feridos_leves",
    "feridos",
    "ilesos",
    "ignorados",
    "classificacao_acidente",
)

EVIDENCE_DIMENSION_TO_MODELING_VARIABLE = {
    "month_name": "month_name",
    "hour": "hour",
    "fase_dia": "fase_dia",
    "uf": "uf",
    "tipo_pista": "tipo_pista",
    "uso_solo": "uso_solo",
    "condicao_metereologica": "condicao_metereologica",
    "tracado_via_component": "tracado_via_components",
    "tipo_acidente": "tipo_acidente",
    "causa_acidente": "causa_acidente",
    "pessoas": "pessoas",
    "veiculos": "veiculos",
}


@dataclass(frozen=True)
class SeverityAssociationsAnalysis:
    association_evidence_matrix: pl.DataFrame
    modeling_eligibility_matrix: pl.DataFrame
    core_findings: pl.DataFrame
    temporal_consistency_summary: pl.DataFrame


@dataclass(frozen=True)
class SeverityAssociationsAnalysisRun:
    analysis: SeverityAssociationsAnalysis
    table_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]


def absolute_difference_percentage_points(focal_rate: float, reference_rate: float) -> float:
    """Calcula a magnitude absoluta de um contraste em pontos percentuais."""
    return round(abs(focal_rate - reference_rate), 6)


def _required_float(value: object, label: str) -> float:
    if not isinstance(value, int | float):
        raise ValueError(f"Métrica numérica ausente ou inválida: {label}.")
    return float(value)


def validate_editorial_classifications(table: pl.DataFrame) -> None:
    """Rejeita prioridades editoriais não previstas, sem criar score matemático."""
    unknown = set(table.get_column("scientific_priority").unique().to_list()) - set(
        SCIENTIFIC_PRIORITIES
    )
    if unknown:
        raise ValueError(f"Classificações editoriais inválidas: {sorted(unknown)}")


def validate_modeling_statuses(table: pl.DataFrame) -> None:
    """Garante que a matriz conceitual use somente os status definidos."""
    unknown = set(table.get_column("modeling_eligibility_status").unique().to_list()) - set(
        MODELING_ELIGIBILITY_STATUSES
    )
    if unknown:
        raise ValueError(f"Status de elegibilidade inválidos: {sorted(unknown)}")


def _row(table: pl.DataFrame, category_column: str, category: object) -> dict[str, Any]:
    selected = table.filter(pl.col(category_column) == category)
    if selected.height != 1:
        raise ValueError(f"Categoria ausente ou duplicada em {category_column}: {category!r}")
    return selected.row(0, named=True)


def _rate_extreme(table: pl.DataFrame, *, maximum: bool) -> dict[str, Any]:
    return table.sort("severe_rate_percent", descending=maximum).row(0, named=True)


def _contains_category(table: pl.DataFrame, category_column: str, category: object) -> bool:
    return table.filter(pl.col(category_column) == category).height == 1


def _annual_rates(df: pl.DataFrame, category_column: str) -> pl.DataFrame:
    return (
        df.group_by("source_year", category_column)
        .agg(
            pl.len().cast(pl.Int64).alias("total_occurrences"),
            pl.col("target_grave").sum().cast(pl.Int64).alias("severe_occurrences"),
        )
        .with_columns(
            (pl.col("severe_occurrences") / pl.col("total_occurrences") * 100)
            .round(6)
            .alias("severe_rate_percent")
        )
    )


def _weekday_group_tables(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    grouped = df.with_columns(
        pl.when(pl.col("dia_semana").is_in(WEEKDAY_ORDER[:5]))
        .then(pl.lit("Dias úteis"))
        .otherwise(pl.lit("Fim de semana"))
        .alias("weekday_group")
    )
    summary = (
        grouped.group_by("weekday_group")
        .agg(
            pl.len().cast(pl.Int64).alias("total_occurrences"),
            pl.col("target_grave").sum().cast(pl.Int64).alias("severe_occurrences"),
        )
        .with_columns(
            (pl.col("severe_occurrences") / pl.col("total_occurrences") * 100)
            .round(6)
            .alias("severe_rate_percent")
        )
    )
    return summary, _annual_rates(grouped, "weekday_group")


def _comparison_evidence(
    *,
    dimension: str,
    category_column: str,
    summary: pl.DataFrame,
    annual: pl.DataFrame,
    focal_category: object,
    reference_category: object,
    priority: str,
    semantic_note: str,
    leakage_concern: str,
    interpretation: str,
    temporal_note: str | None = None,
) -> dict[str, object]:
    focal = _row(summary, category_column, focal_category)
    reference = _row(summary, category_column, reference_category)
    focal_annual = annual.filter(pl.col(category_column) == focal_category)
    rates = focal_annual.get_column("severe_rate_percent")
    minimum = _required_float(rates.min(), f"mínimo anual de {dimension}")
    maximum = _required_float(rates.max(), f"máximo anual de {dimension}")
    years_observed = focal_annual.get_column("source_year").n_unique()
    focal_total = int(focal["total_occurrences"])
    reference_total = int(reference["total_occurrences"])
    sample_flag = (
        "adequada_n_ge_500"
        if min(focal_total, reference_total) >= MIN_SUBSTANTIVE_SAMPLE
        else "amostra_pequena"
    )
    annual_range = round(maximum - minimum, 6)
    return {
        "dimension": dimension,
        "category_or_comparison": f"{focal_category} vs {reference_category}",
        "focal_category": str(focal_category),
        "total_occurrences": focal_total,
        "severe_rate_percent": float(focal["severe_rate_percent"]),
        "reference_category_or_rate": str(reference_category),
        "reference_total_occurrences": reference_total,
        "reference_rate_percent": float(reference["severe_rate_percent"]),
        "absolute_difference_percentage_points": absolute_difference_percentage_points(
            float(focal["severe_rate_percent"]), float(reference["severe_rate_percent"])
        ),
        "years_observed": years_observed,
        "annual_minimum_rate_percent": minimum,
        "annual_maximum_rate_percent": maximum,
        "annual_range_percentage_points": annual_range,
        "sample_size_flag": sample_flag,
        "temporal_consistency_note": temporal_note
        or f"Observada em {years_observed} anos; amplitude anual de {annual_range:.2f} p.p.",
        "semantic_quality_note": semantic_note,
        "leakage_concern": leakage_concern,
        "modeling_eligibility_status": None,
        "scientific_priority": priority,
        "scientific_interpretation": interpretation,
        "substantive_evidence": True,
    }


def _quality_evidence(
    *,
    dimension: str,
    category_column: str,
    summary: pl.DataFrame,
    annual: pl.DataFrame,
    category: object,
    semantic_note: str,
) -> dict[str, object]:
    focal = _row(summary, category_column, category)
    focal_annual = annual.filter(pl.col(category_column) == category)
    rates = focal_annual.get_column("severe_rate_percent")
    minimum = _required_float(rates.min(), f"mínimo anual de {dimension}")
    maximum = _required_float(rates.max(), f"máximo anual de {dimension}")
    annual_range = round(maximum - minimum, 6)
    return {
        "dimension": dimension,
        "category_or_comparison": f"{category} (categoria especial)",
        "focal_category": str(category),
        "total_occurrences": int(focal["total_occurrences"]),
        "severe_rate_percent": float(focal["severe_rate_percent"]),
        "reference_category_or_rate": None,
        "reference_total_occurrences": None,
        "reference_rate_percent": None,
        "absolute_difference_percentage_points": None,
        "years_observed": focal_annual.get_column("source_year").n_unique(),
        "annual_minimum_rate_percent": minimum,
        "annual_maximum_rate_percent": maximum,
        "annual_range_percentage_points": annual_range,
        "sample_size_flag": "qualidade_de_dados",
        "temporal_consistency_note": (
            "Preservada para monitoramento de qualidade; sem contraste substantivo."
        ),
        "semantic_quality_note": semantic_note,
        "leakage_concern": "Não aplicável como achado substantivo.",
        "modeling_eligibility_status": None,
        "scientific_priority": "qualidade/metodológico",
        "scientific_interpretation": "Métrica de qualidade, não evidência da dimensão.",
        "substantive_evidence": False,
    }


def _global_target_evidence(annual: pl.DataFrame) -> dict[str, object]:
    minimum = _required_float(
        annual.get_column("severe_rate_percent").min(), "mínimo anual do target"
    )
    maximum = _required_float(
        annual.get_column("severe_rate_percent").max(), "máximo anual do target"
    )
    annual_range = round(maximum - minimum, 6)
    return {
        "dimension": "target_global",
        "category_or_comparison": "maior taxa anual vs menor taxa anual",
        "focal_category": "maior taxa anual",
        "total_occurrences": int(annual.get_column("total_occurrences").sum()),
        "severe_rate_percent": maximum,
        "reference_category_or_rate": "menor taxa anual",
        "reference_total_occurrences": None,
        "reference_rate_percent": minimum,
        "absolute_difference_percentage_points": annual_range,
        "years_observed": annual.height,
        "annual_minimum_rate_percent": minimum,
        "annual_maximum_rate_percent": maximum,
        "annual_range_percentage_points": annual_range,
        "sample_size_flag": "dataset_completo",
        "temporal_consistency_note": (
            f"Taxa global anual observada em 5 anos; amplitude de {annual_range:.2f} p.p."
        ),
        "semantic_quality_note": "Contexto do target; não é feature explicativa.",
        "leakage_concern": "O target não pode ser usado como preditor.",
        "modeling_eligibility_status": None,
        "scientific_priority": "contextual",
        "scientific_interpretation": (
            "A prevalência anual do target teve baixa amplitude descritiva."
        ),
        "substantive_evidence": True,
    }


def _taxonomy_note(diagnostics: pl.DataFrame, dimension: str) -> str:
    period = diagnostics.filter(
        (pl.col("dimension") == dimension) & (pl.col("scope") == "period")
    ).row(0, named=True)
    return (
        f"Taxonomia variou: união de {period['union_categories']} categorias; "
        f"{period['categories_present_all_years']} presentes nos cinco anos."
    )


def build_modeling_eligibility_matrix(dynamics: OccurrenceDynamicsAnalysis) -> pl.DataFrame:
    """Classifica conceitualmente variáveis sem construir dados ou pipeline de ML."""
    no_direct_leakage = "Sem contaminação direta do target identificada nesta fase."
    rows: list[dict[str, object]] = []

    def add(
        variable: str,
        source: str,
        status: str,
        rationale: str,
        *,
        leakage: str = no_direct_leakage,
        timing: str = "Disponível no registro da ocorrência; confirmar momento operacional.",
        quality: str = "Sem observação adicional nesta fase.",
        drift: bool = True,
    ) -> None:
        rows.append(
            {
                "variable": variable,
                "source_or_derivation": source,
                "modeling_eligibility_status": status,
                "rationale": rationale,
                "leakage_concern": leakage,
                "availability_timing": timing,
                "taxonomy_or_quality_note": quality,
                "requires_temporal_drift_check": drift,
            }
        )

    for variable, source in (
        ("data_inversa", "interim"),
        ("month_name", "derivada de data_inversa"),
        ("dia_semana", "interim"),
        ("horario", "interim"),
        ("hour", "derivada de horario"),
        ("fase_dia", "interim"),
    ):
        add(variable, source, "candidata", "Dimensão temporal disponível e reproduzível.")

    for variable in ("uf", "br", "km"):
        add(variable, "interim", "candidata", "Contexto geográfico/rodoviário do registro.")
    for variable in ("municipio", "latitude", "longitude"):
        add(
            variable,
            "interim",
            "candidata_com_cautela",
            "Contexto geográfico com alta granularidade ou sensibilidade à generalização.",
        )

    for variable in (
        "fase_dia",
        "sentido_via",
        "condicao_metereologica",
        "tipo_pista",
        "uso_solo",
    ):
        if variable == "fase_dia":
            continue
        quality = (
            "Preservar Não Informado como qualidade, não evidência substantiva."
            if variable == "sentido_via"
            else "Preservar Ignorado como qualidade, não condição observada."
            if variable == "condicao_metereologica"
            else "Sem observação adicional nesta fase."
        )
        add(variable, "interim", "candidata", "Contexto de via ou ambiente.", quality=quality)
    add(
        "tracado_via",
        "interim",
        "candidata_com_cautela",
        "Campo multivalorado cuja representação futura ainda precisa ser decidida.",
        quality=(
            "Alta cardinalidade aparente pelas combinações; não tratar ingenuamente como "
            "1.214 categorias independentes."
        ),
    )
    add(
        "tracado_via_components",
        "derivada em memória de tracado_via",
        "candidata_com_cautela",
        "Componentes multivalorados exigem representação futura documentada.",
        quality="Contagens por componente não são mutuamente exclusivas.",
    )

    type_note = _taxonomy_note(dynamics.taxonomy_diagnostics, "accident_type")
    cause_note = _taxonomy_note(dynamics.taxonomy_diagnostics, "cause")
    for variable, note in (("tipo_acidente", type_note), ("causa_acidente", cause_note)):
        add(
            variable,
            "interim",
            "requer_decisao_metodologica",
            "Válida para EDA; uso preditivo depende de disponibilidade temporal.",
            leakage="Possível conhecimento durante ou após a ocorrência.",
            timing="Pode ser definida ou consolidada após a ocorrência.",
            quality=note,
        )
    add(
        "pessoas",
        "interim",
        "requer_decisao_metodologica",
        "Associação parcialmente mecânica com a definição do target no nível da ocorrência.",
        leakage="Mais pessoas oferecem mais oportunidades para ao menos um morto ou ferido grave.",
        timing="Pode ser consolidada durante ou após a ocorrência.",
        quality="Há divergências conhecidas na decomposição de pessoas.",
    )
    add(
        "veiculos",
        "interim",
        "requer_decisao_metodologica",
        "Válida para EDA; disponibilidade no momento preditivo precisa ser definida.",
        leakage="Possível conhecimento durante ou após a ocorrência.",
        timing="Pode ser consolidada durante ou após a ocorrência.",
    )

    for variable in ("regional", "delegacia", "uop"):
        add(
            variable,
            "interim",
            "excluir_administrativa",
            "Proxy administrativo excluído inicialmente da modelagem.",
            timing="Campo administrativo do registro.",
            drift=False,
        )

    for variable in (
        "mortos",
        "feridos_graves",
        "feridos_leves",
        "feridos",
        "ilesos",
        "ignorados",
        "classificacao_acidente",
    ):
        add(
            variable,
            "interim",
            "excluir_por_leakage",
            "Resultado/consequência da ocorrência ou contaminação direta do target.",
            leakage="Contaminação direta ou proxy imediato da definição de gravidade.",
            timing="Conhecida durante ou após a ocorrência.",
            drift=False,
        )

    matrix = pl.DataFrame(rows)
    validate_modeling_statuses(matrix)
    missing = sorted(set(EXPECTED_MODELING_VARIABLES) - set(matrix.get_column("variable")))
    if missing:
        raise RuntimeError(f"Variáveis ausentes da matriz de elegibilidade: {missing}")
    return matrix


def apply_canonical_modeling_eligibility(
    evidence: pl.DataFrame, eligibility: pl.DataFrame
) -> pl.DataFrame:
    """Aplica à evidência somente status vindos do inventário canônico de features."""
    status_by_variable = {
        str(row["variable"]): str(row["modeling_eligibility_status"])
        for row in eligibility.select("variable", "modeling_eligibility_status").iter_rows(
            named=True
        )
    }
    status_by_dimension = {
        dimension: status_by_variable[variable]
        for dimension, variable in EVIDENCE_DIMENSION_TO_MODELING_VARIABLE.items()
    }
    return evidence.with_columns(
        pl.col("dimension")
        .replace_strict(status_by_dimension, default=None, return_dtype=pl.String)
        .alias("modeling_eligibility_status")
    )


def build_association_evidence_matrix(
    df: pl.DataFrame,
) -> tuple[pl.DataFrame, OccurrenceDynamicsAnalysis]:
    """Recalcula e consolida evidências das Fases 2A-2E diretamente do interim."""
    general = analyze_general(df)
    temporal = analyze_temporal(df)
    geographic = analyze_geographic(df)
    road = analyze_road_environment(df)
    dynamics = analyze_occurrence_dynamics(df)
    rows: list[dict[str, object]] = [_global_target_evidence(general.annual_summary)]

    month_high = _rate_extreme(temporal.month_summary, maximum=True)["month_name"]
    month_low = _rate_extreme(temporal.month_summary, maximum=False)["month_name"]
    rows.append(
        _comparison_evidence(
            dimension="month_name",
            category_column="month_name",
            summary=temporal.month_summary,
            annual=temporal.month_by_year,
            focal_category=month_high,
            reference_category=month_low,
            priority="secundário",
            semantic_note="Mês derivado em memória; contraste descritivo sazonal.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Contraste entre maior e menor proporção mensal observada.",
        )
    )
    weekday_summary, weekday_annual = _weekday_group_tables(df)
    rows.append(
        _comparison_evidence(
            dimension="weekday_group",
            category_column="weekday_group",
            summary=weekday_summary,
            annual=weekday_annual,
            focal_category="Fim de semana",
            reference_category="Dias úteis",
            priority="central",
            semantic_note="Agrupamento calendário explícito de sábado/domingo versus demais dias.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Fim de semana apresentou proporção grave superior nos registros.",
        )
    )
    hour_high = _rate_extreme(temporal.hour_summary, maximum=True)["hour"]
    hour_low = _rate_extreme(temporal.hour_summary, maximum=False)["hour"]
    rows.append(
        _comparison_evidence(
            dimension="hour",
            category_column="hour",
            summary=temporal.hour_summary,
            annual=temporal.hour_by_year,
            focal_category=hour_high,
            reference_category=hour_low,
            priority="secundário",
            semantic_note="Hora derivada em memória do horário registrado.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Contraste entre horários de maior e menor proporção observada.",
        )
    )
    rows.append(
        _comparison_evidence(
            dimension="fase_dia",
            category_column="fase_dia",
            summary=temporal.day_phase_summary,
            annual=temporal.day_phase_by_year,
            focal_category="Plena Noite",
            reference_category="Pleno dia",
            priority="central",
            semantic_note="Categorias originais preservadas.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Plena Noite apresentou proporção grave superior de forma recorrente.",
        )
    )

    macro_high = _rate_extreme(geographic.macroregion_summary, maximum=True)["macroregion"]
    macro_low = _rate_extreme(geographic.macroregion_summary, maximum=False)["macroregion"]
    rows.append(
        _comparison_evidence(
            dimension="macroregion",
            category_column="macroregion",
            summary=geographic.macroregion_summary,
            annual=geographic.macroregion_by_year,
            focal_category=macro_high,
            reference_category=macro_low,
            priority="central",
            semantic_note="Macrorregião derivada de UF; sem denominador de exposição.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Heterogeneidade geográfica descritiva entre extremos observados.",
        )
    )
    uf_high = _rate_extreme(geographic.uf_summary, maximum=True)["uf"]
    uf_low = _rate_extreme(geographic.uf_summary, maximum=False)["uf"]
    rows.append(
        _comparison_evidence(
            dimension="uf",
            category_column="uf",
            summary=geographic.uf_summary,
            annual=geographic.uf_by_year,
            focal_category=uf_high,
            reference_category=uf_low,
            priority="contextual",
            semantic_note="Contexto estadual; não classifica segurança ou exposição.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Heterogeneidade estadual descritiva entre extremos observados.",
        )
    )

    for reference, priority in (("Dupla", "central"), ("Múltipla", "secundário")):
        rows.append(
            _comparison_evidence(
                dimension="tipo_pista",
                category_column="tipo_pista",
                summary=road.road_type_summary,
                annual=road.road_type_by_year,
                focal_category="Simples",
                reference_category=reference,
                priority=priority,
                semantic_note="Categorias originais da via; sem exposição rodoviária.",
                leakage_concern="Sem contaminação direta identificada.",
                interpretation="Pista Simples apresentou maior proporção grave no período.",
            )
        )
    rows.append(
        _comparison_evidence(
            dimension="uso_solo",
            category_column="uso_solo",
            summary=road.land_use_summary,
            annual=road.land_use_by_year,
            focal_category="Não",
            reference_category="Sim",
            priority="secundário",
            semantic_note="Campo da PRF; não reinterpretado automaticamente como rural/urbano.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Contraste descritivo entre as duas categorias registradas.",
        )
    )
    weather_focus = road.weather_rate_highlights.row(0, named=True)["condicao_metereologica"]
    weather_reference = road.weather_rate_highlights.tail(1).row(0, named=True)[
        "condicao_metereologica"
    ]
    rows.append(
        _comparison_evidence(
            dimension="condicao_metereologica",
            category_column="condicao_metereologica",
            summary=road.weather_summary,
            annual=road.weather_by_year,
            focal_category=weather_focus,
            reference_category=weather_reference,
            priority="secundário",
            semantic_note="Somente condições informadas com n≥500; Ignorado excluído do contraste.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Contraste meteorológico descritivo com controle editorial de amostra.",
        )
    )
    layout_focus = road.road_layout_component_rate_highlights.row(0, named=True)[
        "road_layout_component"
    ]
    layout_reference = road.road_layout_component_rate_highlights.tail(1).row(0, named=True)[
        "road_layout_component"
    ]
    rows.append(
        _comparison_evidence(
            dimension="tracado_via_component",
            category_column="road_layout_component",
            summary=road.road_layout_component_summary,
            annual=road.road_layout_component_by_year,
            focal_category=layout_focus,
            reference_category=layout_reference,
            priority="secundário",
            semantic_note="Componentes multivalorados e não mutuamente exclusivos; n≥500.",
            leakage_concern="Sem contaminação direta identificada.",
            interpretation="Contraste entre componentes elegíveis sem participação exclusiva.",
        )
    )

    type_focus = dynamics.accident_type_severe_rate_top15.row(0, named=True)["tipo_acidente"]
    type_reference = dynamics.accident_type_volume_top15.row(0, named=True)["tipo_acidente"]
    rows.append(
        _comparison_evidence(
            dimension="tipo_acidente",
            category_column="tipo_acidente",
            summary=dynamics.accident_type_summary,
            annual=dynamics.accident_type_by_year,
            focal_category=type_focus,
            reference_category=type_reference,
            priority="central",
            semantic_note=_taxonomy_note(dynamics.taxonomy_diagnostics, "accident_type"),
            leakage_concern="Possível conhecimento durante ou após a ocorrência.",
            interpretation=(
                "Tipo de alta taxa comparado ao tipo de maior volume; associação descritiva."
            ),
        )
    )
    frontal_collision = "Colisão frontal"
    if frontal_collision != type_focus and _contains_category(
        dynamics.accident_type_summary, "tipo_acidente", frontal_collision
    ):
        rows.append(
            _comparison_evidence(
                dimension="tipo_acidente",
                category_column="tipo_acidente",
                summary=dynamics.accident_type_summary,
                annual=dynamics.accident_type_by_year,
                focal_category=frontal_collision,
                reference_category=type_reference,
                priority="central",
                semantic_note=_taxonomy_note(dynamics.taxonomy_diagnostics, "accident_type"),
                leakage_concern="Possível conhecimento durante ou após a ocorrência.",
                interpretation=(
                    "Colisão frontal comparada ao tipo de maior volume; associação descritiva."
                ),
            )
        )
    cause_focus = dynamics.cause_severe_rate_top15.row(0, named=True)["causa_acidente"]
    cause_reference = dynamics.cause_volume_top15.row(0, named=True)["causa_acidente"]
    rows.append(
        _comparison_evidence(
            dimension="causa_acidente",
            category_column="causa_acidente",
            summary=dynamics.cause_summary,
            annual=dynamics.cause_by_year,
            focal_category=cause_focus,
            reference_category=cause_reference,
            priority="central",
            semantic_note=_taxonomy_note(dynamics.taxonomy_diagnostics, "cause"),
            leakage_concern="Causa registrada pode ser consolidada após a ocorrência.",
            interpretation="Causa registrada de alta taxa comparada à categoria de maior volume.",
        )
    )
    wrong_way = "Transitar na contramão"
    if wrong_way != cause_focus and _contains_category(
        dynamics.cause_summary, "causa_acidente", wrong_way
    ):
        rows.append(
            _comparison_evidence(
                dimension="causa_acidente",
                category_column="causa_acidente",
                summary=dynamics.cause_summary,
                annual=dynamics.cause_by_year,
                focal_category=wrong_way,
                reference_category=cause_reference,
                priority="central",
                semantic_note=_taxonomy_note(dynamics.taxonomy_diagnostics, "cause"),
                leakage_concern="Causa registrada pode ser consolidada após a ocorrência.",
                interpretation=(
                    "Contramão comparada à causa de maior volume; associação descritiva."
                ),
            )
        )
    people_focus = dynamics.people_severe_rate.get_column("pessoas").max()
    people_reference = dynamics.people_severe_rate.get_column("pessoas").min()
    rows.append(
        _comparison_evidence(
            dimension="pessoas",
            category_column="pessoas",
            summary=dynamics.people_distribution,
            annual=_annual_rates(df, "pessoas"),
            focal_category=people_focus,
            reference_category=people_reference,
            priority="secundário",
            semantic_note=(
                "Valores exatos com n≥500; associação parcialmente mecânica com o target."
            ),
            leakage_concern=(
                "Mais pessoas oferecem mais oportunidades de satisfazer o target da ocorrência."
            ),
            interpretation="Crescimento descritivo real, sem interpretação causal direta.",
        )
    )
    vehicle_focus = dynamics.vehicle_severe_rate.sort("severe_rate_percent", descending=True).row(
        0, named=True
    )["veiculos"]
    vehicle_reference = dynamics.vehicle_severe_rate.get_column("veiculos").min()
    rows.append(
        _comparison_evidence(
            dimension="veiculos",
            category_column="veiculos",
            summary=dynamics.vehicle_distribution,
            annual=_annual_rates(df, "veiculos"),
            focal_category=vehicle_focus,
            reference_category=vehicle_reference,
            priority="secundário",
            semantic_note="Valores exatos com n≥500; não se assume relação linear.",
            leakage_concern="Pode ser consolidada durante ou após a ocorrência.",
            interpretation="Contraste descritivo entre contagens elegíveis.",
        )
    )

    rows.extend(
        (
            _quality_evidence(
                dimension="condicao_metereologica_qualidade",
                category_column="condicao_metereologica",
                summary=road.weather_summary,
                annual=road.weather_by_year,
                category="Ignorado",
                semantic_note=(
                    "Ausência semântica; não representa condição meteorológica observada."
                ),
            ),
            _quality_evidence(
                dimension="sentido_via_qualidade",
                category_column="sentido_via",
                summary=road.direction_summary,
                annual=road.direction_by_year,
                category="Não Informado",
                semantic_note=(
                    "Categoria de informação ausente; não evidência substantiva de sentido."
                ),
            ),
            _quality_evidence(
                dimension="br_qualidade",
                category_column="br",
                summary=geographic.br_summary,
                annual=_annual_rates(df, "br"),
                category=0,
                semantic_note="BR não identificada; preservada como qualidade geográfica.",
            ),
        )
    )
    evidence = pl.DataFrame(rows, infer_schema_length=None)
    validate_editorial_classifications(evidence)
    return evidence, dynamics


def analyze_severity_associations(df: pl.DataFrame) -> SeverityAssociationsAnalysis:
    """Executa a síntese descritiva da Fase 2F sem modificar o DataFrame recebido."""
    if df.is_empty():
        raise ValueError("O dataset não pode estar vazio.")
    evidence, dynamics = build_association_evidence_matrix(df)
    eligibility = build_modeling_eligibility_matrix(dynamics)
    evidence = apply_canonical_modeling_eligibility(evidence, eligibility)
    core = evidence.filter(pl.col("scientific_priority") == "central").sort(
        "absolute_difference_percentage_points", descending=True, nulls_last=True
    )
    temporal = evidence.filter(
        pl.col("substantive_evidence") & pl.col("years_observed").is_not_null()
    ).select(
        "dimension",
        "category_or_comparison",
        "years_observed",
        "annual_minimum_rate_percent",
        "annual_maximum_rate_percent",
        "annual_range_percentage_points",
        "temporal_consistency_note",
        "scientific_priority",
    )
    return SeverityAssociationsAnalysis(evidence, eligibility, core, temporal)


def write_severity_association_tables(
    analysis: SeverityAssociationsAnalysis, output_dir: Path
) -> tuple[Path, ...]:
    """Grava as quatro matrizes sintéticas da Fase 2F."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (analysis.association_evidence_matrix, "phase_2f_association_evidence_matrix.csv"),
        (analysis.modeling_eligibility_matrix, "phase_2f_modeling_eligibility_matrix.csv"),
        (analysis.core_findings, "phase_2f_core_findings.csv"),
        (analysis.temporal_consistency_summary, "phase_2f_temporal_consistency_summary.csv"),
    )
    for table, filename in outputs:
        table.write_csv(output_dir / filename)
    return tuple(output_dir / filename for _, filename in outputs)


def run_severity_associations_analysis(
    parquet_path: Path = INTERIM_PARQUET_PATH,
    manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> SeverityAssociationsAnalysisRun:
    """Verifica o interim, executa a Fase 2F e publica sínteses tabulares e visuais."""
    verify_interim_dataset(raw_dir, parquet_path, manifest_path)
    analysis = analyze_severity_associations(pl.read_parquet(parquet_path))
    table_paths = write_severity_association_tables(analysis, tables_dir)

    from tcc_prf_severity.analysis.severity_associations_plots import (
        write_severity_association_figures,
    )

    figure_paths = write_severity_association_figures(analysis, figures_dir)
    return SeverityAssociationsAnalysisRun(analysis, table_paths, figure_paths)
