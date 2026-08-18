from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import polars as pl

from tcc_prf_severity.config import (
    EXPECTED_YEARS,
    INTERIM_MANIFEST_PATH,
    INTERIM_PARQUET_PATH,
    PROJECT_ROOT,
    RAW_DIR,
    RAW_FILE_TEMPLATE,
)
from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.data.ingest import concatenate_years, load_year
from tcc_prf_severity.data.validation import validate_dataset


@dataclass(frozen=True)
class InterimExpectations:
    years: tuple[int, ...] = EXPECTED_YEARS
    rows: int = 342_624
    columns: int = 32
    graves: int = 96_857


@dataclass(frozen=True)
class InterimBuildResult:
    parquet_path: Path
    manifest_path: Path
    rows: int
    columns: int
    years: tuple[int, ...]
    graves: int
    grave_rate: float
    sha256: str
    size_bytes: int


DEFAULT_INTERIM_EXPECTATIONS = InterimExpectations()


def _installed_version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def _logical_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _dataset_metrics(df: pl.DataFrame) -> tuple[tuple[int, ...], int, int]:
    years = tuple(sorted(int(year) for year in df.get_column("source_year").unique().to_list()))
    graves = int(df.select(pl.col("target_grave").sum()).item())
    unique_ids = int(df.select(pl.col("id").n_unique()).item())
    return years, graves, unique_ids


def _validate_expected_dataset(df: pl.DataFrame, expected: InterimExpectations) -> None:
    years, graves, unique_ids = _dataset_metrics(df)
    failures: list[str] = []

    if df.height != expected.rows:
        failures.append(f"linhas: esperado={expected.rows}, recebido={df.height}")
    if df.width != expected.columns:
        failures.append(f"colunas: esperado={expected.columns}, recebido={df.width}")
    if years != expected.years:
        failures.append(f"anos: esperado={list(expected.years)}, recebido={list(years)}")
    if graves != expected.graves:
        failures.append(f"graves: esperado={expected.graves}, recebido={graves}")
    if unique_ids != df.height:
        failures.append(f"IDs únicos: esperado={df.height}, recebido={unique_ids}")
    if not df.get_column("source_year").is_sorted():
        failures.append("source_year não está em ordem cronológica")

    if failures:
        details = "\n- ".join(failures)
        raise ValueError(f"Dataset intermediário fora do baseline esperado:\n- {details}")


def _validate_round_trip(source: pl.DataFrame, persisted: pl.DataFrame) -> None:
    validate_dataset(persisted)
    failures: list[str] = []

    if persisted.height != source.height:
        failures.append("a quantidade de linhas mudou após a persistência")
    if persisted.width != source.width:
        failures.append("a quantidade de colunas mudou após a persistência")
    if persisted.columns != source.columns:
        failures.append("a ordem ou os nomes das colunas mudaram após a persistência")
    if persisted.schema != source.schema:
        failures.append("os dtypes mudaram após a persistência")
    if not persisted.get_column("target_grave").equals(source.get_column("target_grave")):
        failures.append("target_grave mudou após a persistência")
    if not persisted.get_column("source_year").equals(source.get_column("source_year")):
        failures.append("source_year mudou após a persistência")
    if not persisted.get_column("id").equals(source.get_column("id")):
        failures.append("IDs ou sua ordem mudaram após a persistência")
    if not persisted.equals(source):
        failures.append("um ou mais valores mudaram após a persistência")

    if failures:
        details = "\n- ".join(failures)
        raise ValueError(f"Parquet não preservou o dataset consolidado:\n- {details}")


def _manifest(
    df: pl.DataFrame,
    parquet_path: Path,
    parquet_sha256: str,
    parquet_size: int,
    raw_sources: list[dict[str, Any]],
    project_root: Path,
) -> dict[str, Any]:
    years, graves, _ = _dataset_metrics(df)
    return {
        "artifact_name": parquet_path.name,
        "logical_path": _logical_path(parquet_path, project_root),
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "format": "parquet",
        "compression": "zstd",
        "rows": df.height,
        "columns": df.width,
        "years": list(years),
        "graves": graves,
        "grave_rate": round(graves / df.height, 6),
        "sha256": parquet_sha256,
        "size_bytes": parquet_size,
        "schema": {name: str(dtype) for name, dtype in df.schema.items()},
        "raw_sources": raw_sources,
        "versions": {
            "python": sys.version.split()[0],
            "polars": _installed_version("polars"),
            "pandera": _installed_version("pandera"),
            "project": _installed_version("tcc-prf-severity"),
        },
    }


def _backup_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.{uuid.uuid4().hex}.backup")


