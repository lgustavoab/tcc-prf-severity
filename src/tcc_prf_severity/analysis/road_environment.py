from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl

from tcc_prf_severity.config import (
    FIGURES_DIR,
    INTERIM_MANIFEST_PATH,
    INTERIM_PARQUET_PATH,
    RAW_DIR,
    TABLES_DIR,
)
from tcc_prf_severity.data.interim import verify_interim_dataset

ROAD_TYPE_ORDER = ("Simples", "Dupla", "Múltipla")
LAND_USE_ORDER = ("Não", "Sim")
DIRECTION_ORDER = ("Crescente", "Decrescente", "Não Informado")
WEATHER_ORDER = (
    "Chuva",
    "Céu Claro",
    "Garoa/Chuvisco",
    "Granizo",
    "Ignorado",
    "Neve",
    "Nevoeiro/Neblina",
    "Nublado",
    "Sol",
    "Vento",
)
ROAD_LAYOUT_COMPONENTS = (
    "Aclive",
    "Curva",
    "Declive",
    "Desvio Temporário",
    "Em Obras",
    "Interseção de Vias",
    "Ponte",
    "Reta",
    "Retorno Regulamentado",
    "Rotatória",
    "Túnel",
    "Viaduto",
)
ROAD_LAYOUT_DELIMITER = ";"
MIN_RATE_HIGHLIGHT_OCCURRENCES = 500


@dataclass(frozen=True)
class RoadEnvironmentAnalysis:
    road_type_summary: pl.DataFrame
    road_type_by_year: pl.DataFrame
    land_use_summary: pl.DataFrame
    land_use_by_year: pl.DataFrame
    direction_summary: pl.DataFrame
    direction_by_year: pl.DataFrame
    weather_summary: pl.DataFrame
    weather_by_year: pl.DataFrame
    weather_rate_highlights: pl.DataFrame
    road_layout_component_summary: pl.DataFrame
    road_layout_component_by_year: pl.DataFrame
    road_layout_component_rate_highlights: pl.DataFrame
    road_layout_tokens: pl.DataFrame
    environment_stability: pl.DataFrame


@dataclass(frozen=True)
class RoadEnvironmentAnalysisRun:
    analysis: RoadEnvironmentAnalysis
    table_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]


def _require_columns(df: pl.DataFrame, columns: tuple[str, ...]) -> None:
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes para a Fase 2D: {missing}")


def _sort_by_order(df: pl.DataFrame, column: str, order: tuple[str, ...]) -> pl.DataFrame:
    unknown = sorted(set(df.get_column(column).unique().to_list()) - set(order))
    if unknown:
        raise ValueError(f"Categorias inesperadas em {column}: {unknown}")
    rank = {category: index for index, category in enumerate(order)}
    return (
        df.with_columns(
            pl.col(column).replace_strict(rank, return_dtype=pl.Int64).alias("_category_order")
        )
        .sort("_category_order")
        .drop("_category_order")
    )


def categorical_summary(
    df: pl.DataFrame, category_column: str, category_order: tuple[str, ...]
) -> pl.DataFrame:
    """Resume uma dimensão exclusiva de via/ambiente e reconcilia com o dataset."""
    _require_columns(df, (category_column, "target_grave"))
    if df.is_empty():
        raise ValueError("O dataset não pode estar vazio.")
    if df.get_column(category_column).null_count() > 0:
        raise ValueError(f"A dimensão {category_column} contém valores nulos.")

    summary = (
        df.group_by(category_column)
        .agg(
            pl.len().cast(pl.Int64).alias("total_occurrences"),
            pl.col("target_grave").sum().cast(pl.Int64).alias("severe_occurrences"),
        )
        .with_columns(
            (pl.col("total_occurrences") - pl.col("severe_occurrences")).alias(
                "non_severe_occurrences"
            )
        )
        .with_columns(
            (pl.col("severe_occurrences") / pl.col("total_occurrences") * 100)
            .round(6)
            .alias("severe_rate_percent"),
            (pl.col("total_occurrences") / pl.lit(df.height) * 100)
            .round(6)
            .alias("dataset_share_percent"),
        )
    )
    summary = _sort_by_order(summary, category_column, category_order)
    if int(summary.get_column("total_occurrences").sum()) != df.height:
        raise RuntimeError(f"O resumo de {category_column} não reconciliou com o dataset.")
    if not (
        summary.get_column("severe_occurrences") + summary.get_column("non_severe_occurrences")
    ).equals(summary.get_column("total_occurrences")):
        raise RuntimeError(f"As classes do resumo de {category_column} não reconciliaram.")
    return summary


