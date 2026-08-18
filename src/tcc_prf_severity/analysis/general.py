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

CATEGORICAL_COLUMNS = (
    "dia_semana",
    "uf",
    "municipio",
    "causa_acidente",
    "tipo_acidente",
    "classificacao_acidente",
    "fase_dia",
    "sentido_via",
    "condicao_metereologica",
    "tipo_pista",
    "tracado_via",
    "uso_solo",
    "regional",
    "delegacia",
    "uop",
)
SPECIAL_CATEGORY_COLUMNS = (
    "sentido_via",
    "condicao_metereologica",
    "classificacao_acidente",
    "regional",
    "delegacia",
    "uop",
)
SPECIAL_CATEGORIES = ("Ignorado", "Não Informado")


@dataclass(frozen=True)
class TargetStability:
    minimum_annual_rate_percent: float
    maximum_annual_rate_percent: float
    range_percentage_points: float
    simple_mean_annual_rate_percent: float
    weighted_global_rate_percent: float


@dataclass(frozen=True)
class GeneralAnalysis:
    annual_summary: pl.DataFrame
    stability: TargetStability
    data_quality: pl.DataFrame
    cardinality: pl.DataFrame
    special_categories: pl.DataFrame


@dataclass(frozen=True)
class GeneralAnalysisRun:
    analysis: GeneralAnalysis
    table_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]


def _require_columns(df: pl.DataFrame, columns: tuple[str, ...]) -> None:
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes para a análise: {missing}")


def _as_float(value: object, metric: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"Não foi possível calcular {metric}.")
    return float(value)


def annual_summary(df: pl.DataFrame) -> pl.DataFrame:
    """Resume volume e distribuição de target_grave por ano."""
    _require_columns(df, ("source_year", "target_grave"))
    if df.is_empty():
        raise ValueError("O dataset não pode estar vazio.")

    summary = (
        df.group_by("source_year")
        .agg(
            pl.len().cast(pl.Int64).alias("total_occurrences"),
            pl.col("target_grave").sum().cast(pl.Int64).alias("severe_occurrences"),
        )
        .sort("source_year")
        .with_columns(
            (pl.col("total_occurrences") - pl.col("severe_occurrences")).alias(
                "non_severe_occurrences"
            )
        )
        .with_columns(
            (pl.col("severe_occurrences") / pl.col("total_occurrences") * 100).alias(
                "severe_rate_percent"
            ),
            (pl.col("non_severe_occurrences") / pl.col("total_occurrences") * 100).alias(
                "non_severe_rate_percent"
            ),
            (pl.col("total_occurrences") / pl.col("total_occurrences").sum() * 100).alias(
                "dataset_share_percent"
            ),
            ((pl.col("total_occurrences") / pl.col("total_occurrences").shift(1) - 1) * 100).alias(
                "occurrences_yoy_percent"
            ),
        )
        .with_columns(
            pl.col(
                "severe_rate_percent",
                "non_severe_rate_percent",
                "dataset_share_percent",
                "occurrences_yoy_percent",
            ).round(6)
        )
    )

    if int(summary.get_column("total_occurrences").sum()) != df.height:
        raise RuntimeError("O resumo anual não reconciliou com o total de registros.")
    return summary


def target_stability(summary: pl.DataFrame) -> TargetStability:
    """Calcula medidas descritivas das taxas anuais e da taxa global ponderada."""
    _require_columns(
        summary,
        ("total_occurrences", "severe_occurrences", "severe_rate_percent"),
    )
    if summary.is_empty():
        raise ValueError("O resumo anual não pode estar vazio.")

    rates = summary.get_column("severe_rate_percent")
    minimum_value = rates.min()
    maximum_value = rates.max()
    mean_value = rates.mean()
    minimum = _as_float(minimum_value, "a menor taxa anual")
    maximum = _as_float(maximum_value, "a maior taxa anual")
    total = int(summary.get_column("total_occurrences").sum())
    graves = int(summary.get_column("severe_occurrences").sum())
    return TargetStability(
        minimum_annual_rate_percent=minimum,
        maximum_annual_rate_percent=maximum,
        range_percentage_points=maximum - minimum,
        simple_mean_annual_rate_percent=_as_float(mean_value, "a média anual simples"),
        weighted_global_rate_percent=graves / total * 100,
    )