def _publish_artifact_pair(
    temporary_parquet: Path,
    parquet_path: Path,
    temporary_manifest: Path,
    manifest_path: Path,
) -> None:
    parquet_existed = parquet_path.exists()
    manifest_existed = manifest_path.exists()
    parquet_backup = _backup_path(parquet_path)
    manifest_backup = _backup_path(manifest_path)
    parquet_backed_up = False
    manifest_backed_up = False

    try:
        if parquet_existed:
            os.replace(parquet_path, parquet_backup)
            parquet_backed_up = True
        if manifest_existed:
            os.replace(manifest_path, manifest_backup)
            manifest_backed_up = True

        os.replace(temporary_parquet, parquet_path)
        os.replace(temporary_manifest, manifest_path)
    except BaseException as error:
        rollback_errors: list[str] = []

        try:
            if parquet_backed_up:
                os.replace(parquet_backup, parquet_path)
            elif not parquet_existed:
                parquet_path.unlink(missing_ok=True)
        except OSError as rollback_error:
            rollback_errors.append(f"Parquet: {rollback_error}")

        try:
            if manifest_backed_up:
                os.replace(manifest_backup, manifest_path)
            elif not manifest_existed:
                manifest_path.unlink(missing_ok=True)
        except OSError as rollback_error:
            rollback_errors.append(f"manifesto: {rollback_error}")

        for backup in (parquet_backup, manifest_backup):
            try:
                backup.unlink(missing_ok=True)
            except OSError as cleanup_error:
                rollback_errors.append(f"limpeza de {backup.name}: {cleanup_error}")

        if rollback_errors:
            error.add_note("Falhas adicionais durante o rollback: " + "; ".join(rollback_errors))
        raise

    parquet_backup.unlink(missing_ok=True)
    manifest_backup.unlink(missing_ok=True)


def build_interim_dataset(
    raw_dir: Path = RAW_DIR,
    parquet_path: Path = INTERIM_PARQUET_PATH,
    manifest_path: Path = INTERIM_MANIFEST_PATH,
    *,
    expected: InterimExpectations = DEFAULT_INTERIM_EXPECTATIONS,
    project_root: Path = PROJECT_ROOT,
) -> InterimBuildResult:
    """Constrói, valida e publica atomicamente o Parquet intermediário e seu manifesto."""
    years = tuple(sorted(expected.years))
    if years != expected.years or len(set(years)) != len(years):
        raise ValueError("Os anos esperados devem ser únicos e estar em ordem cronológica.")

    raw_sources: list[dict[str, Any]] = []
    source_hashes: dict[Path, str] = {}
    frames: list[pl.DataFrame] = []

    for year in years:
        source_path = raw_dir / RAW_FILE_TEMPLATE.format(year=year)
        if not source_path.is_file():
            raise FileNotFoundError(f"Arquivo RAW obrigatório não encontrado: {source_path}")

        source_hash = sha256_file(source_path)
        source_hashes[source_path] = source_hash
        raw_sources.append(
            {
                "year": year,
                "filename": source_path.name,
                "logical_path": _logical_path(source_path, project_root),
                "sha256": source_hash,
            }
        )

        frame = load_year(source_path, year)
        validate_dataset(frame)
        frames.append(frame)

    combined = concatenate_years(frames)
    validate_dataset(combined)
    _validate_expected_dataset(combined, expected)

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_parquet: Path | None = None
    temporary_manifest: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            dir=parquet_path.parent,
            prefix=f".{parquet_path.name}.",
            suffix=".parquet",
            delete=False,
        ) as temporary_file:
            temporary_parquet = Path(temporary_file.name)

        combined.write_parquet(temporary_parquet, compression="zstd")
        persisted = pl.read_parquet(temporary_parquet)
        _validate_round_trip(combined, persisted)
        _validate_expected_dataset(persisted, expected)

        current_hashes = {path: sha256_file(path) for path in source_hashes}
        if current_hashes != source_hashes:
            raise RuntimeError("Um ou mais arquivos RAW foram alterados durante a construção.")

        parquet_sha256 = sha256_file(temporary_parquet)
        parquet_size = temporary_parquet.stat().st_size
        manifest = _manifest(
            persisted,
            parquet_path,
            parquet_sha256,
            parquet_size,
            raw_sources,
            project_root,
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=manifest_path.parent,
            prefix=f".{manifest_path.name}.",
            suffix=".json",
            delete=False,
        ) as temporary_file:
            temporary_manifest = Path(temporary_file.name)
            json.dump(manifest, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")

        _publish_artifact_pair(
            temporary_parquet,
            parquet_path,
            temporary_manifest,
            manifest_path,
        )
        temporary_parquet = None
        temporary_manifest = None

        years_present, graves, _ = _dataset_metrics(persisted)
        return InterimBuildResult(
            parquet_path=parquet_path,
            manifest_path=manifest_path,
            rows=persisted.height,
            columns=persisted.width,
            years=years_present,
            graves=graves,
            grave_rate=graves / persisted.height,
            sha256=parquet_sha256,
            size_bytes=parquet_size,
        )
    finally:
        if temporary_parquet is not None:
            temporary_parquet.unlink(missing_ok=True)
        if temporary_manifest is not None:
            temporary_manifest.unlink(missing_ok=True)