def categorical_by_year(
    df: pl.DataFrame, category_column: str, category_order: tuple[str, ...]
) -> pl.DataFrame:
    """Resume uma dimensão exclusiva por ano, inclusive participação dentro do ano."""
    _require_columns(df, ("source_year", category_column, "target_grave"))
    annual_totals = df.group_by("source_year").agg(pl.len().alias("_annual_total"))
    summary = (
        df.group_by("source_year", category_column)
        .agg(
            pl.len().cast(pl.Int64).alias("total_occurrences"),
            pl.col("target_grave").sum().cast(pl.Int64).alias("severe_occurrences"),
        )
        .with_columns(
            (pl.col("total_occurrences") - pl.col("severe_occurrences")).alias(
                "non_severe_occurrences"
            )
        )
        .join(annual_totals, on="source_year")
        .with_columns(
            (pl.col("severe_occurrences") / pl.col("total_occurrences") * 100)
            .round(6)
            .alias("severe_rate_percent"),
            (pl.col("total_occurrences") / pl.col("_annual_total") * 100)
            .round(6)
            .alias("year_share_percent"),
        )
        .drop("_annual_total")
    )
    rank = {category: index for index, category in enumerate(category_order)}
    unknown = sorted(set(summary.get_column(category_column).unique().to_list()) - set(rank))
    if unknown:
        raise ValueError(f"Categorias inesperadas em {category_column}: {unknown}")
    summary = (
        summary.with_columns(
            pl.col(category_column)
            .replace_strict(rank, return_dtype=pl.Int64)
            .alias("_category_order")
        )
        .sort("source_year", "_category_order")
        .drop("_category_order")
    )
    if int(summary.get_column("total_occurrences").sum()) != df.height:
        raise RuntimeError(f"O resumo anual de {category_column} não reconciliou.")
    return summary


def extract_road_layout_components(df: pl.DataFrame) -> pl.DataFrame:
    """Explode `tracado_via` por ponto e vírgula e valida os componentes conhecidos."""
    _require_columns(df, ("tracado_via", "source_year", "target_grave"))
    exploded = (
        df.with_row_index("_occurrence_index")
        .select(
            "_occurrence_index",
            "source_year",
            "target_grave",
            pl.col("tracado_via").str.split(ROAD_LAYOUT_DELIMITER).alias("road_layout_component"),
        )
        .explode("road_layout_component", empty_as_null=True)
        .with_columns(pl.col("road_layout_component").str.strip_chars())
        .unique(
            subset=("_occurrence_index", "road_layout_component"),
            maintain_order=True,
        )
    )
    found = set(exploded.get_column("road_layout_component").unique().to_list())
    unknown = sorted(found - set(ROAD_LAYOUT_COMPONENTS))
    if unknown:
        raise ValueError(f"Componentes desconhecidos em tracado_via: {unknown}")
    return exploded


def road_layout_component_summary(df: pl.DataFrame) -> pl.DataFrame:
    """Resume componentes não exclusivos de traçado sem exigir soma igual ao dataset."""
    components = extract_road_layout_components(df)
    summary = (
        components.group_by("road_layout_component")
        .agg(
            pl.len().cast(pl.Int64).alias("total_occurrences"),
            pl.col("target_grave").sum().cast(pl.Int64).alias("severe_occurrences"),
        )
        .with_columns(
            (pl.col("total_occurrences") - pl.col("severe_occurrences")).alias(
                "non_severe_occurrences"
            )
        )
        .with_columns(
            (pl.col("severe_occurrences") / pl.col("total_occurrences") * 100)
            .round(6)
            .alias("severe_rate_percent"),
            (pl.col("total_occurrences") / pl.lit(df.height) * 100)
            .round(6)
            .alias("occurrences_containing_component_percent"),
        )
        .sort("total_occurrences", descending=True)
    )
    if not (
        summary.get_column("severe_occurrences") + summary.get_column("non_severe_occurrences")
    ).equals(summary.get_column("total_occurrences")):
        raise RuntimeError("As classes do resumo de componentes não reconciliaram.")
    return summary


