from __future__ import annotations

import polars as pl

from tcc_prf_severity.data.schemas import validate_standardized

DAY_TO_ISO_WEEKDAY = {
    "segunda-feira": 1,
    "terça-feira": 2,
    "quarta-feira": 3,
    "quinta-feira": 4,
    "sexta-feira": 5,
    "sábado": 6,
    "domingo": 7,
}


def _failure_count(df: pl.DataFrame, condition: pl.Expr) -> int:
    return int(df.select(condition.sum()).item())


def validate_invariants(df: pl.DataFrame) -> pl.DataFrame:
    """Valida relações bloqueantes entre colunas do dataset padronizado."""
    failures: list[str] = []

    duplicate_rows = _failure_count(df, pl.col("id").is_duplicated())
    if duplicate_rows:
        failures.append(f"IDs duplicados: {duplicate_rows} registro(s) envolvido(s)")

    inconsistent_injured = _failure_count(
        df, pl.col("feridos") != pl.col("feridos_leves") + pl.col("feridos_graves")
    )
    if inconsistent_injured:
        failures.append(
            f"feridos != feridos_leves + feridos_graves: {inconsistent_injured} registro(s)"
        )

    inconsistent_year = _failure_count(
        df, pl.col("data_inversa").dt.year() != pl.col("source_year")
    )
    if inconsistent_year:
        failures.append(f"ano de data_inversa != source_year: {inconsistent_year} registro(s)")

    expected_target = (pl.col("mortos") > 0) | (pl.col("feridos_graves") > 0)
    inconsistent_target = _failure_count(df, pl.col("target_grave") != expected_target)
    if inconsistent_target:
        failures.append(
            "target_grave != (mortos > 0) OR (feridos_graves > 0): "
            f"{inconsistent_target} registro(s)"
        )

    expected_weekday = pl.col("dia_semana").replace_strict(DAY_TO_ISO_WEEKDAY, return_dtype=pl.Int8)
    inconsistent_weekday = _failure_count(
        df, expected_weekday != pl.col("data_inversa").dt.weekday()
    )
    if inconsistent_weekday:
        failures.append(
            f"dia_semana incompatível com data_inversa: {inconsistent_weekday} registro(s)"
        )

    if failures:
        details = "\n- ".join(failures)
        raise ValueError(f"Invariantes do dataset violadas:\n- {details}")

    return df


def validate_dataset(df: pl.DataFrame) -> pl.DataFrame:
    """Aplica o schema Pandera e as invariantes entre colunas."""
    validated = validate_standardized(df)
    return validate_invariants(validated)
