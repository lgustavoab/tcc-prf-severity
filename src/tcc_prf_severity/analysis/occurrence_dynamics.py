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

MIN_RATE_HIGHLIGHT_OCCURRENCES = 500
RANKING_SIZE = 15
MIN_STABILITY_YEARS = 3


@dataclass(frozen=True)
class OccurrenceDynamicsAnalysis:
    accident_type_summary: pl.DataFrame
    accident_type_by_year: pl.DataFrame
    accident_type_volume_top15: pl.DataFrame
    accident_type_severe_rate_top15: pl.DataFrame
    cause_summary: pl.DataFrame
    cause_by_year: pl.DataFrame
    cause_volume_top15: pl.DataFrame
    cause_severe_rate_top15: pl.DataFrame
    taxonomy_diagnostics: pl.DataFrame
    category_lifecycle: pl.DataFrame
    category_stability: pl.DataFrame
    people_distribution: pl.DataFrame
    people_summary_statistics: pl.DataFrame
    people_severe_rate: pl.DataFrame
    vehicle_distribution: pl.DataFrame
    vehicle_summary_statistics: pl.DataFrame
    vehicle_severe_rate: pl.DataFrame


@dataclass(frozen=True)
class OccurrenceDynamicsAnalysisRun:
    analysis: OccurrenceDynamicsAnalysis
    table_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]


def _require_columns(df: pl.DataFrame, columns: tuple[str, ...]) -> None:
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes para a Fase 2E: {missing}")


def categorical_summary(df: pl.DataFrame, category_column: str) -> pl.DataFrame:
    """Resume uma taxonomia preservada e reconcilia suas classes com o dataset."""
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
        .sort("total_occurrences", category_column, descending=[True, False])
    )
    if int(summary.get_column("total_occurrences").sum()) != df.height:
        raise RuntimeError(f"O resumo de {category_column} não reconciliou com o dataset.")
    if not (
        summary.get_column("severe_occurrences") + summary.get_column("non_severe_occurrences")
    ).equals(summary.get_column("total_occurrences")):
        raise RuntimeError(f"As classes do resumo de {category_column} não reconciliaram.")
    return summary


def categorical_by_year(df: pl.DataFrame, category_column: str) -> pl.DataFrame:
    """Resume volume e gravidade por ano e categoria sem harmonizar rótulos."""
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
        .sort("source_year", "total_occurrences", descending=[False, True])
    )
    if int(summary.get_column("total_occurrences").sum()) != df.height:
        raise RuntimeError(f"O resumo anual de {category_column} não reconciliou.")
    return summary


def volume_ranking(
    summary: pl.DataFrame, category_column: str, size: int = RANKING_SIZE
) -> pl.DataFrame:
    """Seleciona categorias com maior volume sem filtro de amostra."""
    return summary.head(size).select(
        category_column,
        "total_occurrences",
        "severe_occurrences",
        "severe_rate_percent",
    )


def severe_rate_ranking(
    summary: pl.DataFrame,
    category_column: str,
    minimum_occurrences: int = MIN_RATE_HIGHLIGHT_OCCURRENCES,
    size: int = RANKING_SIZE,
) -> pl.DataFrame:
    """Seleciona taxas somente entre categorias com amostra editorial mínima."""
    return (
        summary.filter(pl.col("total_occurrences") >= minimum_occurrences)
        .sort("severe_rate_percent", "total_occurrences", descending=[True, True])
        .head(size)
        .select(
            category_column,
            "total_occurrences",
            "severe_occurrences",
            "severe_rate_percent",
        )
    )


