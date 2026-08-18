from pathlib import Path

import polars as pl

from tcc_prf_severity.config import EXPECTED_COLUMNS, FLOAT_COLUMNS, INTEGER_COLUMNS


def read_raw_csv(path: Path, year: int) -> pl.DataFrame:
    """Lê um CSV oficial da PRF preservando os dados antes da tipagem."""
    df = pl.read_csv(
        path,
        separator=";",
        encoding="windows-1252",
        infer_schema=False,
        null_values=["", "NA", "N/A"],
        truncate_ragged_lines=False,
    )

    if tuple(df.columns) != EXPECTED_COLUMNS:
        missing = sorted(set(EXPECTED_COLUMNS) - set(df.columns))
        extra = sorted(set(df.columns) - set(EXPECTED_COLUMNS))
        raise ValueError(
            f"Schema inesperado em {path.name}. "
            f"Esperadas {len(EXPECTED_COLUMNS)} colunas; recebidas {len(df.columns)}. "
            f"Ausentes={missing}; extras={extra}."
        )

    return standardize_types(df, year=year)


def _decimal_string(column: str) -> pl.Expr:
    return pl.col(column).str.strip_chars().str.replace_all(",", ".")


def standardize_types(df: pl.DataFrame, year: int) -> pl.DataFrame:
    """Padroniza tipos sem imputar, excluir ou corrigir valores de negócio."""
    text_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in {*INTEGER_COLUMNS, *FLOAT_COLUMNS, "id", "br", "data_inversa", "horario"}
    ]

    return df.with_columns(
        [pl.col(column).str.strip_chars() for column in text_columns]
        + [
            pl.col("id").cast(pl.String),
            pl.col("data_inversa").str.strptime(pl.Date, "%Y-%m-%d", strict=True),
            pl.col("horario").str.strptime(pl.Time, "%H:%M:%S", strict=True),
            *[
                pl.col(column).str.strip_chars().cast(pl.Int64, strict=True)
                for column in INTEGER_COLUMNS
            ],
            *[_decimal_string(column).cast(pl.Float64, strict=False) for column in FLOAT_COLUMNS],
            pl.col("br").str.strip_chars().cast(pl.Int64, strict=False),
            pl.lit(year, dtype=pl.Int64).alias("source_year"),
        ]
    ).with_columns(
        ((pl.col("mortos") > 0) | (pl.col("feridos_graves") > 0)).alias("target_grave_provisorio")
    )


def load_year(path: Path, year: int) -> pl.DataFrame:
    return read_raw_csv(path, year)


def concatenate_years(frames: list[pl.DataFrame]) -> pl.DataFrame:
    if not frames:
        raise ValueError("Nenhum DataFrame foi informado para concatenação.")
    return pl.concat(frames, how="vertical_relaxed", rechunk=True)
