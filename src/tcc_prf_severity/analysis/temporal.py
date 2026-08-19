from __future__ import annotations

import calendar
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

MONTH_ORDER = (
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)
WEEKDAY_ORDER = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)
DAY_PHASE_ORDER = ("Amanhecer", "Pleno dia", "Anoitecer", "Plena Noite")
WEEKDAY_GROUP_ORDER = ("Dias úteis", "Fim de semana")


@dataclass(frozen=True)
class TemporalAnalysis:
    month_summary: pl.DataFrame
    month_by_year: pl.DataFrame
    weekday_summary: pl.DataFrame
    weekday_by_year: pl.DataFrame
    weekday_group_summary: pl.DataFrame
    hour_summary: pl.DataFrame
    hour_by_year: pl.DataFrame
    day_phase_summary: pl.DataFrame
    day_phase_by_year: pl.DataFrame
    stability: pl.DataFrame


@dataclass(frozen=True)
class TemporalAnalysisRun:
    analysis: TemporalAnalysis
    table_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]


def _require_columns(df: pl.DataFrame, columns: tuple[str, ...]) -> None:
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes para a análise temporal: {missing}")


def _sort_by_order(df: pl.DataFrame, column: str, order: tuple[object, ...]) -> pl.DataFrame:
    rank = {value: index for index, value in enumerate(order)}
    unknown = set(df.get_column(column).unique().to_list()) - set(order)
    if unknown:
        raise ValueError(f"Categorias temporais inesperadas em {column}: {sorted(unknown)!r}")
    return (
        df.with_columns(
            pl.col(column).replace_strict(rank, return_dtype=pl.Int64).alias("_category_order")
        )
        .sort("_category_order")
        .drop("_category_order")
    )


