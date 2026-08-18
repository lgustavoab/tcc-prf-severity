import json
import os
from datetime import date
from pathlib import Path

import polars as pl
import pytest
from pandera.errors import SchemaErrors

from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.data.ingest import concatenate_years, load_year
from tcc_prf_severity.data.interim import (
    InterimBuildResult,
    InterimExpectations,
    build_interim_dataset,
)
from tcc_prf_severity.data.validation import validate_dataset

WEEKDAYS = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)


def _raw_row(year: int, *, invalid_uf: bool = False) -> pl.DataFrame:
    grave = year == 2023
    occurrence_date = date(year, 1, 1)
    return pl.DataFrame(
        {
            "id": [str(year)],
            "data_inversa": [occurrence_date.isoformat()],
            "dia_semana": [WEEKDAYS[occurrence_date.weekday()]],
            "horario": ["12:30:00"],
            "uf": ["XX" if invalid_uf else "SP"],
            "br": ["0" if year == 2021 else "116"],
            "km": ["0" if year == 2022 else "128,5"],
            "municipio": ["SAO PAULO"],
            "causa_acidente": ["Exemplo"],
            "tipo_acidente": ["Exemplo"],
            "classificacao_acidente": [None],
            "fase_dia": ["Pleno dia"],
            "sentido_via": ["Não Informado"],
            "condicao_metereologica": ["Ignorado"],
            "tipo_pista": ["Dupla"],
            "tracado_via": ["Reta;Declive"],
            "uso_solo": ["Sim"],
            "pessoas": ["1"],
            "mortos": ["0"],
            "feridos_leves": ["0"],
            "feridos_graves": ["1" if grave else "0"],
            "ilesos": ["0" if grave else "1"],
            "ignorados": ["0"],
            "feridos": ["1" if grave else "0"],
            "veiculos": ["1"],
            "latitude": ["-23,55"],
            "longitude": ["-46,63"],
            "regional": ["SPRF-SP"],
            "delegacia": ["DEL01-SP"],
            "uop": ["UOP01-SP"],
        }
    )


def _write_raw_sources(raw_dir: Path, *, invalid_year: int | None = None) -> list[Path]:
    raw_dir.mkdir(parents=True)
    paths = []
    for year in range(2021, 2026):
        path = raw_dir / f"datatran{year}.csv"
        csv = _raw_row(year, invalid_uf=year == invalid_year).write_csv(separator=";")
        path.write_bytes(csv.encode("windows-1252"))
        paths.append(path)
    return paths


def _build_paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    return (
        tmp_path / "data" / "raw",
        tmp_path / "data" / "interim" / "prf_accidents_2021_2025.parquet",
        tmp_path / "artifacts" / "interim" / "interim_manifest.json",
    )


@pytest.fixture
def expected() -> InterimExpectations:
    return InterimExpectations(rows=5, graves=1)


@pytest.fixture
def built_interim(
    tmp_path: Path, expected: InterimExpectations
) -> tuple[InterimBuildResult, Path, dict[Path, str]]:
    raw_dir, parquet_path, manifest_path = _build_paths(tmp_path)
    sources = _write_raw_sources(raw_dir)
    source_hashes = {path: sha256_file(path) for path in sources}
    result = build_interim_dataset(
        raw_dir,
        parquet_path,
        manifest_path,
        expected=expected,
        project_root=tmp_path,
    )
    return result, raw_dir, source_hashes


def test_builds_valid_parquet_preserving_shape_dtypes_and_target(
    built_interim: tuple[InterimBuildResult, Path, dict[Path, str]],
) -> None:
    result, raw_dir, _ = built_interim
    persisted = pl.read_parquet(result.parquet_path)
    source = concatenate_years(
        [load_year(raw_dir / f"datatran{year}.csv", year) for year in range(2021, 2026)]
    )

    assert result.rows == persisted.height == 5
    assert result.columns == persisted.width == 32
    assert persisted.columns == source.columns
    assert persisted.schema == source.schema
    assert persisted.get_column("target_grave").equals(source.get_column("target_grave"))
    assert result.graves == 1
    assert validate_dataset(persisted).equals(source)


def test_manifest_records_artifact_hash_and_sources(
    built_interim: tuple[InterimBuildResult, Path, dict[Path, str]],
) -> None:
    result, _, source_hashes = built_interim
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert manifest["sha256"] == result.sha256 == sha256_file(result.parquet_path)
    assert manifest["size_bytes"] == result.parquet_path.stat().st_size
    assert manifest["rows"] == 5
    assert manifest["columns"] == 32
    assert manifest["years"] == [2021, 2022, 2023, 2024, 2025]
    assert manifest["graves"] == 1
    assert manifest["format"] == "parquet"
    assert manifest["compression"] == "zstd"
    assert list(manifest["schema"]) == pl.read_parquet(result.parquet_path).columns
    assert [source["year"] for source in manifest["raw_sources"]] == manifest["years"]
    assert {source["sha256"] for source in manifest["raw_sources"]} == set(source_hashes.values())


