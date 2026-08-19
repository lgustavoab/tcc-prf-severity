import json
import os
from datetime import date, time
from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.data.analytical import (
    ANALYTICAL_COLUMNS,
    EXPECTED_CONCEPTUAL_FEATURES,
    FORBIDDEN_COLUMNS,
    METADATA_COLUMNS,
    PHYSICAL_PREDICTOR_COLUMNS,
    ROAD_LAYOUT_COLUMN_MAP,
    ROAD_LAYOUT_INDICATOR_COLUMNS,
    AnalyticalExpectations,
    build_analytical_schema,
    create_primary_analytical_dataset,
    load_primary_feature_contract,
    publish_primary_analytical_dataset,
    validate_primary_analytical_dataset,
    verify_primary_analytical_artifacts,
)
from tcc_prf_severity.data.audit import sha256_file


def _write_contract(path: Path, features: tuple[str, ...] = EXPECTED_CONCEPTUAL_FEATURES) -> None:
    sources = {
        "month_name": "data_inversa",
        "hour": "horario",
        "tracado_via_components": "tracado_via",
    }
    pl.DataFrame(
        {
            "feature": list(features),
            "source": [sources.get(feature, "interim") for feature in features],
            "representation": ["synthetic"] * len(features),
            "rationale": ["synthetic"] * len(features),
            "expected_future_preprocessing": ["none"] * len(features),
        }
    ).write_csv(path)


def _source() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "source_year": [2021, 2022, 2024, 2025],
            "data_inversa": [
                date(2021, 1, 2),
                date(2022, 6, 15),
                date(2024, 12, 31),
                date(2025, 3, 1),
            ],
            "dia_semana": ["sábado", "quarta-feira", "terça-feira", "sábado"],
            "horario": [time(0, 5), time(13, 45), time(23, 59), time(8, 30)],
            "fase_dia": ["Plena Noite", "Pleno dia", "Plena Noite", "Pleno dia"],
            "uf": ["SP", "MG", "PR", "BA"],
            "br": [0, 381, 116, 101],
            "km": [0.0, 10.5, 201.0, 3.2],
            "sentido_via": ["Não Informado", "Crescente", "Decrescente", "Crescente"],
            "condicao_metereologica": ["Ignorado", "Chuva", "Sol", "Céu Claro"],
            "tipo_pista": ["Simples", "Dupla", "Simples", "Múltipla"],
            "uso_solo": ["Sim", "Não", "Não", "Sim"],
            "tracado_via": ["Reta;Curva;Reta", "Aclive", "Ponte;Viaduto", "Em Obras"],
            "mortos": [0, 1, 0, 0],
            "feridos_graves": [0, 0, 2, 0],
            "target_grave": [False, True, True, False],
            "tipo_acidente": ["A", "B", "C", "D"],
            "causa_acidente": ["A", "B", "C", "D"],
            "pessoas": [1, 2, 3, 4],
            "veiculos": [1, 1, 2, 3],
            "classificacao_acidente": ["A", "B", "C", "D"],
            "feridos_leves": [0, 0, 0, 0],
            "feridos": [0, 0, 2, 0],
            "ilesos": [1, 1, 1, 1],
            "ignorados": [0, 0, 0, 0],
            "regional": ["R"] * 4,
            "delegacia": ["D"] * 4,
            "uop": ["U"] * 4,
            "municipio": ["M"] * 4,
            "latitude": [-20.0] * 4,
            "longitude": [-40.0] * 4,
        }
    )


@pytest.fixture
def contract_path(tmp_path: Path) -> Path:
    path = tmp_path / "phase_3b_primary_feature_set.csv"
    _write_contract(path)
    return path


def _expected() -> AnalyticalExpectations:
    return AnalyticalExpectations(years=(2021, 2022, 2024, 2025), rows=4, graves=2)


def _artifact_paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    return (
        tmp_path / "interim.parquet",
        tmp_path / "processed" / "analytical.parquet",
        tmp_path / "tables" / "schema.csv",
        tmp_path / "artifacts" / "manifest.json",
    )


def test_contract_is_loaded_with_exact_frozen_features(contract_path: Path) -> None:
    contract = load_primary_feature_contract(contract_path)

    assert tuple(contract.get_column("feature").to_list()) == EXPECTED_CONCEPTUAL_FEATURES


def test_contract_divergence_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    _write_contract(path, EXPECTED_CONCEPTUAL_FEATURES[:-1])

    with pytest.raises(ValueError, match="representações divergentes"):
        load_primary_feature_contract(path)


