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

MACROREGION_ORDER = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
UF_TO_MACROREGION = {
    "AC": "Norte",
    "AP": "Norte",
    "AM": "Norte",
    "PA": "Norte",
    "RO": "Norte",
    "RR": "Norte",
    "TO": "Norte",
    "AL": "Nordeste",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "MA": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste",
    "GO": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste",
    "MG": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",
    "PR": "Sul",
    "RS": "Sul",
    "SC": "Sul",
}
MIN_RATE_RANKING_OCCURRENCES = 500
RANKING_THRESHOLDS = (100, 500, 1000)
RANKING_SIZE = 15


@dataclass(frozen=True)
class GeographicAnalysis:
    macroregion_summary: pl.DataFrame
    macroregion_by_year: pl.DataFrame
    macroregion_stability: pl.DataFrame
    uf_summary: pl.DataFrame
    uf_volume_top15: pl.DataFrame
    uf_by_year: pl.DataFrame
    uf_stability: pl.DataFrame
    br_summary: pl.DataFrame
    br_volume_top15: pl.DataFrame
    br_severe_rate_top15: pl.DataFrame
    municipality_summary: pl.DataFrame
    municipality_volume_top15: pl.DataFrame
    municipality_severe_rate_top15: pl.DataFrame
    ranking_threshold_diagnostics: pl.DataFrame
    coordinate_coverage: pl.DataFrame


@dataclass(frozen=True)
class GeographicAnalysisRun:
    analysis: GeographicAnalysis
    table_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]


def _require_columns(df: pl.DataFrame, columns: tuple[str, ...]) -> None:
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes para a análise geográfica: {missing}")