def test_build_does_not_modify_raw_sources(
    built_interim: tuple[InterimBuildResult, Path, dict[Path, str]],
) -> None:
    _, _, source_hashes = built_interim

    assert {path: sha256_file(path) for path in source_hashes} == source_hashes


def test_contract_violation_prevents_final_artifacts(
    tmp_path: Path, expected: InterimExpectations
) -> None:
    raw_dir, parquet_path, manifest_path = _build_paths(tmp_path)
    _write_raw_sources(raw_dir, invalid_year=2023)

    with pytest.raises(SchemaErrors):
        build_interim_dataset(
            raw_dir,
            parquet_path,
            manifest_path,
            expected=expected,
            project_root=tmp_path,
        )

    assert not parquet_path.exists()
    assert not manifest_path.exists()


def test_post_write_validation_failure_preserves_previous_artifact(
    tmp_path: Path, expected: InterimExpectations, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_dir, parquet_path, manifest_path = _build_paths(tmp_path)
    _write_raw_sources(raw_dir)
    parquet_path.parent.mkdir(parents=True)
    previous_contents = b"previous artifact"
    parquet_path.write_bytes(previous_contents)

    def fail_readback(*args: object, **kwargs: object) -> pl.DataFrame:
        raise RuntimeError("falha simulada na releitura")

    monkeypatch.setattr("tcc_prf_severity.data.interim.pl.read_parquet", fail_readback)

    with pytest.raises(RuntimeError, match="falha simulada"):
        build_interim_dataset(
            raw_dir,
            parquet_path,
            manifest_path,
            expected=expected,
            project_root=tmp_path,
        )

    assert parquet_path.read_bytes() == previous_contents
    assert not manifest_path.exists()
    assert not list(parquet_path.parent.glob(f".{parquet_path.name}.*"))


def test_manifest_publish_failure_restores_previous_artifact_pair(
    tmp_path: Path, expected: InterimExpectations, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_dir, parquet_path, manifest_path = _build_paths(tmp_path)
    _write_raw_sources(raw_dir)
    parquet_path.parent.mkdir(parents=True)
    manifest_path.parent.mkdir(parents=True)
    previous_parquet = b"previous parquet"
    previous_manifest = b'{"version": "previous"}\n'
    parquet_path.write_bytes(previous_parquet)
    manifest_path.write_bytes(previous_manifest)
    real_replace = os.replace
    failure_injected = False

    def fail_first_manifest_publish(source: Path, destination: Path) -> None:
        nonlocal failure_injected
        if Path(destination) == manifest_path and not failure_injected:
            failure_injected = True
            raise OSError("falha simulada na publicação do manifesto")
        real_replace(source, destination)

    monkeypatch.setattr("tcc_prf_severity.data.interim.os.replace", fail_first_manifest_publish)

    with pytest.raises(OSError, match="falha simulada"):
        build_interim_dataset(
            raw_dir,
            parquet_path,
            manifest_path,
            expected=expected,
            project_root=tmp_path,
        )

    assert parquet_path.read_bytes() == previous_parquet
    assert manifest_path.read_bytes() == previous_manifest
    assert not list(parquet_path.parent.glob(f".{parquet_path.name}.*"))
    assert not list(manifest_path.parent.glob(f".{manifest_path.name}.*"))


def test_manifest_publish_failure_without_previous_pair_leaves_no_artifacts(
    tmp_path: Path, expected: InterimExpectations, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_dir, parquet_path, manifest_path = _build_paths(tmp_path)
    _write_raw_sources(raw_dir)
    real_replace = os.replace
    failure_injected = False

    def fail_first_manifest_publish(source: Path, destination: Path) -> None:
        nonlocal failure_injected
        if Path(destination) == manifest_path and not failure_injected:
            failure_injected = True
            raise OSError("falha simulada na publicação do manifesto")
        real_replace(source, destination)

    monkeypatch.setattr("tcc_prf_severity.data.interim.os.replace", fail_first_manifest_publish)

    with pytest.raises(OSError, match="falha simulada"):
        build_interim_dataset(
            raw_dir,
            parquet_path,
            manifest_path,
            expected=expected,
            project_root=tmp_path,
        )

    assert not parquet_path.exists()
    assert not manifest_path.exists()
    assert not list(parquet_path.parent.glob(f".{parquet_path.name}.*"))
    assert not list(manifest_path.parent.glob(f".{manifest_path.name}.*"))