def test_only_authorized_physical_columns_are_materialized(contract_path: Path) -> None:
    analytical = create_primary_analytical_dataset(_source(), contract_path)

    assert tuple(analytical.columns) == ANALYTICAL_COLUMNS
    assert tuple(analytical.columns[4:]) == PHYSICAL_PREDICTOR_COLUMNS
    assert not (FORBIDDEN_COLUMNS & set(analytical.columns))
    assert len(PHYSICAL_PREDICTOR_COLUMNS) == 22


def test_temporal_derivations_and_metadata_are_preserved(contract_path: Path) -> None:
    analytical = create_primary_analytical_dataset(_source(), contract_path)

    assert analytical.get_column("month_name").to_list() == [
        "Janeiro",
        "Junho",
        "Dezembro",
        "Março",
    ]
    assert analytical.get_column("hour").to_list() == [0, 13, 23, 8]
    assert tuple(analytical.select(METADATA_COLUMNS).columns) == METADATA_COLUMNS
    assert "horario" not in analytical.columns
    assert "fase_dia" not in analytical.columns


def test_multilabel_indicators_are_binary_and_deduplicated(contract_path: Path) -> None:
    analytical = create_primary_analytical_dataset(_source(), contract_path)

    first = analytical.row(0, named=True)
    assert first["tracado_reta"] == 1
    assert first["tracado_curva"] == 1
    assert sum(int(first[column]) for column in ROAD_LAYOUT_INDICATOR_COLUMNS) == 2
    for column in ROAD_LAYOUT_INDICATOR_COLUMNS:
        assert set(analytical.get_column(column).unique().to_list()) <= {0, 1}
        assert analytical.schema[column] == pl.UInt8


def test_unknown_road_layout_component_is_rejected(contract_path: Path) -> None:
    source = _source().with_columns(pl.lit("Reta;Desconhecido").alias("tracado_via"))

    with pytest.raises(ValueError, match=r"Componentes desconhecidos.*Desconhecido"):
        create_primary_analytical_dataset(source, contract_path)


def test_duplicate_id_and_changed_target_are_rejected(contract_path: Path) -> None:
    duplicate = _source().with_columns(pl.Series("id", [1, 1, 3, 4]))
    with pytest.raises(ValueError, match="IDs duplicados"):
        create_primary_analytical_dataset(duplicate, contract_path)

    changed_target = _source().with_columns(pl.lit(False).alias("target_grave"))
    with pytest.raises(ValueError, match="target_grave diverge"):
        create_primary_analytical_dataset(changed_target, contract_path)


def test_target_rows_year_and_semantic_categories_are_preserved(contract_path: Path) -> None:
    source = _source()
    analytical = create_primary_analytical_dataset(source, contract_path)

    assert analytical.height == source.height
    assert analytical.get_column("target_grave").equals(source.get_column("target_grave"))
    assert analytical.get_column("source_year").equals(source.get_column("source_year"))
    assert analytical.get_column("sentido_via")[0] == "Não Informado"
    assert analytical.get_column("condicao_metereologica")[0] == "Ignorado"
    assert analytical.get_column("br")[0] == 0
    assert analytical.get_column("km")[0] == 0.0


def test_no_imputation_occurs_and_source_is_not_modified(
    contract_path: Path,
) -> None:
    source = _source().with_columns(
        pl.when(pl.col("id") == 1).then(None).otherwise(pl.col("uf")).alias("uf")
    )
    before = source.clone()

    analytical = create_primary_analytical_dataset(source, contract_path)

    assert analytical.get_column("uf").null_count() == 1
    assert source.equals(before)


def test_validation_detects_row_and_indicator_changes(contract_path: Path) -> None:
    source = _source()
    analytical = create_primary_analytical_dataset(source, contract_path)

    with pytest.raises(ValueError, match="linhas"):
        validate_primary_analytical_dataset(analytical.head(3), source)
    invalid_binary = analytical.with_columns(pl.lit(2).alias("tracado_reta"))
    with pytest.raises(ValueError, match="não é estritamente binário"):
        validate_primary_analytical_dataset(invalid_binary, source)


def test_schema_records_roles_mapping_and_model_matrix(contract_path: Path) -> None:
    contract = load_primary_feature_contract(contract_path)
    analytical = create_primary_analytical_dataset(_source(), contract_path)
    schema = build_analytical_schema(analytical, contract)

    assert schema.filter(pl.col("role") == "metadata").get_column("column").to_list() == list(
        METADATA_COLUMNS
    )
    assert schema.filter(pl.col("role") == "target").get_column("column").to_list() == [
        "target_grave"
    ]
    components = schema.filter(pl.col("conceptual_feature") == "tracado_via_components")
    assert components.height == 12
    assert components.get_column("included_in_model_matrix").all()


