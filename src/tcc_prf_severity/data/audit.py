from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import polars as pl

from tcc_prf_severity.config import AUDIT_DIR, EXPECTED_YEARS, RAW_FILE_TEMPLATE
from tcc_prf_severity.data.ingest import load_year
from tcc_prf_severity.data.validation import validate_dataset


@dataclass(frozen=True)
class YearAudit:
    year: int
    sha256: str
    rows: int
    columns: int
    duplicate_ids: int
    date_min: str
    date_max: str
    graves: int
    non_graves: int
    grave_rate: float
    feridos_identity_failures: int
    pessoas_identity_failures: int
    br_zero: int
    km_zero: int
    clima_ignorado: int
    sentido_nao_informado: int


def _scalar(df: pl.DataFrame, expression: pl.Expr) -> Any:
    return df.select(expression).item()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_year(df: pl.DataFrame, year: int, path: Path) -> YearAudit:
    graves = int(_scalar(df, pl.col("target_grave").sum()))
    rows = df.height

    feridos_identity_failures = int(
        _scalar(
            df,
            (pl.col("feridos") != pl.col("feridos_leves") + pl.col("feridos_graves")).sum(),
        )
    )

    pessoas_identity_failures = int(
        _scalar(
            df,
            (
                pl.col("pessoas")
                != pl.col("mortos")
                + pl.col("feridos_leves")
                + pl.col("feridos_graves")
                + pl.col("ilesos")
                + pl.col("ignorados")
            ).sum(),
        )
    )

    return YearAudit(
        year=year,
        sha256=sha256_file(path),
        rows=rows,
        columns=len(df.columns) - 2,  # remove source_year e target_grave
        duplicate_ids=int(df.select(pl.col("id").is_duplicated().sum()).item()),
        date_min=str(df.select(pl.col("data_inversa").min()).item()),
        date_max=str(df.select(pl.col("data_inversa").max()).item()),
        graves=graves,
        non_graves=rows - graves,
        grave_rate=round(graves / rows, 6),
        feridos_identity_failures=feridos_identity_failures,
        pessoas_identity_failures=pessoas_identity_failures,
        br_zero=int(df.select((pl.col("br") == 0).sum()).item()),
        km_zero=int(df.select((pl.col("km") == 0).sum()).item()),
        clima_ignorado=int(
            df.select((pl.col("condicao_metereologica") == "Ignorado").sum()).item()
        ),
        sentido_nao_informado=int(
            df.select((pl.col("sentido_via") == "Não Informado").sum()).item()
        ),
    )


def null_counts(df: pl.DataFrame) -> dict[str, int]:
    return {
        column: int(value)
        for column, value in zip(df.columns, df.null_count().row(0), strict=True)
        if value > 0
    }


def category_counts(df: pl.DataFrame) -> dict[str, int]:
    columns = (
        "dia_semana",
        "uf",
        "causa_acidente",
        "tipo_acidente",
        "classificacao_acidente",
        "fase_dia",
        "sentido_via",
        "condicao_metereologica",
        "tipo_pista",
        "tracado_via",
        "uso_solo",
    )
    return {column: int(df.select(pl.col(column).n_unique()).item()) for column in columns}


def tracado_tokens(df: pl.DataFrame) -> list[str]:
    tokens = (
        df.select(
            pl.col("tracado_via")
            .str.split(";")
            .explode(empty_as_null=True)
            .str.strip_chars()
            .alias("token")
        )
        .drop_nulls()
        .unique()
        .sort("token")
    )
    return tokens.get_column("token").to_list()


def run_audit(raw_dir: Path, output_dir: Path = AUDIT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    yearly_reports: list[YearAudit] = []
    detailed: dict[str, Any] = {}
    all_frames: list[pl.DataFrame] = []

    for year in EXPECTED_YEARS:
        path = raw_dir / RAW_FILE_TEMPLATE.format(year=year)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo obrigatório não encontrado: {path}")

        df = load_year(path, year)
        validate_dataset(df)
        all_frames.append(df)
        yearly_reports.append(audit_year(df, year, path))
        detailed[str(year)] = {
            "null_counts": null_counts(df),
            "category_cardinality": category_counts(df),
            "tracado_tokens": tracado_tokens(df),
        }

    combined = pl.concat(all_frames, how="vertical_relaxed", rechunk=True)
    validate_dataset(combined)

    summary = {
        "years": [asdict(report) for report in yearly_reports],
        "combined": {
            "rows": combined.height,
            "duplicate_ids": int(combined.select(pl.col("id").is_duplicated().sum()).item()),
            "graves": int(combined.select(pl.col("target_grave").sum()).item()),
            "grave_rate": round(float(combined.select(pl.col("target_grave").mean()).item()), 6),
            "feridos_identity_failures": sum(
                report.feridos_identity_failures for report in yearly_reports
            ),
            "pessoas_identity_failures": sum(
                report.pessoas_identity_failures for report in yearly_reports
            ),
            "br_zero": sum(report.br_zero for report in yearly_reports),
            "km_zero": sum(report.km_zero for report in yearly_reports),
        },
        "details": detailed,
        "notes": {
            "target": "target_grave = (mortos > 0) OU (feridos_graves > 0)",
            "raw_files_mutated": False,
            "modeling_started": False,
        },
    }

    json_path = output_dir / "audit_2021_2025.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    pl.DataFrame([asdict(report) for report in yearly_reports]).write_csv(
        output_dir / "audit_summary.csv"
    )

    return summary
