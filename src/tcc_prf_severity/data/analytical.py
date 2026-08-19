from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from tcc_prf_severity.analysis.road_environment import (
    ROAD_LAYOUT_COMPONENTS,
    extract_road_layout_components,
)
from tcc_prf_severity.analysis.temporal import derive_temporal_columns
from tcc_prf_severity.config import (
    EXPECTED_YEARS,
    INTERIM_MANIFEST_PATH,
    INTERIM_PARQUET_PATH,
    PRIMARY_ANALYTICAL_MANIFEST_PATH,
    PRIMARY_ANALYTICAL_PARQUET_PATH,
    PRIMARY_ANALYTICAL_SCHEMA_PATH,
    PRIMARY_FEATURE_CONTRACT_PATH,
    PROJECT_ROOT,
    RAW_DIR,
)
from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.data.interim import verify_interim_dataset

EXPECTED_CONCEPTUAL_FEATURES = (
    "month_name",
    "dia_semana",
    "hour",
    "uf",
    "br",
    "km",
    "sentido_via",
    "condicao_metereologica",
    "tipo_pista",
    "uso_solo",
    "tracado_via_components",
)
ROAD_LAYOUT_COLUMN_MAP = (
    ("Aclive", "tracado_aclive"),
    ("Curva", "tracado_curva"),
    ("Declive", "tracado_declive"),
    ("Desvio Temporário", "tracado_desvio_temporario"),
    ("Em Obras", "tracado_em_obras"),
    ("Interseção de Vias", "tracado_intersecao_de_vias"),
    ("Ponte", "tracado_ponte"),
    ("Reta", "tracado_reta"),
    ("Retorno Regulamentado", "tracado_retorno_regulamentado"),
    ("Rotatória", "tracado_rotatoria"),
    ("Túnel", "tracado_tunel"),
    ("Viaduto", "tracado_viaduto"),
)
METADATA_COLUMNS = ("id", "source_year", "data_inversa")
TARGET_COLUMN = "target_grave"
DIRECT_PREDICTOR_COLUMNS = (
    "month_name",
    "dia_semana",
    "hour",
    "uf",
    "br",
    "km",
    "sentido_via",
    "condicao_metereologica",
    "tipo_pista",
    "uso_solo",
)
ROAD_LAYOUT_INDICATOR_COLUMNS = tuple(column for _, column in ROAD_LAYOUT_COLUMN_MAP)
PHYSICAL_PREDICTOR_COLUMNS = DIRECT_PREDICTOR_COLUMNS + ROAD_LAYOUT_INDICATOR_COLUMNS
ANALYTICAL_COLUMNS = (*METADATA_COLUMNS, TARGET_COLUMN, *PHYSICAL_PREDICTOR_COLUMNS)
FORBIDDEN_COLUMNS = frozenset(
    {
        "mortos",
        "feridos_graves",
        "feridos_leves",
        "feridos",
        "ilesos",
        "ignorados",
        "classificacao_acidente",
        "regional",
        "delegacia",
        "uop",
        "tipo_acidente",
        "causa_acidente",
        "pessoas",
        "veiculos",
        "horario",
        "fase_dia",
        "municipio",
        "latitude",
        "longitude",
        "tracado_via",
    }
)
REQUIRED_CONTRACT_COLUMNS = frozenset(
    {"feature", "source", "representation", "rationale", "expected_future_preprocessing"}
)
REQUIRED_SOURCE_COLUMNS = frozenset(
    {
        *METADATA_COLUMNS,
        TARGET_COLUMN,
        "mortos",
        "feridos_graves",
        "horario",
        "fase_dia",
        "tracado_via",
        *(column for column in DIRECT_PREDICTOR_COLUMNS if column not in {"month_name", "hour"}),
    }
)


@dataclass(frozen=True)
class AnalyticalExpectations:
    years: tuple[int, ...] = EXPECTED_YEARS
    rows: int = 342_624
    graves: int = 96_857


@dataclass(frozen=True)
class AnalyticalArtifactResult:
    parquet_path: Path
    schema_path: Path
    manifest_path: Path
    rows: int
    columns: int
    predictor_columns: int
    metadata_columns: int
    years: tuple[int, ...]
    graves: int
    grave_rate: float
    unique_ids: int
    sha256: str
    missingness: dict[str, int]