def category_lifecycle(df: pl.DataFrame, dimension: str, category_column: str) -> pl.DataFrame:
    """Registra primeiro/último ano, presença e volume de cada categoria original."""
    _require_columns(df, ("source_year", category_column))
    years = sorted(df.get_column("source_year").unique().to_list())
    first_period_year = years[0]
    last_period_year = years[-1]
    total_years = len(years)
    return (
        df.group_by(category_column)
        .agg(
            pl.col("source_year").min().cast(pl.Int64).alias("first_year"),
            pl.col("source_year").max().cast(pl.Int64).alias("last_year"),
            pl.col("source_year").n_unique().cast(pl.Int64).alias("years_observed"),
            pl.len().cast(pl.Int64).alias("total_occurrences"),
        )
        .with_columns(
            pl.lit(dimension).alias("dimension"),
            pl.col(category_column).alias("category"),
            (pl.col("years_observed") == total_years).alias("present_all_years"),
            (pl.col("years_observed") == 1).alias("exclusive_to_one_year"),
            (pl.col("first_year") > first_period_year).alias("appears_after_period_start"),
            (pl.col("last_year") < last_period_year).alias("disappears_before_period_end"),
        )
        .select(
            "dimension",
            "category",
            "first_year",
            "last_year",
            "years_observed",
            "total_occurrences",
            "present_all_years",
            "exclusive_to_one_year",
            "appears_after_period_start",
            "disappears_before_period_end",
        )
        .sort("dimension", "category")
    )


def taxonomy_diagnostics(
    df: pl.DataFrame, lifecycles: tuple[tuple[str, str, pl.DataFrame], ...]
) -> pl.DataFrame:
    """Quantifica cardinalidade anual e mudanças observadas nas taxonomias."""
    years = sorted(df.get_column("source_year").unique().to_list())
    rows: list[dict[str, int | str | None]] = []
    for dimension, category_column, lifecycle in lifecycles:
        annual = (
            df.group_by("source_year")
            .agg(pl.col(category_column).n_unique().alias("distinct_categories"))
            .sort("source_year")
        )
        for annual_row in annual.iter_rows(named=True):
            year = int(annual_row["source_year"])
            rows.append(
                {
                    "dimension": dimension,
                    "scope": "year",
                    "source_year": year,
                    "distinct_categories": int(annual_row["distinct_categories"]),
                    "union_categories": None,
                    "categories_present_all_years": None,
                    "categories_exclusive_one_year": None,
                    "categories_first_observed_in_year": lifecycle.filter(
                        pl.col("first_year") == year
                    ).height,
                    "categories_last_observed_in_year": lifecycle.filter(
                        pl.col("last_year") == year
                    ).height,
                    "categories_appearing_after_start": None,
                    "categories_disappearing_before_end": None,
                }
            )
        rows.append(
            {
                "dimension": dimension,
                "scope": "period",
                "source_year": None,
                "distinct_categories": None,
                "union_categories": lifecycle.height,
                "categories_present_all_years": lifecycle.filter(
                    pl.col("years_observed") == len(years)
                ).height,
                "categories_exclusive_one_year": lifecycle.filter(
                    pl.col("exclusive_to_one_year")
                ).height,
                "categories_first_observed_in_year": None,
                "categories_last_observed_in_year": None,
                "categories_appearing_after_start": lifecycle.filter(
                    pl.col("appears_after_period_start")
                ).height,
                "categories_disappearing_before_end": lifecycle.filter(
                    pl.col("disappears_before_period_end")
                ).height,
            }
        )
    return pl.DataFrame(rows).sort("dimension", "scope", "source_year", nulls_last=True)


def category_stability(
    by_year_tables: tuple[tuple[str, str, pl.DataFrame], ...],
    lifecycle: pl.DataFrame,
) -> pl.DataFrame:
    """Calcula amplitude apenas para categorias observadas em pelo menos três anos."""
    outputs: list[pl.DataFrame] = []
    observed_years: set[int] = set()
    for dimension, category_column, by_year in by_year_tables:
        observed_years.update(by_year.get_column("source_year").unique().to_list())
        normalized = by_year.select(
            pl.lit(dimension).alias("dimension"),
            pl.col(category_column).alias("category"),
            "source_year",
            "severe_rate_percent",
        )
        outputs.append(
            normalized.group_by("dimension", "category")
            .agg(
                pl.col("source_year").n_unique().cast(pl.Int64).alias("years_observed"),
                pl.col("severe_rate_percent").min().alias("minimum_annual_rate_percent"),
                pl.col("severe_rate_percent").max().alias("maximum_annual_rate_percent"),
            )
            .filter(pl.col("years_observed") >= MIN_STABILITY_YEARS)
            .with_columns(
                (pl.col("maximum_annual_rate_percent") - pl.col("minimum_annual_rate_percent"))
                .round(6)
                .alias("range_percentage_points")
            )
        )
    return (
        pl.concat(outputs)
        .join(
            lifecycle.select("dimension", "category", "total_occurrences"),
            on=("dimension", "category"),
            how="left",
        )
        .with_columns(
            (
                (pl.col("years_observed") == len(observed_years))
                & (pl.col("total_occurrences") >= MIN_RATE_HIGHLIGHT_OCCURRENCES)
            ).alias("priority_for_narrative")
        )
        .select(
            "dimension",
            "category",
            "years_observed",
            "total_occurrences",
            "minimum_annual_rate_percent",
            "maximum_annual_rate_percent",
            "range_percentage_points",
            "priority_for_narrative",
        )
        .sort("dimension", "category")
    )


