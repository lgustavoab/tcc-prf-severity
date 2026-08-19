from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import polars as pl
import pytest

from tcc_prf_severity.config import PROJECT_ROOT
from tcc_prf_severity.dashboard.contracts import (
    ASSET_SPECS,
    CONTEXTUAL_DIMENSIONS,
    GEOGRAPHY_DIMENSIONS,
    LOGICAL_ASSET_IDS,
    SCHEMA_VERSION,
    TEMPORAL_DIMENSIONS,
)
from tcc_prf_severity.dashboard.export import (
    _publish_bytes,
    aggregate_exploratory,
    export_dashboard_data,
)

FIXED_GENERATED_AT = "2026-08-19T18:00:00Z"


def _load(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _all_values(value: Any) -> Iterator[Any]:
    yield value
    if isinstance(value, dict):
        for nested in value.values():
            yield from _all_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _all_values(nested)


@pytest.fixture(scope="module")
def exported_data(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("dashboard-export") / "data"
    result = export_dashboard_data(generated_at=FIXED_GENERATED_AT, output_dir=output)
    assert result.physical_asset_count == 14
    assert result.logical_asset_count == 12
    return output


def test_aggregate_exploratory_uses_only_observed_cells_and_validates_measures() -> None:
    frame = pl.DataFrame(
        {
            "source_year": [2022, 2021, 2021, 2022],
            "dia_semana": ["terça-feira", "segunda-feira", "segunda-feira", "terça-feira"],
            "hour": [9, 8, 8, 9],
            "target_grave": [True, False, True, False],
        }
    )

    rows = aggregate_exploratory(frame, TEMPORAL_DIMENSIONS)

    assert len(rows) == 2
    assert rows[0] == {
        "source_year": 2021,
        "dia_semana": "segunda-feira",
        "hour": 8,
        "total_occurrences": 2,
        "severe_occurrences": 1,
        "non_severe_occurrences": 1,
        "severe_proportion": 0.5,
    }
    assert rows[1]["total_occurrences"] == 2
    assert rows[1]["severe_occurrences"] == 1


@pytest.mark.parametrize(
    "generated_at",
    ["2026-08-19", "2026-08-19T18:00:00", "2026-08-19T18:00:00-03:00", "invalid"],
)
def test_generated_at_requires_explicit_utc(generated_at: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="generated_at"):
        export_dashboard_data(generated_at=generated_at, output_dir=tmp_path / "data")


def test_manifest_covers_twelve_logical_assets_and_fourteen_parts(
    exported_data: Path,
) -> None:
    manifest = _load(exported_data / "manifest.json")

    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["generated_at"] == FIXED_GENERATED_AT
    assert len(manifest["assets"]) == len(ASSET_SPECS) == 14
    assert {asset["asset_id"] for asset in manifest["assets"]} == set(LOGICAL_ASSET_IDS)
    assert len(LOGICAL_ASSET_IDS) == 12
    assert not any(asset["path"] == "manifest.json" for asset in manifest["assets"])


def test_manifest_hashes_sizes_rows_and_sources_are_exact(exported_data: Path) -> None:
    manifest = _load(exported_data / "manifest.json")
    for asset in manifest["assets"]:
        path = exported_data / asset["path"]
        payload = path.read_bytes()
        loaded = json.loads(payload)
        expected_rows = len(loaded["data"]) if isinstance(loaded.get("data"), list) else 1

        assert path.is_file()
        assert asset["size_bytes"] == len(payload)
        assert asset["sha256"] == hashlib.sha256(payload).hexdigest()
        assert asset["row_count"] == expected_rows
        assert asset["generation_status"] == "generated"
        assert all((PROJECT_ROOT / source).is_file() for source in asset["source_artifacts"])


def test_every_asset_has_schema_metadata_numeric_values_and_no_non_finite(
    exported_data: Path,
) -> None:
    manifest = _load(exported_data / "manifest.json")
    for asset in manifest["assets"]:
        payload = _load(exported_data / asset["path"])
        metadata = payload["metadata"]
        assert metadata["schema_version"] == "1"
        assert metadata["asset_id"] == asset["asset_id"]
        assert metadata["part_id"] == asset["part_id"]
        assert metadata["scientific_status"] == asset["scientific_status"]
        for value in _all_values(payload):
            if isinstance(value, float):
                assert math.isfinite(value)


def test_exploratory_scopes_are_isolated_and_have_no_individual_ids(
    exported_data: Path,
) -> None:
    expectations = {
        "exploration/temporal.json": set(TEMPORAL_DIMENSIONS),
        "exploration/contextual.json": set(CONTEXTUAL_DIMENSIONS),
        "geography/geography.json": set(GEOGRAPHY_DIMENSIONS),
    }
    forbidden = {
        "exploration/temporal.json": {
            "tipo_pista",
            "condicao_metereologica",
            "uso_solo",
            "uf",
            "br",
        },
        "exploration/contextual.json": {"dia_semana", "hour", "uf", "br"},
        "geography/geography.json": {
            "dia_semana",
            "hour",
            "tipo_pista",
            "condicao_metereologica",
            "uso_solo",
        },
    }
    for relative, dimensions in expectations.items():
        payload = _load(exported_data / relative)
        assert set(payload["dimensions"]) == dimensions
        for row in payload["data"]:
            assert not (set(row) & forbidden[relative])
            assert "id" not in row
            assert "latitude" not in row
            assert "longitude" not in row


def test_exploratory_totals_reconcile_globally_and_annually(exported_data: Path) -> None:
    t1 = _csv_rows(PROJECT_ROOT / "reports/tables/tcc/T1_population_characterization.csv")
    expected = {
        int(row["Ano"]): (int(row["Ocorrências"]), int(row["Graves"]))
        for row in t1
        if row["Ano"] != "Total"
    }
    for relative in (
        "exploration/temporal.json",
        "exploration/contextual.json",
        "geography/geography.json",
    ):
        rows = _load(exported_data / relative)["data"]
        assert sum(row["total_occurrences"] for row in rows) == 342_624
        assert sum(row["severe_occurrences"] for row in rows) == 96_857
        assert sum(row["non_severe_occurrences"] for row in rows) == 245_767
        for year, (total, severe) in expected.items():
            selected = [row for row in rows if row["source_year"] == year]
            assert sum(row["total_occurrences"] for row in selected) == total
            assert sum(row["severe_occurrences"] for row in selected) == severe


def test_geography_dependency_is_derived_from_published_rows(exported_data: Path) -> None:
    payload = _load(exported_data / "geography/geography.json")
    rows = payload["data"]
    br_by_uf = payload["filters"]["br_by_uf"]

    assert set(br_by_uf) == set(payload["filters"]["ufs"])
    assert 0 in payload["filters"]["brs"]
    for uf, brs in br_by_uf.items():
        observed = sorted({row["br"] for row in rows if row["uf"] == uf})
        assert brs == observed


def test_frozen_results_equal_published_sources_without_recomputation(
    exported_data: Path,
) -> None:
    comparison_source = {
        row["model_id"]: row
        for row in _csv_rows(PROJECT_ROOT / "reports/tables/phase_4d_model_comparison.csv")
    }
    comparison = _load(exported_data / "models/model_comparison.json")
    for row in comparison["data"]:
        source = comparison_source[row["model_id"]]
        assert row["mean_average_precision"] == float(source["ap_unweighted_mean"])
        assert row["ap_standard_deviation"] == float(source["ap_population_std"])

    fold_source = _csv_rows(PROJECT_ROOT / "reports/tables/phase_4d_fold_comparison.csv")
    temporal = _load(exported_data / "validation/temporal_validation.json")
    assert temporal["validation_year_role"] == "published_result_dimension_not_population_filter"

    source_keys = [
        (row["model_id"], int(row["fold"]), int(row["validation_year"])) for row in fold_source
    ]
    exported_keys = [
        (row["model_id"], row["fold"], row["validation_year"]) for row in temporal["data"]
    ]
    assert len(source_keys) == len(set(source_keys)) == 9
    assert len(exported_keys) == len(set(exported_keys)) == 9
    assert set(exported_keys) == set(source_keys)

    source_by_key = dict(zip(source_keys, fold_source, strict=True))
    exported_by_key = dict(zip(exported_keys, temporal["data"], strict=True))
    for key, source_row in source_by_key.items():
        exported_row = exported_by_key[key]
        for metric in ("average_precision", "roc_auc", "brier_score"):
            assert exported_row[metric] == float(source_row[metric])

    calibration_source = _csv_rows(PROJECT_ROOT / "reports/tables/phase_4h_calibration.csv")
    calibration = _load(exported_data / "models/calibration_2025.json")
    assert [row["mean_predicted_probability"] for row in calibration["data"]] == [
        float(row["mean_predicted_probability"]) for row in calibration_source
    ]

    top_source = _csv_rows(PROJECT_ROOT / "reports/tables/tcc/A1_top15_transformed_features.csv")
    top15 = _load(exported_data / "interpretation/transformed_top15.json")
    assert [row["mean_absolute_shap"] for row in top15["data"]] == [
        float(row["Contribuição absoluta média"]) for row in top_source
    ]


def test_frozen_assets_have_no_population_filters_or_recomputation_contracts(
    exported_data: Path,
) -> None:
    manifest = _load(exported_data / "manifest.json")
    frozen = [
        asset for asset in manifest["assets"] if asset["scientific_status"] == "FROZEN_RESULT"
    ]
    forbidden_terms = {
        "ap_recomputation",
        "shap_recomputation",
        "threshold_recomputation",
        "predict",
        "predict_proba",
    }
    for asset in frozen:
        payload = _load(exported_data / asset["path"])
        assert "filters" not in payload
        assert forbidden_terms.isdisjoint(payload)


def test_export_is_bytewise_deterministic_for_fixed_generated_at(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    export_dashboard_data(generated_at=FIXED_GENERATED_AT, output_dir=first)
    export_dashboard_data(generated_at=FIXED_GENERATED_AT, output_dir=second)

    first_files = sorted(path.relative_to(first) for path in first.rglob("*.json"))
    second_files = sorted(path.relative_to(second) for path in second.rglob("*.json"))
    assert first_files == second_files
    assert len(first_files) == 15
    for relative in first_files:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()


def test_assets_are_below_review_and_hard_size_limits(exported_data: Path) -> None:
    manifest = _load(exported_data / "manifest.json")
    assert max(asset["size_bytes"] for asset in manifest["assets"]) < 2 * 1024 * 1024
    assert max(asset["size_bytes"] for asset in manifest["assets"]) < 5 * 1024 * 1024


def test_publication_failure_restores_previous_managed_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "data"
    output.mkdir()
    previous = {"a.json": b"old-a\n", "nested/b.json": b"old-b\n"}
    for relative, payload in previous.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    original_replace = os.replace

    def fail_second_publish(source: str | Path, destination: str | Path) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        if destination_path == output / "nested/b.json" and ".dashboard-data-stage-" in str(
            source_path
        ):
            raise OSError("falha simulada na publicação")
        original_replace(source, destination)

    monkeypatch.setattr("tcc_prf_severity.dashboard.export.os.replace", fail_second_publish)
    with pytest.raises(OSError, match="falha simulada"):
        _publish_bytes(output, {"a.json": b"new-a\n", "nested/b.json": b"new-b\n"})

    assert {relative: (output / relative).read_bytes() for relative in previous} == previous
    assert not list(tmp_path.glob(".dashboard-data-stage-*"))
    assert not list(tmp_path.glob(".dashboard-data-backup-*"))


def test_export_preserves_unmanaged_json_inside_data_directory(tmp_path: Path) -> None:
    output = tmp_path / "data"
    output.mkdir()
    unmanaged = output / "unmanaged.json"
    unmanaged.write_text('{"owner":"human"}\n', encoding="utf-8")

    export_dashboard_data(generated_at=FIXED_GENERATED_AT, output_dir=output)

    assert unmanaged.read_text(encoding="utf-8") == '{"owner":"human"}\n'


def test_phase_6b_does_not_create_frontend_scaffolding() -> None:
    assert not (PROJECT_ROOT / "dashboard/package.json").exists()
    assert not (PROJECT_ROOT / "dashboard/tsconfig.json").exists()
    assert not (PROJECT_ROOT / "dashboard/src").exists()
    assert not (PROJECT_ROOT / "dashboard/node_modules").exists()