DEFAULT_ANALYTICAL_EXPECTATIONS = AnalyticalExpectations()


def _logical_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_primary_feature_contract(path: Path = PRIMARY_FEATURE_CONTRACT_PATH) -> pl.DataFrame:
    """Carrega e valida o contrato autoritativo das 11 representações da Fase 3B."""
    if not path.is_file():
        raise FileNotFoundError(f"Contrato principal da Fase 3B não encontrado: {path}")
    try:
        contract = pl.read_csv(path)
    except Exception as error:
        raise ValueError(f"Não foi possível ler o contrato principal da Fase 3B: {path}") from error

    missing_columns = sorted(REQUIRED_CONTRACT_COLUMNS - set(contract.columns))
    if missing_columns:
        raise ValueError(
            f"Contrato principal da Fase 3B sem colunas obrigatórias: {missing_columns}"
        )

    features = tuple(str(value) for value in contract.get_column("feature").to_list())
    failures: list[str] = []
    if len(features) != len(set(features)):
        failures.append("há representações conceituais duplicadas")
    if features != EXPECTED_CONCEPTUAL_FEATURES:
        failures.append(
            "representações divergentes: "
            f"esperado={list(EXPECTED_CONCEPTUAL_FEATURES)!r}, recebido={list(features)!r}"
        )
    if failures:
        raise ValueError("Contrato principal da Fase 3B inválido: " + "; ".join(failures))
    return contract