def numeric_distribution(df: pl.DataFrame, column: str) -> pl.DataFrame:
    """Preserva a distribuição exata de uma contagem, sem bins ou remoção de cauda."""
    _require_columns(df, (column, "target_grave"))
    return (
        df.group_by(column)
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
        .sort(column)
    )


def numeric_summary_statistics(df: pl.DataFrame, column: str) -> pl.DataFrame:
    """Calcula estatísticas e diagnóstico simples da cauda superior original."""
    _require_columns(df, (column,))
    statistics = df.select(
        pl.lit(column).alias("variable"),
        pl.col(column).min().cast(pl.Float64).alias("minimum"),
        pl.col(column).quantile(0.25, interpolation="nearest").alias("p25"),
        pl.col(column).median().alias("median"),
        pl.col(column).mean().alias("mean"),
        pl.col(column).quantile(0.75, interpolation="nearest").alias("p75"),
        pl.col(column).quantile(0.90, interpolation="nearest").alias("p90"),
        pl.col(column).quantile(0.95, interpolation="nearest").alias("p95"),
        pl.col(column).quantile(0.99, interpolation="nearest").alias("p99"),
        pl.col(column).max().cast(pl.Float64).alias("maximum"),
    )
    p99 = statistics.get_column("p99").item()
    if p99 is None:
        raise ValueError(f"Não foi possível calcular o P99 de {column}.")
    return statistics.with_columns(
        pl.lit(df.filter(pl.col(column) > pl.lit(p99)).height)
        .cast(pl.Int64)
        .alias("occurrences_above_p99")
    )


def numeric_rate_highlights(distribution: pl.DataFrame, column: str) -> pl.DataFrame:
    """Mantém valores exatos com amostra suficiente, ordenados pelo valor observado."""
    return distribution.filter(
        pl.col("total_occurrences") >= MIN_RATE_HIGHLIGHT_OCCURRENCES
    ).select(
        column,
        "total_occurrences",
        "severe_occurrences",
        "severe_rate_percent",
    )


