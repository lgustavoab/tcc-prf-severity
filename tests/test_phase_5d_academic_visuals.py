from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import polars as pl
import pytest

from tcc_prf_severity.config import PROJECT_ROOT
from tcc_prf_severity.presentation.academic_visuals import (
    SOURCE_SPECS,
    GenerationResult,
    generate_academic_visuals,
    load_confusion_counts,
    load_fold_average_precision,
    load_model_average_precision,
    validate_sources,
)


@dataclass(frozen=True)
class GeneratedBundle:
    output_root: Path
    result: GenerationResult
    source_hashes_before: dict[str, str]
    source_hashes_after: dict[str, str]


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


@pytest.fixture(scope="module")
def frozen_sources() -> dict[str, pl.DataFrame]:
    return validate_sources(PROJECT_ROOT)


@pytest.fixture(scope="module")
def generated_bundle(tmp_path_factory: pytest.TempPathFactory) -> GeneratedBundle:
    source_paths = {
        filename: PROJECT_ROOT / "reports" / "tables" / filename for filename in SOURCE_SPECS
    }
    before = {filename: _sha256(path) for filename, path in source_paths.items()}
    output_root = tmp_path_factory.mktemp("phase5d") / "reports"
    result = generate_academic_visuals(project_root=PROJECT_ROOT, output_root=output_root)
    after = {filename: _sha256(path) for filename, path in source_paths.items()}
    return GeneratedBundle(output_root, result, before, after)


def test_required_sources_and_columns_are_recognized(
    frozen_sources: dict[str, pl.DataFrame],
) -> None:
    assert set(frozen_sources) == set(SOURCE_SPECS)
    for filename, required_columns in SOURCE_SPECS.items():
        assert required_columns <= set(frozen_sources[filename].columns)


def test_generation_creates_all_png_svg_and_csv_outputs(
    generated_bundle: GeneratedBundle,
) -> None:
    result = generated_bundle.result
    assert {artifact.visual_id for artifact in result.figures} == {
        "M1",
        "F1",
        "F2",
        "F4",
        "F5",
        "F6",
        "F7",
        "F8",
        "A2",
    }
    assert {artifact.visual_id for artifact in result.tables} == {
        "M2",
        "T1",
        "T2",
        "A1",
        "A3",
        "A4",
    }
    assert all(
        artifact.png_path.is_file()
        and artifact.png_path.stat().st_size > 0
        and artifact.svg_path.is_file()
        and artifact.svg_path.stat().st_size > 0
        for artifact in result.figures
    )
    assert all(
        artifact.path.is_file() and artifact.path.stat().st_size > 0 for artifact in result.tables
    )


def test_manifest_contains_all_mandatory_visual_ids(generated_bundle: GeneratedBundle) -> None:
    manifest = pl.read_csv(generated_bundle.result.manifest_path)
    assert set(manifest.get_column("visual_id")) == {
        "M1",
        "M2",
        "T1",
        "F1",
        "F2",
        "F4",
        "F5",
        "T2",
        "F6",
        "F7",
        "F8",
        "A1",
        "A2",
        "A3",
        "A4",
        "REVIEW",
    }
    assert manifest.filter(pl.col("status") != "generated").is_empty()
    assert (
        manifest.filter((pl.col("artifact_type") == "figure") & (pl.col("format") == "png")).height
        == 9
    )
    assert (
        manifest.filter((pl.col("artifact_type") == "figure") & (pl.col("format") == "svg")).height
        == 9
    )


def test_f6_preserves_frozen_confusion_counts(
    frozen_sources: dict[str, pl.DataFrame],
) -> None:
    assert load_confusion_counts(frozen_sources) == {
        "threshold": 0.23723246157169342,
        "tn": 20_153,
        "fp": 31_883,
        "fn": 4_676,
        "tp": 15_817,
    }


def test_f4_preserves_the_three_published_average_precisions(
    frozen_sources: dict[str, pl.DataFrame],
) -> None:
    assert load_model_average_precision(frozen_sources) == {
        "phase_4a_logistic_baseline": 0.3935082935577437,
        "phase_4b_random_forest_baseline": 0.3959839275865431,
        "phase_4c_xgboost_baseline": 0.40081097458169895,
    }


def test_f5_preserves_all_nine_published_fold_values(
    frozen_sources: dict[str, pl.DataFrame],
) -> None:
    observed = load_fold_average_precision(frozen_sources)
    assert len(observed) == 9
    assert {(fold, model, value) for fold, _, model, value in observed} == {
        (1, "phase_4a_logistic_baseline", 0.3866809762501382),
        (1, "phase_4b_random_forest_baseline", 0.3880957692713414),
        (1, "phase_4c_xgboost_baseline", 0.390374557377428),
        (2, "phase_4a_logistic_baseline", 0.3960583174959361),
        (2, "phase_4b_random_forest_baseline", 0.3996726973944841),
        (2, "phase_4c_xgboost_baseline", 0.40496847114969603),
        (3, "phase_4a_logistic_baseline", 0.3977855869271569),
        (3, "phase_4b_random_forest_baseline", 0.4001833160938038),
        (3, "phase_4c_xgboost_baseline", 0.4070898952179728),
    }


def test_generation_does_not_overwrite_scientific_sources(
    generated_bundle: GeneratedBundle,
) -> None:
    assert generated_bundle.source_hashes_before == generated_bundle.source_hashes_after


def test_repeated_generation_is_logically_idempotent(
    generated_bundle: GeneratedBundle,
) -> None:
    csv_paths = sorted(generated_bundle.output_root.rglob("*.csv"))
    before = {
        path.relative_to(generated_bundle.output_root): pl.read_csv(path)
        for path in csv_paths
        if path.name != "phase_5d_visual_qa.csv"
    }
    qa_before = pl.read_csv(generated_bundle.result.qa_path).drop(
        ["png_size_bytes", "svg_size_bytes"]
    )

    generate_academic_visuals(project_root=PROJECT_ROOT, output_root=generated_bundle.output_root)

    after = {
        path.relative_to(generated_bundle.output_root): pl.read_csv(path)
        for path in sorted(generated_bundle.output_root.rglob("*.csv"))
        if path.name != "phase_5d_visual_qa.csv"
    }
    qa_after = pl.read_csv(generated_bundle.result.qa_path).drop(
        ["png_size_bytes", "svg_size_bytes"]
    )
    assert before.keys() == after.keys()
    assert all(before[path].equals(after[path]) for path in before)
    assert qa_before.equals(qa_after)


def test_outputs_are_restricted_to_requested_root(generated_bundle: GeneratedBundle) -> None:
    output_root = generated_bundle.output_root.resolve()
    paths = [
        *(artifact.png_path for artifact in generated_bundle.result.figures),
        *(artifact.svg_path for artifact in generated_bundle.result.figures),
        *(artifact.path for artifact in generated_bundle.result.tables),
        generated_bundle.result.contact_sheet,
        generated_bundle.result.manifest_path,
        generated_bundle.result.qa_path,
        generated_bundle.result.checklist_path,
    ]
    assert all(path.resolve().is_relative_to(output_root) for path in paths)