def derive_geographic_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Deriva macrorregião e rótulos geográficos somente em memória."""
    _require_columns(df, ("uf", "municipio", "br", "source_year", "target_grave"))
    if df.is_empty():
        raise ValueError("O dataset não pode estar vazio.")
    unknown = sorted(set(df.get_column("uf").unique().to_list()) - set(UF_TO_MACROREGION))
    if unknown:
        raise ValueError(f"UF sem mapeamento para macrorregião: {unknown}")

    return df.with_columns(
        pl.col("uf").replace_strict(UF_TO_MACROREGION, return_dtype=pl.String).alias("macroregion"),
        pl.concat_str("municipio", "uf", separator=" - ").alias("municipality_label"),
        pl.when(pl.col("br") == 0)
        .then(pl.lit("Não identificada (BR 0)"))
        .otherwise(pl.concat_str(pl.lit("BR "), pl.col("br")))
        .alias("br_label"),
    )


def geographic_summary(
    df: pl.DataFrame,
    category_columns: str | tuple[str, ...],
) -> pl.DataFrame:
    """Resume volume, classes, taxa e participação por categoria geográfica."""
    columns = (category_columns,) if isinstance(category_columns, str) else category_columns
    _require_columns(df, (*columns, "target_grave"))
    if any(df.get_column(column).null_count() for column in columns):
        raise ValueError(f"A dimensão geográfica {columns} contém valores nulos.")

    summary = (
        df.group_by(*columns)
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
    if int(summary.get_column("total_occurrences").sum()) != df.height:
        raise RuntimeError(f"O resumo geográfico de {columns} não reconciliou com o dataset.")
    if not (
        summary.get_column("severe_occurrences") + summary.get_column("non_severe_occurrences")
    ).equals(summary.get_column("total_occurrences")):
        raise RuntimeError(f"As classes do resumo geográfico de {columns} não reconciliaram.")
    return summary


def geographic_by_year(
    df: pl.DataFrame,
    category_column: str,
) -> pl.DataFrame:
    """Resume uma dimensão geográfica por ano."""
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
    if int(summary.get_column("total_occurrences").sum()) != df.height:
        raise RuntimeError(f"O resumo anual de {category_column} não reconciliou.")
    return summary


def _sort_macroregion(df: pl.DataFrame, *, by_year: bool = False) -> pl.DataFrame:
    rank = {name: index for index, name in enumerate(MACROREGION_ORDER)}
    sort_columns = ["source_year", "_macroregion_order"] if by_year else ["_macroregion_order"]
    return (
        df.with_columns(
            pl.col("macroregion")
            .replace_strict(rank, return_dtype=pl.Int64)
            .alias("_macroregion_order")
        )
        .sort(sort_columns)
        .drop("_macroregion_order")
    )


def category_stability(by_year: pl.DataFrame, category_column: str) -> pl.DataFrame:
    """Calcula mínimo, máximo e amplitude anual da taxa grave por categoria."""
    _require_columns(by_year, ("source_year", category_column, "severe_rate_percent"))
    return (
        by_year.group_by(category_column)
        .agg(
            pl.col("source_year").n_unique().cast(pl.Int64).alias("years_observed"),
            pl.col("severe_rate_percent").min().alias("minimum_annual_rate_percent"),
            pl.col("severe_rate_percent").max().alias("maximum_annual_rate_percent"),
        )
        .with_columns(
            (pl.col("maximum_annual_rate_percent") - pl.col("minimum_annual_rate_percent"))
            .round(6)
            .alias("range_percentage_points")
        )
        .sort(category_column)
    )


def uf_stability(uf_by_year: pl.DataFrame) -> pl.DataFrame:
    """Calcula mínimo, máximo e amplitude anual da taxa grave por UF."""
    return category_stability(uf_by_year, "uf")


def volume_ranking(
    summary: pl.DataFrame,
    category_columns: tuple[str, ...],
    *,
    exclude_br_zero: bool = False,
    size: int = RANKING_SIZE,
) -> pl.DataFrame:
    """Seleciona destaques por volume sem aplicar limiar de taxa."""
    ranked = summary.filter(pl.col("br") != 0) if exclude_br_zero else summary
    return (
        ranked.sort("total_occurrences", descending=True)
        .head(size)
        .select(
            *category_columns,
            "total_occurrences",
            "severe_occurrences",
            "severe_rate_percent",
        )
    )


def severe_rate_ranking(
    summary: pl.DataFrame,
    category_columns: tuple[str, ...],
    *,
    exclude_br_zero: bool = False,
    minimum_occurrences: int = MIN_RATE_RANKING_OCCURRENCES,
    size: int = RANKING_SIZE,
) -> pl.DataFrame:
    """Seleciona taxas apenas entre categorias com amostra editorial mínima."""
    eligible = summary.filter(pl.col("total_occurrences") >= minimum_occurrences)
    if exclude_br_zero:
        eligible = eligible.filter(pl.col("br") != 0)
    return (
        eligible.sort("severe_rate_percent", "total_occurrences", descending=[True, True])
        .head(size)
        .select(
            *category_columns,
            "total_occurrences",
            "severe_occurrences",
            "severe_rate_percent",
        )
    )


def threshold_diagnostics(
    br_summary: pl.DataFrame,
    municipality_summary: pl.DataFrame,
) -> pl.DataFrame:
    """Conta categorias elegíveis em três thresholds sem gerar rankings adicionais."""
    rows: list[dict[str, int | str]] = []
    for dimension, summary in (
        ("br_excluding_zero", br_summary.filter(pl.col("br") != 0)),
        ("municipality", municipality_summary),
    ):
        for threshold in RANKING_THRESHOLDS:
            rows.append(
                {
                    "dimension": dimension,
                    "minimum_occurrences": threshold,
                    "eligible_categories": summary.filter(
                        pl.col("total_occurrences") >= threshold
                    ).height,
                }
            )
    return pl.DataFrame(rows)


def coordinate_coverage(df: pl.DataFrame) -> pl.DataFrame:
    """Registra cobertura mínima das coordenadas sem realizar análise espacial."""
    _require_columns(df, ("latitude", "longitude"))
    distinct_pairs = df.select("latitude", "longitude").unique().height
    return pl.DataFrame(
        {
            "metric": (
                "latitude_null_count",
                "longitude_null_count",
                "distinct_coordinate_pairs",
            ),
            "value": (
                df.get_column("latitude").null_count(),
                df.get_column("longitude").null_count(),
                distinct_pairs,
            ),
        }
    )


def analyze_geographic(df: pl.DataFrame) -> GeographicAnalysis:
    """Executa a Fase 2C sem modificar o DataFrame recebido."""
    geographic = derive_geographic_columns(df)
    macroregion_summary = _sort_macroregion(geographic_summary(geographic, "macroregion"))
    macroregion_by_year = _sort_macroregion(
        geographic_by_year(geographic, "macroregion"), by_year=True
    )
    uf_summary = geographic_summary(geographic, "uf").sort("uf")
    uf_by_year = geographic_by_year(geographic, "uf").sort("source_year", "uf")
    br_summary = geographic_summary(geographic, ("br", "br_label")).sort("br")
    municipality_summary = geographic_summary(
        geographic, ("uf", "municipio", "municipality_label")
    ).sort("uf", "municipio")
    return GeographicAnalysis(
        macroregion_summary=macroregion_summary,
        macroregion_by_year=macroregion_by_year,
        macroregion_stability=_sort_macroregion(
            category_stability(macroregion_by_year, "macroregion")
        ),
        uf_summary=uf_summary,
        uf_volume_top15=volume_ranking(uf_summary, ("uf",)),
        uf_by_year=uf_by_year,
        uf_stability=uf_stability(uf_by_year),
        br_summary=br_summary,
        br_volume_top15=volume_ranking(br_summary, ("br", "br_label"), exclude_br_zero=True),
        br_severe_rate_top15=severe_rate_ranking(
            br_summary, ("br", "br_label"), exclude_br_zero=True
        ),
        municipality_summary=municipality_summary,
        municipality_volume_top15=volume_ranking(
            municipality_summary, ("uf", "municipio", "municipality_label")
        ),
        municipality_severe_rate_top15=severe_rate_ranking(
            municipality_summary, ("uf", "municipio", "municipality_label")
        ),
        ranking_threshold_diagnostics=threshold_diagnostics(br_summary, municipality_summary),
        coordinate_coverage=coordinate_coverage(geographic),
    )


def write_geographic_tables(analysis: GeographicAnalysis, output_dir: Path) -> tuple[Path, ...]:
    """Grava as tabelas científicas da Fase 2C em CSV UTF-8."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (analysis.macroregion_summary, "phase_2c_macroregion_summary.csv"),
        (analysis.macroregion_by_year, "phase_2c_macroregion_by_year.csv"),
        (analysis.macroregion_stability, "phase_2c_macroregion_stability.csv"),
        (analysis.uf_summary, "phase_2c_uf_summary.csv"),
        (analysis.uf_volume_top15, "phase_2c_uf_volume_top15.csv"),
        (analysis.uf_by_year, "phase_2c_uf_by_year.csv"),
        (analysis.uf_stability, "phase_2c_uf_stability.csv"),
        (analysis.br_summary, "phase_2c_br_summary.csv"),
        (analysis.br_volume_top15, "phase_2c_br_volume_top15.csv"),
        (analysis.br_severe_rate_top15, "phase_2c_br_severe_rate_top15_n500.csv"),
        (analysis.municipality_summary, "phase_2c_municipality_summary.csv"),
        (analysis.municipality_volume_top15, "phase_2c_municipality_volume_top15.csv"),
        (
            analysis.municipality_severe_rate_top15,
            "phase_2c_municipality_severe_rate_top15_n500.csv",
        ),
        (
            analysis.ranking_threshold_diagnostics,
            "phase_2c_ranking_threshold_diagnostics.csv",
        ),
        (analysis.coordinate_coverage, "phase_2c_coordinate_coverage.csv"),
    )
    for table, filename in outputs:
        table.write_csv(output_dir / filename)
    return tuple(output_dir / filename for _, filename in outputs)


def run_geographic_analysis(
    parquet_path: Path = INTERIM_PARQUET_PATH,
    manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> GeographicAnalysisRun:
    """Verifica o interim, executa a Fase 2C e publica tabelas e figuras."""
    verify_interim_dataset(raw_dir, parquet_path, manifest_path)
    analysis = analyze_geographic(pl.read_parquet(parquet_path))
    table_paths = write_geographic_tables(analysis, tables_dir)

    from tcc_prf_severity.analysis.geographic_plots import write_geographic_figures

    figure_paths = write_geographic_figures(analysis, figures_dir)
    return GeographicAnalysisRun(analysis, table_paths, figure_paths)