def data_quality_table(df: pl.DataFrame) -> pl.DataFrame:
    """Resume dtype, nulidade e valores distintos não nulos de todas as colunas."""
    if df.is_empty():
        raise ValueError("O dataset não pode estar vazio.")

    null_counts = df.null_count().row(0)
    distinct_counts = df.select(
        [pl.col(column).drop_nulls().n_unique().alias(column) for column in df.columns]
    ).row(0)
    return pl.DataFrame(
        {
            "column": df.columns,
            "dtype": [str(dtype) for dtype in df.dtypes],
            "null_count": [int(value) for value in null_counts],
            "null_percent": [round(int(value) / df.height * 100, 6) for value in null_counts],
            "distinct_non_null": [int(value) for value in distinct_counts],
        }
    )


def cardinality_table(
    df: pl.DataFrame, columns: tuple[str, ...] = CATEGORICAL_COLUMNS
) -> pl.DataFrame:
    """Calcula cardinalidade não nula das variáveis categóricas selecionadas."""
    _require_columns(df, columns)
    return pl.DataFrame(
        {
            "column": list(columns),
            "distinct_non_null": [
                df.get_column(column).drop_nulls().n_unique() for column in columns
            ],
            "null_count": [df.get_column(column).null_count() for column in columns],
        }
    )


def special_category_table(
    df: pl.DataFrame,
    columns: tuple[str, ...] = SPECIAL_CATEGORY_COLUMNS,
    categories: tuple[str, ...] = SPECIAL_CATEGORIES,
) -> pl.DataFrame:
    """Conta categorias especiais sem transformar ou excluir valores."""
    _require_columns(df, columns)
    rows = []
    for column in columns:
        series = df.get_column(column)
        for category in categories:
            count = int((series == category).sum())
            rows.append(
                {
                    "column": column,
                    "special_category": category,
                    "count": count,
                    "percent_of_rows": round(count / df.height * 100, 6),
                }
            )
    return pl.DataFrame(rows)


def analyze_general(df: pl.DataFrame) -> GeneralAnalysis:
    """Executa os cálculos descritivos da Fase 2A sem modificar o DataFrame recebido."""
    summary = annual_summary(df)
    return GeneralAnalysis(
        annual_summary=summary,
        stability=target_stability(summary),
        data_quality=data_quality_table(df),
        cardinality=cardinality_table(df),
        special_categories=special_category_table(df),
    )


def write_analysis_tables(analysis: GeneralAnalysis, output_dir: Path) -> tuple[Path, ...]:
    """Grava as quatro tabelas científicas da Fase 2A em CSV UTF-8."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (analysis.annual_summary, output_dir / "phase_2a_year_summary.csv"),
        (analysis.data_quality, output_dir / "phase_2a_data_quality.csv"),
        (analysis.cardinality, output_dir / "phase_2a_cardinality.csv"),
        (analysis.special_categories, output_dir / "phase_2a_special_categories.csv"),
    )
    for table, path in outputs:
        table.write_csv(path)
    return tuple(path for _, path in outputs)


def run_general_analysis(
    parquet_path: Path = INTERIM_PARQUET_PATH,
    manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> GeneralAnalysisRun:
    """Verifica o interim, executa a Fase 2A e publica suas tabelas e figuras."""
    verify_interim_dataset(raw_dir, parquet_path, manifest_path)
    df = pl.read_parquet(parquet_path)
    analysis = analyze_general(df)
    table_paths = write_analysis_tables(analysis, tables_dir)

    from tcc_prf_severity.analysis.plots import write_general_figures

    figure_paths = write_general_figures(analysis.annual_summary, figures_dir)
    return GeneralAnalysisRun(
        analysis=analysis,
        table_paths=table_paths,
        figure_paths=figure_paths,
    )