def _require_source_columns(source: pl.DataFrame) -> None:
    missing = sorted(REQUIRED_SOURCE_COLUMNS - set(source.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes no interim: {missing}")
    if source.is_empty():
        raise ValueError("O dataset intermediário não pode estar vazio.")


def _validate_source(source: pl.DataFrame) -> None:
    _require_source_columns(source)
    duplicate_ids = source.height - int(source.get_column("id").n_unique())
    if duplicate_ids:
        raise ValueError(f"O dataset intermediário contém {duplicate_ids} IDs duplicados.")
    expected_target = (pl.col("mortos") > 0) | (pl.col("feridos_graves") > 0)
    mismatches = source.filter(pl.col(TARGET_COLUMN) != expected_target).height
    if mismatches:
        raise ValueError(
            f"target_grave diverge de (mortos > 0) OR (feridos_graves > 0) em {mismatches} linhas."
        )


def _materialize_road_layout_indicators(source: pl.DataFrame) -> pl.DataFrame:
    components = extract_road_layout_components(source)
    if tuple(ROAD_LAYOUT_COMPONENTS) != tuple(label for label, _ in ROAD_LAYOUT_COLUMN_MAP):
        raise RuntimeError(
            "O mapa físico de tracado_via diverge dos componentes validados na Fase 2D."
        )

    indicators = pl.DataFrame(
        {"_occurrence_index": pl.Series(range(source.height), dtype=pl.UInt32)}
    )
    for label, column in ROAD_LAYOUT_COLUMN_MAP:
        present = components.filter(pl.col("road_layout_component") == label).select(
            "_occurrence_index", pl.lit(1, dtype=pl.UInt8).alias(column)
        )
        indicators = indicators.join(present, on="_occurrence_index", how="left").with_columns(
            pl.col(column).fill_null(0).cast(pl.UInt8)
        )
    return indicators.drop("_occurrence_index")


def create_primary_analytical_dataset(
    source: pl.DataFrame,
    contract_path: Path = PRIMARY_FEATURE_CONTRACT_PATH,
) -> pl.DataFrame:
    """Materializa somente metadata, target e predictors autorizados, sem fit estatístico."""
    load_primary_feature_contract(contract_path)
    _validate_source(source)
    temporal = derive_temporal_columns(source)
    indicators = _materialize_road_layout_indicators(source)
    analytical = temporal.select(
        *METADATA_COLUMNS,
        TARGET_COLUMN,
        *DIRECT_PREDICTOR_COLUMNS,
    ).hstack(indicators)
    validate_primary_analytical_dataset(analytical, source)
    return analytical


def _dataset_metrics(df: pl.DataFrame) -> tuple[tuple[int, ...], int, int]:
    years = tuple(sorted(int(year) for year in df.get_column("source_year").unique().to_list()))
    graves = int(df.get_column(TARGET_COLUMN).sum())
    unique_ids = int(df.get_column("id").n_unique())
    return years, graves, unique_ids


def validate_primary_analytical_dataset(
    analytical: pl.DataFrame,
    source: pl.DataFrame,
    expected: AnalyticalExpectations | None = None,
) -> None:
    """Reconcilia população, papéis, target e representações físicas com o interim."""
    failures: list[str] = []
    if tuple(analytical.columns) != ANALYTICAL_COLUMNS:
        failures.append(
            f"colunas divergentes: esperado={list(ANALYTICAL_COLUMNS)!r}, "
            f"recebido={analytical.columns!r}"
        )
    forbidden = sorted(FORBIDDEN_COLUMNS & set(analytical.columns))
    if forbidden:
        failures.append(f"colunas proibidas presentes: {forbidden}")
    if analytical.height != source.height:
        failures.append(f"linhas: interim={source.height}, analítico={analytical.height}")

    for column in (*METADATA_COLUMNS, TARGET_COLUMN):
        if (
            column in analytical.columns
            and column in source.columns
            and not analytical.get_column(column).equals(source.get_column(column))
        ):
            failures.append(f"{column} mudou em relação ao interim")

    for column in DIRECT_PREDICTOR_COLUMNS[1:]:
        if (
            column in analytical.columns
            and column in source.columns
            and not analytical.get_column(column).equals(source.get_column(column))
        ):
            failures.append(f"{column} mudou em relação ao interim")

    if "id" in analytical.columns:
        unique_ids = int(analytical.get_column("id").n_unique())
        if unique_ids != analytical.height:
            failures.append(f"IDs únicos: esperado={analytical.height}, recebido={unique_ids}")

    for column in ROAD_LAYOUT_INDICATOR_COLUMNS:
        if column not in analytical.columns:
            continue
        values = set(analytical.get_column(column).drop_nulls().unique().to_list())
        if not values <= {0, 1} or analytical.get_column(column).null_count() > 0:
            failures.append(f"indicador {column} não é estritamente binário e não nulo")

    if expected is not None and {"source_year", TARGET_COLUMN} <= set(analytical.columns):
        years, graves, _ = _dataset_metrics(analytical)
        if analytical.height != expected.rows:
            failures.append(
                f"linhas do baseline: esperado={expected.rows}, recebido={analytical.height}"
            )
        if years != expected.years:
            failures.append(
                f"anos do baseline: esperado={list(expected.years)}, recebido={list(years)}"
            )
        if graves != expected.graves:
            failures.append(f"graves do baseline: esperado={expected.graves}, recebido={graves}")

    if failures:
        raise ValueError("Dataset analítico principal inválido:\n- " + "\n- ".join(failures))


def _allowed_values_note(column: str) -> str:
    notes = {
        "id": "ID único da ocorrência.",
        "source_year": "2021, 2022, 2023, 2024 ou 2025.",
        "data_inversa": "Data da ocorrência; metadata, não predictor.",
        TARGET_COLUMN: "Booleano definido por mortos > 0 ou feridos_graves > 0.",
        "month_name": "Nome do mês em português derivado de data_inversa.",
        "hour": "Inteiro de 0 a 23 derivado de horario.",
        "br": "Valor observado preservado, inclusive br = 0.",
        "km": "Valor numérico observado preservado, inclusive km = 0.",
        "sentido_via": "Categoria observada preservada, inclusive Não Informado.",
        "condicao_metereologica": "Categoria observada preservada, inclusive Ignorado.",
    }
    if column in ROAD_LAYOUT_INDICATOR_COLUMNS:
        return "Indicador binário: 0 ou 1."
    return notes.get(column, "Valor do contrato intermediário preservado sem imputação.")


def build_analytical_schema(
    analytical: pl.DataFrame,
    contract: pl.DataFrame,
) -> pl.DataFrame:
    """Constrói o esquema formal e os papéis das 26 colunas físicas."""
    contract_by_feature = {str(row["feature"]): row for row in contract.iter_rows(named=True)}
    rows: list[dict[str, Any]] = []
    for column in analytical.columns:
        if column in METADATA_COLUMNS:
            role = "metadata"
            conceptual_feature = "not_applicable"
            source = "interim"
            derivation = "preservada sem transformação"
            included = False
        elif column == TARGET_COLUMN:
            role = "target"
            conceptual_feature = TARGET_COLUMN
            source = "interim"
            derivation = "preservado; definição validada contra mortos e feridos_graves"
            included = False
        elif column in ROAD_LAYOUT_INDICATOR_COLUMNS:
            label = dict((physical, source) for source, physical in ROAD_LAYOUT_COLUMN_MAP)[column]
            role = "predictor"
            conceptual_feature = "tracado_via_components"
            source = "tracado_via"
            derivation = f"indicador determinístico da presença do componente {label}"
            included = True
        else:
            role = "predictor"
            conceptual_feature = column
            contract_row = contract_by_feature[column]
            source = str(contract_row["source"])
            if column == "month_name":
                derivation = "derivado deterministicamente de data_inversa"
            elif column == "hour":
                derivation = "derivado deterministicamente de horario"
            else:
                derivation = "preservada sem transformação"
            included = True
        rows.append(
            {
                "column": column,
                "role": role,
                "conceptual_feature": conceptual_feature,
                "source": source,
                "derivation": derivation,
                "dtype": str(analytical.schema[column]),
                "nullable": analytical.get_column(column).null_count() > 0,
                "allowed_values_note": _allowed_values_note(column),
                "included_in_model_matrix": included,
            }
        )
    return pl.DataFrame(rows)


def _missingness(df: pl.DataFrame) -> dict[str, int]:
    return {column: df.get_column(column).null_count() for column in df.columns}


def _manifest(
    analytical: pl.DataFrame,
    parquet_path: Path,
    parquet_sha256: str,
    parquet_size: int,
    interim_path: Path,
    contract_path: Path,
    schema_path: Path,
    schema_sha256: str,
    project_root: Path,
) -> dict[str, Any]:
    years, graves, unique_ids = _dataset_metrics(analytical)
    return {
        "artifact_name": parquet_path.name,
        "logical_path": _logical_path(parquet_path, project_root),
        "format": "parquet",
        "compression": "zstd",
        "rows": analytical.height,
        "columns": analytical.width,
        "predictor_column_count": len(PHYSICAL_PREDICTOR_COLUMNS),
        "metadata_column_count": len(METADATA_COLUMNS),
        "metadata_columns": list(METADATA_COLUMNS),
        "target_column": TARGET_COLUMN,
        "unique_ids": unique_ids,
        "years": list(years),
        "graves": graves,
        "grave_rate": round(graves / analytical.height, 9),
        "sha256": parquet_sha256,
        "size_bytes": parquet_size,
        "conceptual_feature_count": len(EXPECTED_CONCEPTUAL_FEATURES),
        "conceptual_features": list(EXPECTED_CONCEPTUAL_FEATURES),
        "physical_predictor_columns": list(PHYSICAL_PREDICTOR_COLUMNS),
        "road_layout_component_mapping": [
            {"source_label": label, "physical_column": column}
            for label, column in ROAD_LAYOUT_COLUMN_MAP
        ],
        "schema": {name: str(dtype) for name, dtype in analytical.schema.items()},
        "missingness": _missingness(analytical),
        "sources": {
            "interim": {
                "logical_path": _logical_path(interim_path, project_root),
                "sha256": sha256_file(interim_path),
            },
            "phase_3b_primary_feature_set": {
                "logical_path": _logical_path(contract_path, project_root),
                "sha256": sha256_file(contract_path),
            },
            "analytical_schema": {
                "logical_path": _logical_path(schema_path, project_root),
                "sha256": schema_sha256,
            },
        },
    }


def _backup_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.{uuid.uuid4().hex}.backup")


def _publish_artifacts(pairs: tuple[tuple[Path, Path], ...]) -> None:
    states = [
        {
            "temporary": temporary,
            "final": final,
            "existed": final.exists(),
            "backup": _backup_path(final),
            "backed_up": False,
        }
        for temporary, final in pairs
    ]
    try:
        for state in states:
            if state["existed"]:
                os.replace(state["final"], state["backup"])
                state["backed_up"] = True
        for state in states:
            os.replace(state["temporary"], state["final"])
    except BaseException as error:
        rollback_errors: list[str] = []
        for state in states:
            try:
                if state["backed_up"]:
                    os.replace(state["backup"], state["final"])
                elif not state["existed"]:
                    state["final"].unlink(missing_ok=True)
            except OSError as rollback_error:
                rollback_errors.append(f"{Path(state['final']).name}: {rollback_error}")
        for state in states:
            try:
                state["backup"].unlink(missing_ok=True)
            except OSError as cleanup_error:
                rollback_errors.append(f"limpeza de {Path(state['backup']).name}: {cleanup_error}")
        if rollback_errors:
            error.add_note("Falhas adicionais durante o rollback: " + "; ".join(rollback_errors))
        raise
    for state in states:
        state["backup"].unlink(missing_ok=True)


def _temporary_path(parent: Path, filename: str, suffix: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=parent,
        prefix=f".{filename}.",
        suffix=suffix,
        delete=False,
    ) as temporary_file:
        return Path(temporary_file.name)


def publish_primary_analytical_dataset(
    source: pl.DataFrame,
    *,
    interim_path: Path,
    contract_path: Path = PRIMARY_FEATURE_CONTRACT_PATH,
    parquet_path: Path = PRIMARY_ANALYTICAL_PARQUET_PATH,
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
    manifest_path: Path = PRIMARY_ANALYTICAL_MANIFEST_PATH,
    expected: AnalyticalExpectations = DEFAULT_ANALYTICAL_EXPECTATIONS,
    project_root: Path = PROJECT_ROOT,
) -> AnalyticalArtifactResult:
    """Constrói, valida e publica com rollback o Parquet, esquema e manifesto da 3C."""
    contract = load_primary_feature_contract(contract_path)
    interim_sha256 = sha256_file(interim_path)
    contract_sha256 = sha256_file(contract_path)
    analytical = create_primary_analytical_dataset(source, contract_path)
    validate_primary_analytical_dataset(analytical, source, expected)
    schema = build_analytical_schema(analytical, contract)

    temporary_parquet = _temporary_path(parquet_path.parent, parquet_path.name, ".parquet")
    temporary_schema = _temporary_path(schema_path.parent, schema_path.name, ".csv")
    temporary_manifest = _temporary_path(manifest_path.parent, manifest_path.name, ".json")
    try:
        analytical.write_parquet(temporary_parquet, compression="zstd")
        persisted = pl.read_parquet(temporary_parquet)
        validate_primary_analytical_dataset(persisted, source, expected)
        if not persisted.equals(analytical):
            raise ValueError("Parquet analítico não preservou o dataset após a releitura.")

        schema.write_csv(temporary_schema)
        persisted_schema = pl.read_csv(temporary_schema)
        if not persisted_schema.equals(schema):
            raise ValueError("Esquema analítico não foi preservado após a releitura.")

        if sha256_file(interim_path) != interim_sha256:
            raise RuntimeError("O Parquet intermediário foi alterado durante a construção.")
        if sha256_file(contract_path) != contract_sha256:
            raise RuntimeError("O contrato principal da Fase 3B foi alterado durante a construção.")

        parquet_sha256 = sha256_file(temporary_parquet)
        parquet_size = temporary_parquet.stat().st_size
        schema_sha256 = sha256_file(temporary_schema)
        manifest = _manifest(
            persisted,
            parquet_path,
            parquet_sha256,
            parquet_size,
            interim_path,
            contract_path,
            schema_path,
            schema_sha256,
            project_root,
        )
        temporary_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        _publish_artifacts(
            (
                (temporary_parquet, parquet_path),
                (temporary_schema, schema_path),
                (temporary_manifest, manifest_path),
            )
        )
        temporary_parquet = temporary_schema = temporary_manifest = Path()
    finally:
        for temporary in (temporary_parquet, temporary_schema, temporary_manifest):
            if temporary != Path():
                temporary.unlink(missing_ok=True)

    years, graves, unique_ids = _dataset_metrics(analytical)
    return AnalyticalArtifactResult(
        parquet_path=parquet_path,
        schema_path=schema_path,
        manifest_path=manifest_path,
        rows=analytical.height,
        columns=analytical.width,
        predictor_columns=len(PHYSICAL_PREDICTOR_COLUMNS),
        metadata_columns=len(METADATA_COLUMNS),
        years=years,
        graves=graves,
        grave_rate=graves / analytical.height,
        unique_ids=unique_ids,
        sha256=parquet_sha256,
        missingness=_missingness(analytical),
    )


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Manifesto analítico não encontrado: {path}")
    try:
        manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Não foi possível ler o manifesto analítico: {path}") from error
    if not isinstance(manifest, dict):
        raise ValueError("Manifesto analítico inválido: o conteúdo deve ser um objeto JSON.")
    return manifest


def verify_primary_analytical_artifacts(
    *,
    interim_path: Path,
    contract_path: Path = PRIMARY_FEATURE_CONTRACT_PATH,
    parquet_path: Path = PRIMARY_ANALYTICAL_PARQUET_PATH,
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
    manifest_path: Path = PRIMARY_ANALYTICAL_MANIFEST_PATH,
    expected: AnalyticalExpectations = DEFAULT_ANALYTICAL_EXPECTATIONS,
    project_root: Path = PROJECT_ROOT,
) -> AnalyticalArtifactResult:
    """Verifica o trio analítico e suas fontes sem reconstruir nem modificar artefatos."""
    for label, path in (("Parquet", parquet_path), ("esquema", schema_path)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} analítico não encontrado: {path}")
    if not interim_path.is_file():
        raise FileNotFoundError(f"Parquet intermediário não encontrado: {interim_path}")

    try:
        analytical = pl.read_parquet(parquet_path)
    except Exception as error:
        raise ValueError(f"Não foi possível ler o Parquet analítico: {parquet_path}") from error
    source = pl.read_parquet(interim_path)
    contract = load_primary_feature_contract(contract_path)
    validate_primary_analytical_dataset(analytical, source, expected)
    expected_analytical = create_primary_analytical_dataset(source, contract_path)
    if not analytical.equals(expected_analytical):
        raise ValueError(
            "O Parquet analítico diverge da materialização determinística "
            "do interim e do contrato 3B."
        )

    try:
        schema = pl.read_csv(schema_path)
    except Exception as error:
        raise ValueError(f"Não foi possível ler o esquema analítico: {schema_path}") from error
    expected_schema = build_analytical_schema(analytical, contract)
    if not schema.equals(expected_schema):
        raise ValueError("Esquema analítico diverge das colunas, papéis ou dtypes do Parquet.")

    parquet_sha256 = sha256_file(parquet_path)
    parquet_size = parquet_path.stat().st_size
    schema_sha256 = sha256_file(schema_path)
    expected_manifest = _manifest(
        analytical,
        parquet_path,
        parquet_sha256,
        parquet_size,
        interim_path,
        contract_path,
        schema_path,
        schema_sha256,
        project_root,
    )
    manifest = _read_manifest(manifest_path)
    failures = [
        field
        for field, expected_value in expected_manifest.items()
        if manifest.get(field) != expected_value
    ]
    unexpected = sorted(set(manifest) - set(expected_manifest))
    if failures or unexpected:
        details = []
        if failures:
            details.append(f"campos divergentes ou ausentes: {failures}")
        if unexpected:
            details.append(f"campos inesperados: {unexpected}")
        raise ValueError("Manifesto analítico divergente: " + "; ".join(details))

    years, graves, unique_ids = _dataset_metrics(analytical)
    return AnalyticalArtifactResult(
        parquet_path=parquet_path,
        schema_path=schema_path,
        manifest_path=manifest_path,
        rows=analytical.height,
        columns=analytical.width,
        predictor_columns=len(PHYSICAL_PREDICTOR_COLUMNS),
        metadata_columns=len(METADATA_COLUMNS),
        years=years,
        graves=graves,
        grave_rate=graves / analytical.height,
        unique_ids=unique_ids,
        sha256=parquet_sha256,
        missingness=_missingness(analytical),
    )


def build_primary_analytical_dataset(
    interim_path: Path = INTERIM_PARQUET_PATH,
    interim_manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    **paths: Any,
) -> AnalyticalArtifactResult:
    """Verifica o interim e publica o dataset analítico principal."""
    verify_interim_dataset(raw_dir, interim_path, interim_manifest_path)
    return publish_primary_analytical_dataset(
        pl.read_parquet(interim_path), interim_path=interim_path, **paths
    )


def verify_primary_analytical_dataset(
    interim_path: Path = INTERIM_PARQUET_PATH,
    interim_manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    **paths: Any,
) -> AnalyticalArtifactResult:
    """Verifica o interim e, sem reconstrução, o dataset analítico principal."""
    verify_interim_dataset(raw_dir, interim_path, interim_manifest_path)
    return verify_primary_analytical_artifacts(interim_path=interim_path, **paths)