def analyze_occurrence_dynamics(df: pl.DataFrame) -> OccurrenceDynamicsAnalysis:
    """Executa a Fase 2E sem modificar o DataFrame recebido."""
    _require_columns(
        df,
        (
            "source_year",
            "target_grave",
            "tipo_acidente",
            "causa_acidente",
            "pessoas",
            "veiculos",
        ),
    )
    if df.is_empty():
        raise ValueError("O dataset não pode estar vazio.")

    accident_type_summary = categorical_summary(df, "tipo_acidente")
    accident_type_by_year = categorical_by_year(df, "tipo_acidente")
    cause_summary = categorical_summary(df, "causa_acidente")
    cause_by_year = categorical_by_year(df, "causa_acidente")
    type_lifecycle = category_lifecycle(df, "accident_type", "tipo_acidente")
    cause_lifecycle = category_lifecycle(df, "cause", "causa_acidente")
    lifecycle = pl.concat((type_lifecycle, cause_lifecycle))
    people_distribution = numeric_distribution(df, "pessoas")
    vehicle_distribution = numeric_distribution(df, "veiculos")

    return OccurrenceDynamicsAnalysis(
        accident_type_summary=accident_type_summary,
        accident_type_by_year=accident_type_by_year,
        accident_type_volume_top15=volume_ranking(accident_type_summary, "tipo_acidente"),
        accident_type_severe_rate_top15=severe_rate_ranking(accident_type_summary, "tipo_acidente"),
        cause_summary=cause_summary,
        cause_by_year=cause_by_year,
        cause_volume_top15=volume_ranking(cause_summary, "causa_acidente"),
        cause_severe_rate_top15=severe_rate_ranking(cause_summary, "causa_acidente"),
        taxonomy_diagnostics=taxonomy_diagnostics(
            df,
            (
                ("accident_type", "tipo_acidente", type_lifecycle),
                ("cause", "causa_acidente", cause_lifecycle),
            ),
        ),
        category_lifecycle=lifecycle,
        category_stability=category_stability(
            (
                ("accident_type", "tipo_acidente", accident_type_by_year),
                ("cause", "causa_acidente", cause_by_year),
            ),
            lifecycle,
        ),
        people_distribution=people_distribution,
        people_summary_statistics=numeric_summary_statistics(df, "pessoas"),
        people_severe_rate=numeric_rate_highlights(people_distribution, "pessoas"),
        vehicle_distribution=vehicle_distribution,
        vehicle_summary_statistics=numeric_summary_statistics(df, "veiculos"),
        vehicle_severe_rate=numeric_rate_highlights(vehicle_distribution, "veiculos"),
    )


def write_occurrence_dynamics_tables(
    analysis: OccurrenceDynamicsAnalysis, output_dir: Path
) -> tuple[Path, ...]:
    """Grava as tabelas científicas da Fase 2E em CSV UTF-8."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (analysis.accident_type_summary, "phase_2e_accident_type_summary.csv"),
        (analysis.accident_type_by_year, "phase_2e_accident_type_by_year.csv"),
        (analysis.accident_type_volume_top15, "phase_2e_accident_type_volume_top15.csv"),
        (
            analysis.accident_type_severe_rate_top15,
            "phase_2e_accident_type_severe_rate_top15_n500.csv",
        ),
        (analysis.cause_summary, "phase_2e_cause_summary.csv"),
        (analysis.cause_by_year, "phase_2e_cause_by_year.csv"),
        (analysis.cause_volume_top15, "phase_2e_cause_volume_top15.csv"),
        (
            analysis.cause_severe_rate_top15,
            "phase_2e_cause_severe_rate_top15_n500.csv",
        ),
        (analysis.taxonomy_diagnostics, "phase_2e_taxonomy_diagnostics.csv"),
        (analysis.category_lifecycle, "phase_2e_category_lifecycle.csv"),
        (analysis.category_stability, "phase_2e_category_stability.csv"),
        (analysis.people_distribution, "phase_2e_people_distribution.csv"),
        (
            analysis.people_summary_statistics,
            "phase_2e_people_summary_statistics.csv",
        ),
        (analysis.people_severe_rate, "phase_2e_people_severe_rate_n500.csv"),
        (analysis.vehicle_distribution, "phase_2e_vehicle_distribution.csv"),
        (
            analysis.vehicle_summary_statistics,
            "phase_2e_vehicle_summary_statistics.csv",
        ),
        (analysis.vehicle_severe_rate, "phase_2e_vehicle_severe_rate_n500.csv"),
    )
    for table, filename in outputs:
        table.write_csv(output_dir / filename)
    return tuple(output_dir / filename for _, filename in outputs)


def run_occurrence_dynamics_analysis(
    parquet_path: Path = INTERIM_PARQUET_PATH,
    manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> OccurrenceDynamicsAnalysisRun:
    """Verifica o interim, executa a Fase 2E e publica tabelas e figuras."""
    verify_interim_dataset(raw_dir, parquet_path, manifest_path)
    analysis = analyze_occurrence_dynamics(pl.read_parquet(parquet_path))
    table_paths = write_occurrence_dynamics_tables(analysis, tables_dir)

    from tcc_prf_severity.analysis.occurrence_dynamics_plots import (
        write_occurrence_dynamics_figures,
    )

    figure_paths = write_occurrence_dynamics_figures(analysis, figures_dir)
    return OccurrenceDynamicsAnalysisRun(analysis, table_paths, figure_paths)