def road_layout_component_by_year(df: pl.DataFrame) -> pl.DataFrame:
    """Resume componentes não exclusivos por ano."""
    components = extract_road_layout_components(df)
    annual_totals = df.group_by("source_year").agg(pl.len().alias("_annual_total"))
    return (
        components.group_by("source_year", "road_layout_component")
        .agg(
            pl.len().cast(pl.Int64).alias("total_occurrences"),
            pl.col("target_grave").sum().cast(pl.Int64).alias("severe_occurrences"),
        )
        .with_columns(
            (pl.col("total_occurrences") - pl.col("severe_occurrences")).alias(
                "non_severe_occurrences"
            )
        )
        .join(annual_totals, on="source_year")
        .with_columns(
            (pl.col("severe_occurrences") / pl.col("total_occurrences") * 100)
            .round(6)
            .alias("severe_rate_percent"),
            (pl.col("total_occurrences") / pl.col("_annual_total") * 100)
            .round(6)
            .alias("occurrences_containing_component_percent"),
        )
        .drop("_annual_total")
        .sort("source_year", "total_occurrences", descending=[False, True])
    )


def rate_highlights(
    summary: pl.DataFrame,
    category_column: str,
    excluded_categories: tuple[str, ...] = (),
) -> pl.DataFrame:
    """Ordena taxas elegíveis, permitindo excluir categorias sem conteúdo substantivo."""
    eligible = summary.filter(pl.col("total_occurrences") >= MIN_RATE_HIGHLIGHT_OCCURRENCES)
    if excluded_categories:
        eligible = eligible.filter(~pl.col(category_column).is_in(excluded_categories))
    return eligible.sort(
        "severe_rate_percent", "total_occurrences", descending=[True, True]
    ).select(
        category_column,
        "total_occurrences",
        "severe_occurrences",
        "severe_rate_percent",
    )


def stability_table(
    dimensions: tuple[tuple[str, pl.DataFrame, str], ...],
) -> pl.DataFrame:
    """Calcula mínimo, máximo e amplitude anual por dimensão e categoria."""
    tables = []
    for dimension, table, category_column in dimensions:
        tables.append(
            table.group_by(category_column)
            .agg(
                pl.col("source_year").n_unique().cast(pl.Int64).alias("years_observed"),
                pl.col("severe_rate_percent").min().alias("minimum_annual_rate_percent"),
                pl.col("severe_rate_percent").max().alias("maximum_annual_rate_percent"),
            )
            .with_columns(
                (pl.col("maximum_annual_rate_percent") - pl.col("minimum_annual_rate_percent"))
                .round(6)
                .alias("range_percentage_points"),
                pl.lit(dimension).alias("dimension"),
                pl.col(category_column).alias("category"),
            )
            .select(
                "dimension",
                "category",
                "years_observed",
                "minimum_annual_rate_percent",
                "maximum_annual_rate_percent",
                "range_percentage_points",
            )
        )
    return pl.concat(tables)