def test_publication_writes_reproducible_artifacts_and_manifest(
    tmp_path: Path, contract_path: Path
) -> None:
    interim_path, parquet_path, schema_path, manifest_path = _artifact_paths(tmp_path)
    source = _source()
    source.write_parquet(interim_path)

    result = publish_primary_analytical_dataset(
        source,
        interim_path=interim_path,
        contract_path=contract_path,
        parquet_path=parquet_path,
        schema_path=schema_path,
        manifest_path=manifest_path,
        expected=_expected(),
        project_root=tmp_path,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert result.rows == 4
    assert result.columns == 26
    assert result.predictor_columns == 22
    assert manifest["sha256"] == sha256_file(parquet_path)
    assert manifest["sources"]["interim"]["sha256"] == sha256_file(interim_path)
    assert manifest["sources"]["phase_3b_primary_feature_set"]["sha256"] == sha256_file(
        contract_path
    )
    assert manifest["conceptual_features"] == list(EXPECTED_CONCEPTUAL_FEATURES)
    assert manifest["road_layout_component_mapping"] == [
        {"source_label": label, "physical_column": column}
        for label, column in ROAD_LAYOUT_COLUMN_MAP
    ]


def test_verifier_accepts_valid_artifacts_and_rejects_tampered_hash(
    tmp_path: Path, contract_path: Path
) -> None:
    interim_path, parquet_path, schema_path, manifest_path = _artifact_paths(tmp_path)
    source = _source()
    source.write_parquet(interim_path)
    publish_primary_analytical_dataset(
        source,
        interim_path=interim_path,
        contract_path=contract_path,
        parquet_path=parquet_path,
        schema_path=schema_path,
        manifest_path=manifest_path,
        expected=_expected(),
        project_root=tmp_path,
    )

    result = verify_primary_analytical_artifacts(
        interim_path=interim_path,
        contract_path=contract_path,
        parquet_path=parquet_path,
        schema_path=schema_path,
        manifest_path=manifest_path,
        expected=_expected(),
        project_root=tmp_path,
    )
    assert result.unique_ids == 4

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="sha256"):
        verify_primary_analytical_artifacts(
            interim_path=interim_path,
            contract_path=contract_path,
            parquet_path=parquet_path,
            schema_path=schema_path,
            manifest_path=manifest_path,
            expected=_expected(),
            project_root=tmp_path,
        )


def test_verifier_rejects_changed_deterministic_derivation(
    tmp_path: Path, contract_path: Path
) -> None:
    interim_path, parquet_path, schema_path, manifest_path = _artifact_paths(tmp_path)
    source = _source()
    source.write_parquet(interim_path)
    publish_primary_analytical_dataset(
        source,
        interim_path=interim_path,
        contract_path=contract_path,
        parquet_path=parquet_path,
        schema_path=schema_path,
        manifest_path=manifest_path,
        expected=_expected(),
        project_root=tmp_path,
    )
    changed = pl.read_parquet(parquet_path).with_columns(
        pl.when(pl.col("id") == 1)
        .then(pl.lit("Fevereiro"))
        .otherwise(pl.col("month_name"))
        .alias("month_name")
    )
    changed.write_parquet(parquet_path)

    with pytest.raises(ValueError, match="materialização determinística"):
        verify_primary_analytical_artifacts(
            interim_path=interim_path,
            contract_path=contract_path,
            parquet_path=parquet_path,
            schema_path=schema_path,
            manifest_path=manifest_path,
            expected=_expected(),
            project_root=tmp_path,
        )


def test_publish_failure_restores_previous_artifacts_without_residue(
    tmp_path: Path, contract_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    interim_path, parquet_path, schema_path, manifest_path = _artifact_paths(tmp_path)
    source = _source()
    source.write_parquet(interim_path)
    for path in (parquet_path, schema_path, manifest_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"previous {path.name}".encode())
    previous = {path: path.read_bytes() for path in (parquet_path, schema_path, manifest_path)}
    real_replace = os.replace
    failure_injected = False

    def fail_manifest_publish(source_path: Path, destination: Path) -> None:
        nonlocal failure_injected
        if Path(destination) == manifest_path and not failure_injected:
            failure_injected = True
            raise OSError("falha simulada no manifesto")
        real_replace(source_path, destination)

    monkeypatch.setattr("tcc_prf_severity.data.analytical.os.replace", fail_manifest_publish)

    with pytest.raises(OSError, match="falha simulada"):
        publish_primary_analytical_dataset(
            source,
            interim_path=interim_path,
            contract_path=contract_path,
            parquet_path=parquet_path,
            schema_path=schema_path,
            manifest_path=manifest_path,
            expected=_expected(),
            project_root=tmp_path,
        )

    assert {path: path.read_bytes() for path in previous} == previous
    assert not list(tmp_path.rglob("*.backup"))
    assert not [path for path in tmp_path.rglob(".*") if path.is_file()]