def derive_temporal_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Deriva mês e hora somente em memória, sem modificar o DataFrame recebido."""
    _require_columns(
        df,
        ("data_inversa", "dia_semana", "horario", "fase_dia", "source_year", "target_grave"),
    )
    if df.is_empty():
        raise ValueError("O dataset não pode estar vazio.")

    month_names = {number: name for number, name in enumerate(MONTH_ORDER, start=1)}
    return df.with_columns(
        pl.col("data_inversa").dt.month().cast(pl.Int64).alias("month_number"),
        pl.col("horario").dt.hour().cast(pl.Int64).alias("hour"),
    ).with_columns(
        pl.col("month_number")
        .replace_strict(month_names, return_dtype=pl.String)
        .alias("month_name")
    )


def temporal_summary(
    df: pl.DataFrame,
    category_column: str,
    category_order: tuple[object, ...],
) -> pl.DataFrame:
    """Resume volume, classes, taxa e participação para uma dimensão temporal completa."""
    _require_columns(df, (category_column, "target_grave"))
    if df.get_column(category_column).null_count() > 0:
        raise ValueError(f"A dimensão temporal {category_column} contém valores nulos.")

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


def temporal_by_year(
    df: pl.DataFrame,
    category_column: str,
    category_order: tuple[object, ...],
) -> pl.DataFrame:
    """Resume uma dimensão temporal por ano para comparação descritiva."""
    _require_columns(df, ("source_year", category_column, "target_grave"))
    summary = (
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
    rank = {value: index for index, value in enumerate(category_order)}
    unknown = set(summary.get_column(category_column).unique().to_list()) - set(category_order)
    if unknown:
        raise ValueError(f"Categorias temporais inesperadas em {category_column}: {unknown!r}")
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


def _month_summary(df: pl.DataFrame) -> pl.DataFrame:
    summary = temporal_summary(df, "month_name", MONTH_ORDER)
    years = sorted(int(year) for year in df.get_column("source_year").unique().to_list())
    calendar_days = {
        month_name: sum(calendar.monthrange(year, month_number)[1] for year in years)
        for month_number, month_name in enumerate(MONTH_ORDER, start=1)
    }
    return summary.with_columns(
        pl.col("month_name")
        .replace_strict(calendar_days, return_dtype=pl.Int64)
        .alias("calendar_days")
    ).with_columns(
        (pl.col("total_occurrences") / pl.col("calendar_days"))
        .round(6)
        .alias("occurrences_per_calendar_day")
    )


def weekday_group_summary(df: pl.DataFrame) -> pl.DataFrame:
    """Compara descritivamente dias úteis e fim de semana."""
    grouped = df.with_columns(
        pl.when(pl.col("dia_semana").is_in(WEEKDAY_ORDER[:5]))
        .then(pl.lit(WEEKDAY_GROUP_ORDER[0]))
        .otherwise(pl.lit(WEEKDAY_GROUP_ORDER[1]))
        .alias("weekday_group")
    )
    return temporal_summary(grouped, "weekday_group", WEEKDAY_GROUP_ORDER).drop(
        "dataset_share_percent", "non_severe_occurrences"
    )


def temporal_stability(
    dimensions: tuple[tuple[str, pl.DataFrame, str], ...],
) -> pl.DataFrame:
    """Calcula mínimo, máximo e amplitude da taxa anual por categoria."""
    tables = []
    for dimension, table, category_column in dimensions:
        tables.append(
            table.group_by(category_column)
            .agg(
                pl.col("severe_rate_percent").min().alias("minimum_annual_rate_percent"),
                pl.col("severe_rate_percent").max().alias("maximum_annual_rate_percent"),
                pl.col("source_year").n_unique().cast(pl.Int64).alias("years_observed"),
            )
            .with_columns(
                (pl.col("maximum_annual_rate_percent") - pl.col("minimum_annual_rate_percent"))
                .round(6)
                .alias("range_percentage_points"),
                pl.lit(dimension).alias("dimension"),
                pl.col(category_column).cast(pl.String).alias("category"),
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


def analyze_temporal(df: pl.DataFrame) -> TemporalAnalysis:
    """Executa os cálculos descritivos da Fase 2B sem modificar o DataFrame recebido."""
    temporal = derive_temporal_columns(df)
    month_by_year = temporal_by_year(temporal, "month_name", MONTH_ORDER)
    weekday_by_year = temporal_by_year(temporal, "dia_semana", WEEKDAY_ORDER)
    hour_by_year = temporal_by_year(temporal, "hour", tuple(range(24)))
    day_phase_by_year = temporal_by_year(temporal, "fase_dia", DAY_PHASE_ORDER)
    return TemporalAnalysis(
        month_summary=_month_summary(temporal),
        month_by_year=month_by_year,
        weekday_summary=temporal_summary(temporal, "dia_semana", WEEKDAY_ORDER),
        weekday_by_year=weekday_by_year,
        weekday_group_summary=weekday_group_summary(temporal),
        hour_summary=temporal_summary(temporal, "hour", tuple(range(24))),
        hour_by_year=hour_by_year,
        day_phase_summary=temporal_summary(temporal, "fase_dia", DAY_PHASE_ORDER),
        day_phase_by_year=day_phase_by_year,
        stability=temporal_stability(
            (
                ("month", month_by_year, "month_name"),
                ("weekday", weekday_by_year, "dia_semana"),
                ("hour", hour_by_year, "hour"),
                ("day_phase", day_phase_by_year, "fase_dia"),
            )
        ),
    )


def write_temporal_tables(analysis: TemporalAnalysis, output_dir: Path) -> tuple[Path, ...]:
    """Grava as tabelas científicas da Fase 2B em CSV UTF-8."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (analysis.month_summary, "phase_2b_month_summary.csv"),
        (analysis.month_by_year, "phase_2b_month_by_year.csv"),
        (analysis.weekday_summary, "phase_2b_weekday_summary.csv"),
        (analysis.weekday_by_year, "phase_2b_weekday_by_year.csv"),
        (analysis.weekday_group_summary, "phase_2b_weekday_group_summary.csv"),
        (analysis.hour_summary, "phase_2b_hour_summary.csv"),
        (analysis.hour_by_year, "phase_2b_hour_by_year.csv"),
        (analysis.day_phase_summary, "phase_2b_day_phase_summary.csv"),
        (analysis.day_phase_by_year, "phase_2b_day_phase_by_year.csv"),
        (analysis.stability, "phase_2b_temporal_stability.csv"),
    )
    for table, filename in outputs:
        table.write_csv(output_dir / filename)
    return tuple(output_dir / filename for _, filename in outputs)


def run_temporal_analysis(
    parquet_path: Path = INTERIM_PARQUET_PATH,
    manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> TemporalAnalysisRun:
    """Verifica o interim, executa a Fase 2B e publica tabelas e figuras."""
    verify_interim_dataset(raw_dir, parquet_path, manifest_path)
    analysis = analyze_temporal(pl.read_parquet(parquet_path))
    table_paths = write_temporal_tables(analysis, tables_dir)

    from tcc_prf_severity.analysis.temporal_plots import write_temporal_figures

    figure_paths = write_temporal_figures(analysis, figures_dir)
    return TemporalAnalysisRun(analysis, table_paths, figure_paths)