def analyze_road_environment(df: pl.DataFrame) -> RoadEnvironmentAnalysis:
    """Executa os cálculos da Fase 2D sem modificar o DataFrame recebido."""
    road_type_summary = categorical_summary(df, "tipo_pista", ROAD_TYPE_ORDER)
    road_type_by_year = categorical_by_year(df, "tipo_pista", ROAD_TYPE_ORDER)
    land_use_summary = categorical_summary(df, "uso_solo", LAND_USE_ORDER)
    land_use_by_year = categorical_by_year(df, "uso_solo", LAND_USE_ORDER)
    direction_summary = categorical_summary(df, "sentido_via", DIRECTION_ORDER)
    direction_by_year = categorical_by_year(df, "sentido_via", DIRECTION_ORDER)
    weather_summary = categorical_summary(df, "condicao_metereologica", WEATHER_ORDER)
    weather_by_year = categorical_by_year(df, "condicao_metereologica", WEATHER_ORDER)
    component_summary = road_layout_component_summary(df)
    component_by_year = road_layout_component_by_year(df)
    tokens = component_summary.select(
        pl.col("road_layout_component").alias("token"),
        pl.lit(True).alias("expected_component"),
    ).sort("token")
    return RoadEnvironmentAnalysis(
        road_type_summary=road_type_summary,
        road_type_by_year=road_type_by_year,
        land_use_summary=land_use_summary,
        land_use_by_year=land_use_by_year,
        direction_summary=direction_summary,
        direction_by_year=direction_by_year,
        weather_summary=weather_summary,
        weather_by_year=weather_by_year,
        weather_rate_highlights=rate_highlights(
            weather_summary,
            "condicao_metereologica",
            excluded_categories=("Ignorado",),
        ),
        road_layout_component_summary=component_summary,
        road_layout_component_by_year=component_by_year,
        road_layout_component_rate_highlights=rate_highlights(
            component_summary, "road_layout_component"
        ),
        road_layout_tokens=tokens,
        environment_stability=stability_table(
            (
                ("road_type", road_type_by_year, "tipo_pista"),
                ("land_use", land_use_by_year, "uso_solo"),
                ("direction", direction_by_year, "sentido_via"),
                ("weather", weather_by_year, "condicao_metereologica"),
                ("road_layout_component", component_by_year, "road_layout_component"),
            )
        ),
    )


def write_road_environment_tables(
    analysis: RoadEnvironmentAnalysis, output_dir: Path
) -> tuple[Path, ...]:
    """Grava as tabelas científicas da Fase 2D em CSV UTF-8."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (analysis.road_type_summary, "phase_2d_road_type_summary.csv"),
        (analysis.road_type_by_year, "phase_2d_road_type_by_year.csv"),
        (analysis.land_use_summary, "phase_2d_land_use_summary.csv"),
        (analysis.land_use_by_year, "phase_2d_land_use_by_year.csv"),
        (analysis.direction_summary, "phase_2d_direction_summary.csv"),
        (analysis.direction_by_year, "phase_2d_direction_by_year.csv"),
        (analysis.weather_summary, "phase_2d_weather_summary.csv"),
        (analysis.weather_by_year, "phase_2d_weather_by_year.csv"),
        (
            analysis.weather_rate_highlights,
            "phase_2d_weather_severe_rate_n500.csv",
        ),
        (
            analysis.road_layout_component_summary,
            "phase_2d_road_layout_component_summary.csv",
        ),
        (
            analysis.road_layout_component_by_year,
            "phase_2d_road_layout_component_by_year.csv",
        ),
        (
            analysis.road_layout_component_rate_highlights,
            "phase_2d_road_layout_component_severe_rate_n500.csv",
        ),
        (analysis.road_layout_tokens, "phase_2d_road_layout_tokens.csv"),
        (analysis.environment_stability, "phase_2d_environment_stability.csv"),
    )
    for table, filename in outputs:
        table.write_csv(output_dir / filename)
    return tuple(output_dir / filename for _, filename in outputs)


def run_road_environment_analysis(
    parquet_path: Path = INTERIM_PARQUET_PATH,
    manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> RoadEnvironmentAnalysisRun:
    """Verifica o interim, executa a Fase 2D e publica tabelas e figuras."""
    verify_interim_dataset(raw_dir, parquet_path, manifest_path)
    analysis = analyze_road_environment(pl.read_parquet(parquet_path))
    table_paths = write_road_environment_tables(analysis, tables_dir)

    from tcc_prf_severity.analysis.road_environment_plots import (
        write_road_environment_figures,
    )

    figure_paths = write_road_environment_figures(analysis, figures_dir)
    return RoadEnvironmentAnalysisRun(analysis, table_paths, figure_paths)
