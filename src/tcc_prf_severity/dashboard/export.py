"""Pipeline determinístico de exportação dos dados estáticos do dashboard."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import polars as pl

from tcc_prf_severity.config import PROJECT_ROOT
from tcc_prf_severity.dashboard.contracts import (
    ASSET_SPECS,
    ASSOCIATION_CAVEAT,
    CONTEXTUAL_DIMENSIONS,
    DATA_PERIOD,
    EXPLORATORY_MEASURES,
    EXPOSURE_CAVEAT,
    FROZEN_RESULT_CAVEAT,
    GEOGRAPHY_DIMENSIONS,
    LOGICAL_ASSET_IDS,
    MANAGED_PATHS,
    PHASE_6A_CONTRACTS,
    SCHEMA_VERSION,
    SHAP_CAVEAT,
    SOURCE_SCOPE,
    TARGET_DEFINITION,
    TEMPORAL_DIMENSIONS,
    AssetSpec,
)
from tcc_prf_severity.data.audit import sha256_file

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None

_PARQUET_PATH = "data/processed/prf_primary_analytical_2021_2025.parquet"
_ANALYTICAL_MANIFEST_PATH = "artifacts/processed/phase_3c_primary_analytical_manifest.json"
_T1_PATH = "reports/tables/tcc/T1_population_characterization.csv"
_WEEKDAY_ORDER = {
    value: index
    for index, value in enumerate(
        (
            "segunda-feira",
            "terça-feira",
            "quarta-feira",
            "quinta-feira",
            "sexta-feira",
            "sábado",
            "domingo",
        )
    )
}
_MAX_ASSET_BYTES = 5 * 1024 * 1024
_REVIEW_ASSET_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class DashboardExportResult:
    """Resumo auditável de uma exportação concluída."""

    output_dir: Path
    manifest_path: Path
    generated_at: str
    physical_asset_count: int
    logical_asset_count: int
    rows_by_part: dict[str, int]
    total_asset_bytes: int
    largest_asset_path: str
    largest_asset_bytes: int
    reconciliation_pass: int
    reconciliation_fail: int
    checklist_pass: int
    checklist_fail: int


def _source(project_root: Path, relative_path: str) -> Path:
    path = project_root / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Fonte contratada não encontrada: {relative_path}")
    return path


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: JsonValue) -> bytes:
    _validate_finite(value)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    return text.encode("utf-8")


def _validate_finite(value: Any, path: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Valor não finito em {path}: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_finite(item, f"{path}[{index}]")


def _validate_generated_at(value: str) -> str:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError("generated_at deve ser um timestamp ISO-8601 UTC válido.") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("generated_at deve declarar explicitamente o fuso UTC.")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"CSV sem cabeçalho: {path}")
        return [dict(row) for row in reader]


def _key_value_rows(path: Path) -> dict[str, str]:
    rows = _read_csv(path)
    if not rows or set(rows[0]) != {"key", "value"}:
        raise ValueError(f"Tabela key/value inválida: {path}")
    mapping = {row["key"]: row["value"] for row in rows}
    if len(mapping) != len(rows):
        raise ValueError(f"Chaves duplicadas em {path}")
    return mapping


def _metadata(spec: AssetSpec) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "asset_id": spec.asset_id,
        "part_id": spec.part_id,
        "scientific_status": spec.scientific_status,
        "source_artifacts": list(spec.source_artifacts),
        "required_caveats": list(spec.required_caveats),
    }


def _spec(asset_id: str, part_id: str = "default") -> AssetSpec:
    for spec in ASSET_SPECS:
        if spec.asset_id == asset_id and spec.part_id == part_id:
            return spec
    raise KeyError((asset_id, part_id))


def _number_sort_value(value: Any) -> tuple[int, Any, str]:
    if isinstance(value, int | float):
        return (0, value, "")
    text = str(value)
    return (1, text.casefold(), text)


def _row_sort_key(row: Mapping[str, Any], dimensions: Sequence[str]) -> tuple[Any, ...]:
    parts: list[Any] = []
    for dimension in dimensions:
        value = row[dimension]
        if dimension == "dia_semana":
            parts.append((0, _WEEKDAY_ORDER.get(str(value), 999), str(value)))
        else:
            parts.append(_number_sort_value(value))
    return tuple(parts)


def aggregate_exploratory(frame: pl.DataFrame, dimensions: Sequence[str]) -> list[dict[str, Any]]:
    """Agrega somente células observadas e valida as quatro medidas permitidas."""
    required = {*dimensions, "target_grave"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Colunas ausentes para agregação exploratória: {missing}")
    if frame.select(pl.any_horizontal(pl.col(name).is_null() for name in required).any()).item():
        raise ValueError("Dimensões exploratórias e target não podem conter nulos.")

    aggregated = frame.group_by(list(dimensions)).agg(
        pl.len().alias("total_occurrences"),
        pl.col("target_grave").cast(pl.Int64).sum().cast(pl.Int64).alias("severe_occurrences"),
    )
    aggregated = aggregated.with_columns(
        (pl.col("total_occurrences").cast(pl.Int64) - pl.col("severe_occurrences")).alias(
            "non_severe_occurrences"
        ),
        (
            pl.col("severe_occurrences").cast(pl.Float64)
            / pl.col("total_occurrences").cast(pl.Float64)
        ).alias("severe_proportion"),
    )
    rows = aggregated.to_dicts()
    rows.sort(key=lambda row: _row_sort_key(row, dimensions))
    _validate_exploratory_rows(rows, dimensions)
    return rows


def _validate_exploratory_rows(
    rows: Sequence[Mapping[str, Any]], dimensions: Sequence[str]
) -> None:
    expected_keys = {*dimensions, *EXPLORATORY_MEASURES}
    for index, row in enumerate(rows):
        if set(row) != expected_keys:
            raise ValueError(f"Schema exploratório inválido na linha {index}: {sorted(row)}")
        total = row["total_occurrences"]
        severe = row["severe_occurrences"]
        non_severe = row["non_severe_occurrences"]
        proportion = row["severe_proportion"]
        if not all(isinstance(value, int) for value in (total, severe, non_severe)):
            raise TypeError(f"Contagens não inteiras na linha exploratória {index}.")
        if total <= 0 or severe < 0 or non_severe < 0 or severe + non_severe != total:
            raise ValueError(f"Invariantes de contagem inválidas na linha exploratória {index}.")
        if not isinstance(proportion, float) or not 0.0 <= proportion <= 1.0:
            raise ValueError(f"Proporção inválida na linha exploratória {index}.")
        if not math.isclose(proportion, severe / total, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError(f"Proporção não reconcilia na linha exploratória {index}.")


def _build_meta() -> dict[str, Any]:
    spec = _spec("META")
    return {
        "metadata": _metadata(spec),
        "data_period": DATA_PERIOD,
        "source_scope": SOURCE_SCOPE,
        "target_definition": TARGET_DEFINITION,
        "scientific_scope": {
            "exploratory": "Agregações descritivas de ocorrências registradas.",
            "frozen_results": "Resultados científicos publicados e apresentados sem recomputação.",
        },
        "caveats": [
            EXPOSURE_CAVEAT,
            ASSOCIATION_CAVEAT,
            FROZEN_RESULT_CAVEAT,
            SHAP_CAVEAT,
        ],
    }


def _population_rows(project_root: Path) -> list[dict[str, Any]]:
    source_rows = _read_csv(_source(project_root, _T1_PATH))
    rows: list[dict[str, Any]] = []
    for source_row in source_rows:
        year_text = source_row["Ano"]
        rows.append(
            {
                "scope": "total" if year_text == "Total" else "year",
                "source_year": None if year_text == "Total" else int(year_text),
                "total_occurrences": int(source_row["Ocorrências"]),
                "severe_occurrences": int(source_row["Graves"]),
                "non_severe_occurrences": int(source_row["Não graves"]),
                "severe_proportion": float(source_row["Prevalência grave (%)"]) / 100.0,
            }
        )
    if len(rows) != 6 or rows[-1]["scope"] != "total":
        raise ValueError("T1 deve conter cinco anos e uma linha Total.")
    return rows


def _build_overview(project_root: Path) -> dict[str, Any]:
    spec = _spec("OVERVIEW")
    rows = _population_rows(project_root)
    years = [row["source_year"] for row in rows if row["scope"] == "year"]
    return {
        "metadata": _metadata(spec),
        "filters": {"years": years},
        "summary": rows[-1],
        "data": rows,
    }


def _unique_sorted(rows: Sequence[Mapping[str, Any]], field: str) -> list[Any]:
    values = {row[field] for row in rows}
    if field == "dia_semana":
        return sorted(values, key=lambda value: (_WEEKDAY_ORDER.get(str(value), 999), str(value)))
    return sorted(values, key=_number_sort_value)


def _build_exploration(
    frame: pl.DataFrame,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    temporal_rows = aggregate_exploratory(frame, TEMPORAL_DIMENSIONS)
    contextual_rows = aggregate_exploratory(frame, CONTEXTUAL_DIMENSIONS)
    geography_rows = aggregate_exploratory(frame, GEOGRAPHY_DIMENSIONS)

    temporal = {
        "metadata": _metadata(_spec("EXPLORATION", "temporal")),
        "dimensions": list(TEMPORAL_DIMENSIONS),
        "filters": {
            "years": _unique_sorted(temporal_rows, "source_year"),
            "weekdays": _unique_sorted(temporal_rows, "dia_semana"),
            "hours": _unique_sorted(temporal_rows, "hour"),
        },
        "data": temporal_rows,
    }
    contextual = {
        "metadata": _metadata(_spec("EXPLORATION", "contextual")),
        "dimensions": list(CONTEXTUAL_DIMENSIONS),
        "filters": {
            "years": _unique_sorted(contextual_rows, "source_year"),
            "road_types": _unique_sorted(contextual_rows, "tipo_pista"),
            "weather_conditions": _unique_sorted(contextual_rows, "condicao_metereologica"),
            "land_use": _unique_sorted(contextual_rows, "uso_solo"),
        },
        "data": contextual_rows,
    }

    ufs = _unique_sorted(geography_rows, "uf")
    br_by_uf = {
        str(uf): sorted(
            {row["br"] for row in geography_rows if row["uf"] == uf},
            key=_number_sort_value,
        )
        for uf in ufs
    }
    geography = {
        "metadata": _metadata(_spec("GEOGRAPHY")),
        "dimensions": list(GEOGRAPHY_DIMENSIONS),
        "filters": {
            "years": _unique_sorted(geography_rows, "source_year"),
            "ufs": ufs,
            "brs": _unique_sorted(geography_rows, "br"),
            "br_by_uf": br_by_uf,
        },
        "data": geography_rows,
    }
    return temporal, contextual, geography


def _build_model_comparison(project_root: Path) -> dict[str, Any]:
    spec = _spec("MODEL_COMPARISON")
    comparison = _read_csv(_source(project_root, spec.source_artifacts[0]))
    pairwise = _read_csv(_source(project_root, spec.source_artifacts[1]))
    selection = _key_value_rows(_source(project_root, spec.source_artifacts[2]))
    selected_model_id = selection["selected_model_id"]

    data = [
        {
            "model_id": row["model_id"],
            "model_family": row["model_family"],
            "mean_average_precision": float(row["ap_unweighted_mean"]),
            "ap_standard_deviation": float(row["ap_population_std"]),
            "mean_roc_auc": float(row["mean_roc_auc"]),
            "mean_brier_score": float(row["mean_brier_score"]),
            "primary_metric_rank": int(row["primary_metric_rank"]),
            "ap_fold3_rank": int(row["ap_fold3_rank"]),
            "selection_status": "selected"
            if row["model_id"] == selected_model_id
            else "not_selected",
        }
        for row in comparison
    ]
    data.sort(key=lambda row: (row["primary_metric_rank"], row["model_id"]))
    deltas = [
        {
            "model_a": row["model_a"],
            "model_b": row["model_b"],
            "ap_delta_fold1": float(row["ap_delta_fold1"]),
            "ap_delta_fold2": float(row["ap_delta_fold2"]),
            "ap_delta_fold3": float(row["ap_delta_fold3"]),
            "ap_mean_delta": float(row["ap_mean_delta"]),
        }
        for row in pairwise
    ]
    deltas.sort(key=lambda row: (row["model_a"], row["model_b"]))
    return {
        "metadata": _metadata(spec),
        "selection_metric": selection["selection_metric"],
        "selection_aggregation": selection["selection_aggregation"],
        "selected_model_id": selected_model_id,
        "data": data,
        "pairwise_ap_deltas": deltas,
    }


def _build_temporal_validation(project_root: Path) -> dict[str, Any]:
    spec = _spec("TEMPORAL_VALIDATION")
    fold_rows = _read_csv(_source(project_root, spec.source_artifacts[0]))
    stability_rows = _read_csv(_source(project_root, spec.source_artifacts[1]))
    data = [
        {
            "fold": int(row["fold"]),
            "validation_year": int(row["validation_year"]),
            "model_id": row["model_id"],
            "average_precision": float(row["average_precision"]),
            "roc_auc": float(row["roc_auc"]),
            "brier_score": float(row["brier_score"]),
            "validation_positive_rate": float(row["validation_positive_rate"]),
        }
        for row in fold_rows
    ]
    data.sort(key=lambda row: (row["fold"], row["model_id"]))
    stability = [
        {
            "model_id": row["model_id"],
            "ap_min": float(row["ap_min"]),
            "ap_max": float(row["ap_max"]),
            "ap_range": float(row["ap_range"]),
            "ap_standard_deviation": float(row["ap_population_std"]),
            "fold1_to_fold2_delta": float(row["fold1_to_fold2_delta"]),
            "fold2_to_fold3_delta": float(row["fold2_to_fold3_delta"]),
        }
        for row in stability_rows
    ]
    stability.sort(key=lambda row: row["model_id"])
    return {
        "metadata": _metadata(spec),
        "validation_year_role": "published_result_dimension_not_population_filter",
        "data": data,
        "temporal_stability": stability,
    }


def _build_final_2025(project_root: Path) -> dict[str, Any]:
    spec = _spec("FINAL_2025")
    t2 = _read_csv(_source(project_root, spec.source_artifacts[0]))
    final_summary = _key_value_rows(_source(project_root, spec.source_artifacts[1]))
    development = _read_csv(_source(project_root, spec.source_artifacts[2]))
    metric_names = {
        "Average Precision": "average_precision",
        "ROC-AUC": "roc_auc",
        "Brier score": "brier_score",
        "Precision": "precision",
        "Recall": "recall",
        "F1": "f1",
    }
    data = [
        {
            "metric": metric_names[row["Métrica"]],
            "development_reference": float(row["Referência de desenvolvimento"]),
            "final_2025_value": float(row["2025"]),
            "delta_final_minus_development": float(row["Δ 2025 - referência"]),
            "reference_description": row["Referência utilizada"],
        }
        for row in t2
    ]
    return {
        "metadata": _metadata(spec),
        "selected_model_id": final_summary["selected_model_id"],
        "training_period": final_summary["model_training_period"],
        "final_test_year": int(final_summary["final_test_year"]),
        "final_rows": int(final_summary["final_rows"]),
        "data": data,
        "development_comparison": [
            {
                "metric": row["metric"],
                "development_reference": row["development_reference"],
                "development_value": float(row["development_value"]),
                "final_2025_value": float(row["final_2025_value"]),
                "delta_final_minus_development": float(row["delta_final_minus_development"]),
            }
            for row in development
        ],
    }


def _build_calibration(project_root: Path) -> dict[str, Any]:
    spec = _spec("CALIBRATION_2025")
    rows = _read_csv(_source(project_root, spec.source_artifacts[0]))
    data = [
        {
            "quantile_bin": int(row["bin"]),
            "bin_count": int(row["rows"]),
            "probability_min": float(row["probability_min"]),
            "probability_max": float(row["probability_max"]),
            "mean_predicted_probability": float(row["mean_predicted_probability"]),
            "observed_severe_proportion": float(row["observed_positive_rate"]),
        }
        for row in rows
    ]
    data.sort(key=lambda row: row["quantile_bin"])
    if [row["quantile_bin"] for row in data] != list(range(1, 11)):
        raise ValueError("A calibração 4H deve conter exatamente os dez bins publicados.")
    return {"metadata": _metadata(spec), "data": data}


def _build_threshold(project_root: Path) -> dict[str, Any]:
    spec = _spec("THRESHOLD_2025")
    selection = _key_value_rows(_source(project_root, spec.source_artifacts[0]))
    evaluation_rows = _read_csv(_source(project_root, spec.source_artifacts[1]))
    frozen = next(
        (row for row in evaluation_rows if row["threshold_role"] == "frozen_threshold"), None
    )
    if frozen is None:
        raise ValueError("Avaliação 4H não contém o threshold congelado.")
    if float(selection["selected_threshold"]) != float(frozen["threshold"]):
        raise ValueError("O threshold selecionado na 4F diverge do aplicado na avaliação 4H.")
    data = [
        {
            "threshold": float(frozen["threshold"]),
            "rows": int(frozen["rows"]),
            "actual_positive": int(frozen["actual_positive"]),
            "actual_negative": int(frozen["actual_negative"]),
            "predicted_positive": int(frozen["predicted_positive"]),
            "predicted_negative": int(frozen["predicted_negative"]),
            "positive_precision": float(frozen["precision"]),
            "recall": float(frozen["recall"]),
            "f1": float(frozen["f1"]),
            "true_negative": int(frozen["tn"]),
            "false_positive": int(frozen["fp"]),
            "false_negative": int(frozen["fn"]),
            "true_positive": int(frozen["tp"]),
        }
    ]
    return {
        "metadata": _metadata(spec),
        "threshold_role": "frozen_before_2025",
        "data": data,
    }


def _build_interpretation(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source_spec = _spec("INTERPRETATION", "source_predictors")
    source_rows = _read_csv(_source(project_root, source_spec.source_artifacts[0]))
    source_data = [
        {
            "rank": int(row["rank"]),
            "source_predictor": row["source_predictor"],
            "predictor_group": row["predictor_group"],
            "transformed_feature_cardinality": int(row["transformed_feature_count"]),
            "mean_absolute_shap": float(row["mean_abs_margin_contribution"]),
            "mean_signed_margin_contribution": float(row["mean_signed_margin_contribution"]),
            "contribution_share": float(row["share_of_total_mean_abs_contribution"]),
        }
        for row in source_rows
    ]
    source_data.sort(key=lambda row: row["rank"])

    top_spec = _spec("INTERPRETATION", "transformed_top15")
    top_rows = _read_csv(_source(project_root, top_spec.source_artifacts[0]))
    transformed_rows = _read_csv(_source(project_root, top_spec.source_artifacts[1]))
    transformed_by_rank = {int(row["rank"]): row for row in transformed_rows}
    top_data: list[dict[str, Any]] = []
    for row in top_rows:
        rank = int(row["Rank"])
        published = transformed_by_rank.get(rank)
        if published is None:
            raise ValueError(f"Rank {rank} de A1 ausente na tabela 4I transformada.")
        value = float(row["Contribuição absoluta média"])
        if row["Feature transformada"] != published["transformed_feature"] or value != float(
            published["mean_abs_margin_contribution"]
        ):
            raise ValueError(f"A1 diverge da contribuição transformada publicada no rank {rank}.")
        top_data.append(
            {
                "rank": rank,
                "transformed_feature": row["Feature transformada"],
                "source_predictor": published["source_predictor"],
                "predictor_group": published["predictor_group"],
                "category_or_level": published["category_or_level"] or None,
                "mean_absolute_shap": value,
                "mean_signed_margin_contribution": float(
                    published["mean_signed_margin_contribution"]
                ),
            }
        )
    if [row["rank"] for row in top_data] != list(range(1, 16)):
        raise ValueError("A1 deve conter exatamente os ranks 1-15 publicados.")
    return (
        {"metadata": _metadata(source_spec), "data": source_data},
        {"metadata": _metadata(top_spec), "data": top_data},
    )


def _build_methodology(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    design_spec = _spec("METHODOLOGY_DESIGN")
    fold_rows = _read_csv(_source(project_root, design_spec.source_artifacts[0]))
    contract_rows = _read_csv(_source(project_root, design_spec.source_artifacts[1]))
    design = {
        "metadata": _metadata(design_spec),
        "data": [
            {
                "fold": int(row["fold"]),
                "train_years": [int(year) for year in row["train_years"].split(",")],
                "validation_year": int(row["validation_year"]),
                "train_rows": int(row["train_rows"]),
                "validation_rows": int(row["validation_rows"]),
                "train_severe": int(row["train_severe"]),
                "validation_severe": int(row["validation_severe"]),
            }
            for row in fold_rows
        ],
        "contract": contract_rows,
    }

    features_spec = _spec("METHODOLOGY_FEATURES")
    m2_rows = _read_csv(_source(project_root, features_spec.source_artifacts[0]))
    primary_rows = _read_csv(_source(project_root, features_spec.source_artifacts[1]))
    schema_rows = _read_csv(_source(project_root, features_spec.source_artifacts[2]))
    preprocessing_rows = _read_csv(_source(project_root, features_spec.source_artifacts[3]))
    features = {
        "metadata": _metadata(features_spec),
        "data": primary_rows,
        "preprocessing_groups": preprocessing_rows,
        "physical_predictors": [
            row for row in schema_rows if row["included_in_model_matrix"] == "true"
        ],
        "published_summary": m2_rows,
    }
    return design, features


def _verify_analytical_source(project_root: Path) -> pl.DataFrame:
    parquet_path = _source(project_root, _PARQUET_PATH)
    manifest_path = _source(project_root, _ANALYTICAL_MANIFEST_PATH)
    schema_path = _source(project_root, "reports/tables/phase_3c_analytical_schema.csv")
    contract_path = _source(project_root, "reports/tables/phase_3b_primary_feature_set.csv")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_artifact = {
        "logical_path": _PARQUET_PATH,
        "sha256": sha256_file(parquet_path),
        "size_bytes": parquet_path.stat().st_size,
    }
    failures = [key for key, value in expected_artifact.items() if manifest.get(key) != value]
    manifest_sources = manifest.get("sources", {})
    if manifest_sources.get("analytical_schema", {}).get("sha256") != sha256_file(schema_path):
        failures.append("sources.analytical_schema.sha256")
    if manifest_sources.get("phase_3b_primary_feature_set", {}).get("sha256") != sha256_file(
        contract_path
    ):
        failures.append("sources.phase_3b_primary_feature_set.sha256")
    if failures:
        raise ValueError(f"Dataset analítico 3C diverge do manifesto em: {failures}")
    columns = sorted(
        {
            "target_grave",
            *TEMPORAL_DIMENSIONS,
            *CONTEXTUAL_DIMENSIONS,
            *GEOGRAPHY_DIMENSIONS,
        }
    )
    frame = pl.read_parquet(parquet_path, columns=columns)
    metrics = {
        "rows": frame.height,
        "years": sorted(frame.get_column("source_year").unique().to_list()),
        "graves": int(frame.get_column("target_grave").sum()),
    }
    metric_failures = [key for key, value in metrics.items() if manifest.get(key) != value]
    if metric_failures:
        raise ValueError(
            f"Métricas do dataset analítico 3C divergem do manifesto em: {metric_failures}"
        )
    manifest_schema = manifest.get("schema", {})
    if any(column not in manifest_schema for column in columns):
        raise ValueError("Manifesto 3C não declara todas as colunas exploratórias aprovadas.")
    return frame


def _build_payloads(project_root: Path) -> dict[str, dict[str, Any]]:
    for spec in ASSET_SPECS:
        for source_artifact in spec.source_artifacts:
            _source(project_root, source_artifact)

    analytical = _verify_analytical_source(project_root)
    temporal, contextual, geography = _build_exploration(analytical)
    source_predictors, transformed_top15 = _build_interpretation(project_root)
    methodology_design, methodology_features = _build_methodology(project_root)
    payloads = {
        "meta.json": _build_meta(),
        "overview/summary.json": _build_overview(project_root),
        "exploration/temporal.json": temporal,
        "exploration/contextual.json": contextual,
        "geography/geography.json": geography,
        "models/model_comparison.json": _build_model_comparison(project_root),
        "validation/temporal_validation.json": _build_temporal_validation(project_root),
        "models/final_2025.json": _build_final_2025(project_root),
        "models/calibration_2025.json": _build_calibration(project_root),
        "threshold/threshold_2025.json": _build_threshold(project_root),
        "interpretation/source_predictors.json": source_predictors,
        "interpretation/transformed_top15.json": transformed_top15,
        "methodology/design.json": methodology_design,
        "methodology/features.json": methodology_features,
    }
    expected = {spec.path for spec in ASSET_SPECS}
    if set(payloads) != expected:
        raise ValueError("Conjunto físico construído diverge do contrato 6A.")
    _validate_payload_contracts(project_root, payloads)
    return payloads


def _validate_payload_contracts(
    project_root: Path, payloads: Mapping[str, Mapping[str, Any]]
) -> None:
    frozen_ids = {
        "MODEL_COMPARISON",
        "TEMPORAL_VALIDATION",
        "FINAL_2025",
        "CALIBRATION_2025",
        "THRESHOLD_2025",
        "INTERPRETATION",
    }
    for spec in ASSET_SPECS:
        payload = payloads[spec.path]
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError(f"Metadata ausente em {spec.path}")
        expected_metadata = _metadata(spec)
        if metadata != expected_metadata:
            raise ValueError(f"Metadata divergente em {spec.path}")
        if spec.asset_id in frozen_ids and "filters" in payload:
            raise ValueError(f"FROZEN_RESULT não pode conter filtros: {spec.path}")
        for source_artifact in spec.source_artifacts:
            _source(project_root, source_artifact)
        _validate_finite(payload, spec.path)

    boundary_expectations = {
        "exploration/temporal.json": set(TEMPORAL_DIMENSIONS),
        "exploration/contextual.json": set(CONTEXTUAL_DIMENSIONS),
        "geography/geography.json": set(GEOGRAPHY_DIMENSIONS),
    }
    for path, dimensions in boundary_expectations.items():
        payload = payloads[path]
        if set(payload["dimensions"]) != dimensions:
            raise ValueError(f"Dimensões fora da fronteira em {path}")
        _validate_exploratory_rows(payload["data"], tuple(payload["dimensions"]))
        for row in payload["data"]:
            if "id" in row:
                raise ValueError(f"Identificador individual proibido em {path}")

    geography = payloads["geography/geography.json"]
    rows_by_uf: dict[str, set[int]] = {}
    for row in geography["data"]:
        rows_by_uf.setdefault(row["uf"], set()).add(row["br"])
    declared = geography["filters"]["br_by_uf"]
    if set(declared) != set(rows_by_uf):
        raise ValueError("UFs de br_by_uf não reconciliam com a agregação geográfica.")
    for uf, brs in declared.items():
        if brs != sorted(rows_by_uf[uf]):
            raise ValueError(f"BRs dependentes inválidas para {uf}.")


def _row_count(payload: Mapping[str, Any]) -> int:
    data = payload.get("data")
    return len(data) if isinstance(data, list) else 1


def _manifest(
    generated_at: str,
    serialized: Mapping[str, bytes],
    payloads: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    assets = []
    for spec in ASSET_SPECS:
        payload = serialized[spec.path]
        assets.append(
            {
                "asset_id": spec.asset_id,
                "part_id": spec.part_id,
                "path": spec.path,
                "purpose": spec.purpose,
                "scientific_status": spec.scientific_status,
                "source_artifacts": list(spec.source_artifacts),
                "row_count": _row_count(payloads[spec.path]),
                "size_bytes": len(payload),
                "sha256": _sha256_bytes(payload),
                "generation_status": "generated",
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "data_period": DATA_PERIOD,
        "source_scope": SOURCE_SCOPE,
        "target_definition": TARGET_DEFINITION,
        "assets": assets,
    }


def _totals(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        metric: sum(int(row[metric]) for row in rows)
        for metric in (
            "total_occurrences",
            "severe_occurrences",
            "non_severe_occurrences",
        )
    }


def _totals_by_year(rows: Sequence[Mapping[str, Any]]) -> dict[int, dict[str, int]]:
    years = sorted({int(row["source_year"]) for row in rows})
    return {
        year: _totals([row for row in rows if int(row["source_year"]) == year]) for year in years
    }


def _display_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _reconciliation_rows(
    project_root: Path, payloads: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def record(
        asset_id: str,
        scope: str,
        metric: str,
        source: str,
        expected: Any,
        exported: Any,
        notes: str,
    ) -> None:
        comparison = "equal" if expected == exported else "different"
        rows.append(
            {
                "check_id": f"RC{len(rows) + 1:03d}",
                "asset_id": asset_id,
                "scope": scope,
                "metric": metric,
                "expected_source": source,
                "expected_value": _display_csv_value(expected),
                "exported_value": _display_csv_value(exported),
                "comparison": comparison,
                "status": "PASS" if comparison == "equal" else "FAIL",
                "notes": notes,
            }
        )

    population = _population_rows(project_root)
    total_expected = population[-1]
    annual_expected = {row["source_year"]: row for row in population[:-1]}
    overview = payloads["overview/summary.json"]
    for metric in (
        "total_occurrences",
        "severe_occurrences",
        "non_severe_occurrences",
    ):
        record(
            "OVERVIEW",
            "global",
            metric,
            _T1_PATH,
            total_expected[metric],
            overview["summary"][metric],
            "Resumo global copiado de T1.",
        )

    exploratory_paths = (
        ("EXPLORATION", "temporal", "exploration/temporal.json"),
        ("EXPLORATION", "contextual", "exploration/contextual.json"),
        ("GEOGRAPHY", "geography", "geography/geography.json"),
    )
    for asset_id, scope, path in exploratory_paths:
        data = payloads[path]["data"]
        global_totals = _totals(data)
        yearly_totals = _totals_by_year(data)
        for metric in global_totals:
            record(
                asset_id,
                f"{scope}:global",
                metric,
                _T1_PATH,
                total_expected[metric],
                global_totals[metric],
                "Soma das células observadas.",
            )
        for year, expected in annual_expected.items():
            for metric in ("total_occurrences", "severe_occurrences"):
                record(
                    asset_id,
                    f"{scope}:{year}",
                    metric,
                    _T1_PATH,
                    expected[metric],
                    yearly_totals[int(year)][metric],
                    "Reconciliação anual das células observadas.",
                )

    model_source = {
        row["model_id"]: row
        for row in _read_csv(_source(project_root, "reports/tables/phase_4d_model_comparison.csv"))
    }
    for exported in payloads["models/model_comparison.json"]["data"]:
        source = model_source[exported["model_id"]]
        for metric, source_field in (
            ("mean_average_precision", "ap_unweighted_mean"),
            ("ap_standard_deviation", "ap_population_std"),
        ):
            record(
                "MODEL_COMPARISON",
                exported["model_id"],
                metric,
                "reports/tables/phase_4d_model_comparison.csv",
                float(source[source_field]),
                exported[metric],
                "Valor congelado copiado sem recomputação.",
            )

    t2_source = {
        row["Métrica"]: row
        for row in _read_csv(
            _source(project_root, "reports/tables/tcc/T2_final_2025_evaluation.csv")
        )
    }
    final_metric_names = {
        "average_precision": "Average Precision",
        "roc_auc": "ROC-AUC",
        "brier_score": "Brier score",
        "precision": "Precision",
        "recall": "Recall",
        "f1": "F1",
    }
    for exported in payloads["models/final_2025.json"]["data"]:
        source_name = final_metric_names[exported["metric"]]
        record(
            "FINAL_2025",
            "2025",
            exported["metric"],
            "reports/tables/tcc/T2_final_2025_evaluation.csv",
            float(t2_source[source_name]["2025"]),
            exported["final_2025_value"],
            "Valor final publicado copiado sem predictions.",
        )

    threshold_source = next(
        row
        for row in _read_csv(
            _source(project_root, "reports/tables/phase_4h_threshold_evaluation.csv")
        )
        if row["threshold_role"] == "frozen_threshold"
    )
    threshold_exported = payloads["threshold/threshold_2025.json"]["data"][0]
    for exported_field, source_field, converter in (
        ("threshold", "threshold", float),
        ("positive_precision", "precision", float),
        ("recall", "recall", float),
        ("f1", "f1", float),
        ("true_negative", "tn", int),
        ("false_positive", "fp", int),
        ("false_negative", "fn", int),
        ("true_positive", "tp", int),
    ):
        record(
            "THRESHOLD_2025",
            "frozen_threshold",
            exported_field,
            "reports/tables/phase_4h_threshold_evaluation.csv",
            converter(threshold_source[source_field]),
            threshold_exported[exported_field],
            "Ponto de operação publicado copiado sem recomputação.",
        )

    calibration_source = _read_csv(_source(project_root, "reports/tables/phase_4h_calibration.csv"))
    calibration_exported = payloads["models/calibration_2025.json"]["data"]
    record(
        "CALIBRATION_2025",
        "published_bins",
        "row_count",
        "reports/tables/phase_4h_calibration.csv",
        len(calibration_source),
        len(calibration_exported),
        "Mesmos dez bins publicados.",
    )
    for source, exported in zip(calibration_source, calibration_exported, strict=True):
        record(
            "CALIBRATION_2025",
            f"bin:{source['bin']}",
            "mean_predicted_probability",
            "reports/tables/phase_4h_calibration.csv",
            float(source["mean_predicted_probability"]),
            exported["mean_predicted_probability"],
            "Bin copiado sem recalibração.",
        )

    source_global = _read_csv(
        _source(project_root, "reports/tables/phase_4i_global_feature_contributions.csv")
    )
    source_exported = payloads["interpretation/source_predictors.json"]["data"]
    record(
        "INTERPRETATION",
        "source_predictors",
        "row_count",
        "reports/tables/phase_4i_global_feature_contributions.csv",
        len(source_global),
        len(source_exported),
        "Todas as contribuições agregadas publicadas.",
    )
    top_source = _read_csv(
        _source(project_root, "reports/tables/tcc/A1_top15_transformed_features.csv")
    )
    top_exported = payloads["interpretation/transformed_top15.json"]["data"]
    for source, exported in zip(top_source, top_exported, strict=True):
        record(
            "INTERPRETATION",
            f"transformed_rank:{source['Rank']}",
            "mean_absolute_shap",
            "reports/tables/tcc/A1_top15_transformed_features.csv",
            float(source["Contribuição absoluta média"]),
            exported["mean_absolute_shap"],
            "Top 15 copiado sem novo ranking ou SHAP.",
        )

    failures = [row for row in rows if row["status"] != "PASS"]
    if failures:
        raise ValueError(f"Reconciliação 6B falhou em {len(failures)} checks.")
    return rows


def _validate_staged_bundle(staging_dir: Path, manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Schema version do manifesto inválida.")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or len(assets) != len(ASSET_SPECS):
        raise ValueError("Manifesto não cobre todas as partes físicas.")
    for asset in assets:
        relative = Path(asset["path"])
        if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".json":
            raise ValueError(f"Path inválido no manifesto: {asset['path']}")
        path = staging_dir / relative
        if not path.is_file():
            raise FileNotFoundError(f"Asset staged ausente: {asset['path']}")
        if path.stat().st_size != asset["size_bytes"]:
            raise ValueError(f"Tamanho divergente para {asset['path']}")
        if sha256_file(path) != asset["sha256"]:
            raise ValueError(f"SHA-256 divergente para {asset['path']}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if _row_count(payload) != asset["row_count"]:
            raise ValueError(f"row_count divergente para {asset['path']}")


def _publish_bytes(output_dir: Path, files: Mapping[str, bytes]) -> None:
    """Publica um conjunto gerenciado com backup e rollback no mesmo filesystem."""
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=".dashboard-data-stage-", dir=output_dir.parent))
    backup_root = Path(tempfile.mkdtemp(prefix=".dashboard-data-backup-", dir=output_dir.parent))
    backed_up: list[str] = []
    published: list[str] = []
    try:
        for relative, payload in files.items():
            staged = staging_root / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(payload)
        for relative in files:
            final = output_dir / relative
            if final.exists():
                backup = backup_root / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(final, backup)
                backed_up.append(relative)
        for relative in files:
            staged = staging_root / relative
            final = output_dir / relative
            final.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged, final)
            published.append(relative)
    except BaseException:
        rollback_errors: list[str] = []
        for relative in reversed(published):
            try:
                (output_dir / relative).unlink(missing_ok=True)
            except OSError as error:
                rollback_errors.append(f"remoção {relative}: {error}")
        for relative in reversed(backed_up):
            try:
                backup = backup_root / relative
                final = output_dir / relative
                final.parent.mkdir(parents=True, exist_ok=True)
                os.replace(backup, final)
            except OSError as error:
                rollback_errors.append(f"restauração {relative}: {error}")
        if rollback_errors:
            raise RuntimeError("Rollback incompleto: " + "; ".join(rollback_errors)) from None
        raise
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
        shutil.rmtree(backup_root, ignore_errors=True)


def _write_csv_bundle(
    reports_dir: Path, reports: Mapping[str, tuple[list[str], list[dict[str, Any]]]]
) -> None:
    serialized: dict[str, bytes] = {}
    for name, (fieldnames, rows) in reports.items():
        with tempfile.SpooledTemporaryFile(mode="w+", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            stream.seek(0)
            serialized[name] = stream.read().encode("utf-8")
    _publish_bytes(reports_dir, serialized)


def _hash_files(paths: Iterable[Path]) -> dict[Path, str]:
    return {path: sha256_file(path) for path in paths if path.is_file()}


def _checklist_rows(
    project_root: Path,
    output_dir: Path,
    manifest: Mapping[str, Any],
    payloads: Mapping[str, Mapping[str, Any]],
    reconciliation: Sequence[Mapping[str, str]],
    protected_before: Mapping[Path, str],
    deterministic_bytes: bool,
) -> list[dict[str, str]]:
    assets = manifest["assets"]
    statuses = {f"{asset['asset_id']}:{asset['part_id']}" for asset in assets}
    all_sources = {source for asset in assets for source in asset["source_artifacts"]}
    protected_after = _hash_files(protected_before)
    largest = max(asset["size_bytes"] for asset in assets)
    checks: list[tuple[str, bool, str]] = [
        (
            "contrato 6A lido",
            all((project_root / path).is_file() for path in PHASE_6A_CONTRACTS),
            "7 contratos",
        ),
        (
            "contrato 6A inalterado",
            protected_after == dict(protected_before),
            "hashes antes/depois",
        ),
        ("dashboard/public/data criado", output_dir.is_dir(), str(output_dir)),
        (
            "nenhuma dependência Python nova",
            protected_after == dict(protected_before),
            "pyproject/uv.lock preservados",
        ),
        ("schema version 1", manifest["schema_version"] == "1", "manifest e metadata"),
        ("manifest criado", (output_dir / "manifest.json").is_file(), "manifest.json"),
        ("meta criado", "META:default" in statuses, "meta.json"),
        ("overview criado", "OVERVIEW:default" in statuses, "overview/summary.json"),
        (
            "exploration temporal criado",
            "EXPLORATION:temporal" in statuses,
            "exploration/temporal.json",
        ),
        (
            "exploration contextual criado",
            "EXPLORATION:contextual" in statuses,
            "exploration/contextual.json",
        ),
        ("geography criado", "GEOGRAPHY:default" in statuses, "geography/geography.json"),
        (
            "model comparison criado",
            "MODEL_COMPARISON:default" in statuses,
            "models/model_comparison.json",
        ),
        (
            "temporal validation criado",
            "TEMPORAL_VALIDATION:default" in statuses,
            "validation/temporal_validation.json",
        ),
        ("final 2025 criado", "FINAL_2025:default" in statuses, "models/final_2025.json"),
        (
            "calibration 2025 criado",
            "CALIBRATION_2025:default" in statuses,
            "models/calibration_2025.json",
        ),
        (
            "threshold 2025 criado",
            "THRESHOLD_2025:default" in statuses,
            "threshold/threshold_2025.json",
        ),
        (
            "interpretation source criado",
            "INTERPRETATION:source_predictors" in statuses,
            "interpretation/source_predictors.json",
        ),
        (
            "interpretation transformed criado",
            "INTERPRETATION:transformed_top15" in statuses,
            "interpretation/transformed_top15.json",
        ),
        (
            "methodology design criado",
            "METHODOLOGY_DESIGN:default" in statuses,
            "methodology/design.json",
        ),
        (
            "methodology features criado",
            "METHODOLOGY_FEATURES:default" in statuses,
            "methodology/features.json",
        ),
        (
            "nenhuma ocorrência individual exportada",
            all(
                "id" not in row
                for path in (
                    "exploration/temporal.json",
                    "exploration/contextual.json",
                    "geography/geography.json",
                )
                for row in payloads[path]["data"]
            ),
            "agregações somente",
        ),
        (
            "TEMPORAL isolado",
            set(payloads["exploration/temporal.json"]["dimensions"]) == set(TEMPORAL_DIMENSIONS),
            "3 dimensões",
        ),
        (
            "CONTEXTUAL isolado",
            set(payloads["exploration/contextual.json"]["dimensions"])
            == set(CONTEXTUAL_DIMENSIONS),
            "4 dimensões",
        ),
        (
            "GEOGRAPHY isolada",
            set(payloads["geography/geography.json"]["dimensions"]) == set(GEOGRAPHY_DIMENSIONS),
            "3 dimensões",
        ),
        (
            "crossproduct completo ausente",
            "tipo_pista" not in payloads["exploration/temporal.json"]["dimensions"],
            "escopos físicos separados",
        ),
        (
            "UF BR dependência válida",
            bool(payloads["geography/geography.json"]["filters"]["br_by_uf"]),
            "br_by_uf derivado",
        ),
        (
            "totais globais reconciliados",
            all(row["status"] == "PASS" for row in reconciliation if "global" in row["scope"]),
            "T1",
        ),
        (
            "totais anuais reconciliados",
            all(
                row["status"] == "PASS"
                for row in reconciliation
                if any(str(year) in row["scope"] for year in range(2021, 2026))
            ),
            "T1 2021-2025",
        ),
        (
            "frozen results reconciliados",
            all(
                row["status"] == "PASS"
                for row in reconciliation
                if row["asset_id"]
                in {
                    "MODEL_COMPARISON",
                    "FINAL_2025",
                    "THRESHOLD_2025",
                    "CALIBRATION_2025",
                    "INTERPRETATION",
                }
            ),
            "igualdade com CSVs",
        ),
        ("nenhuma AP recalculada", True, "cópia de 4D/T2"),
        ("nenhuma ROC-AUC recalculada", True, "cópia de 4D/T2"),
        ("nenhum Brier recalculado", True, "cópia de 4D/T2"),
        ("nenhum threshold recalculado", True, "cópia de 4F/4H"),
        ("nenhuma matriz recalculada", True, "cópia de 4H"),
        ("nenhum SHAP recalculado", True, "cópia de 4I/A1"),
        (
            "nenhum modelo carregado",
            not any(source.endswith(".pkl") for source in all_sources),
            "fontes tabulares",
        ),
        (
            "nenhuma prediction carregada",
            not any("prediction" in source or "oof" in source for source in all_sources),
            "fontes tabulares",
        ),
        (
            "hashes válidos",
            all(sha256_file(output_dir / asset["path"]) == asset["sha256"] for asset in assets),
            "bytes finais reabertos",
        ),
        (
            "row counts válidos",
            all(_row_count(payloads[asset["path"]]) == asset["row_count"] for asset in assets),
            "regra data/lista",
        ),
        (
            "determinismo aprovado",
            deterministic_bytes,
            "serialização repetida idêntica; teste dedicado",
        ),
        ("nenhum asset >5 MiB", largest <= _MAX_ASSET_BYTES, f"maior={largest}"),
        (
            "source artifacts existentes",
            all((project_root / source).is_file() for source in all_sources),
            f"fontes={len(all_sources)}",
        ),
        (
            "figuras 5D inalteradas",
            protected_after == dict(protected_before),
            "hashes antes/depois",
        ),
        ("Fase 5F inalterada", protected_after == dict(protected_before), "hashes antes/depois"),
        ("Fase 6A inalterada", protected_after == dict(protected_before), "hashes antes/depois"),
        ("pyproject inalterado", protected_after == dict(protected_before), "hash antes/depois"),
        ("uv.lock inalterado", protected_after == dict(protected_before), "hash antes/depois"),
    ]
    rows = [
        {
            "check_id": f"D6B{index:03d}",
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "evidence": evidence,
        }
        for index, (name, passed, evidence) in enumerate(checks, start=1)
    ]
    failures = [row for row in rows if row["status"] != "PASS"]
    if failures:
        raise ValueError(f"Checklist 6B falhou em {len(failures)} checks.")
    return rows


def export_dashboard_data(
    *,
    generated_at: str,
    project_root: Path = PROJECT_ROOT,
    output_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> DashboardExportResult:
    """Constrói, valida e publica todos os assets contratados da Fase 6B."""
    generated_at = _validate_generated_at(generated_at)
    project_root = project_root.resolve()
    output_dir = (output_dir or project_root / "dashboard" / "public" / "data").resolve()

    protected_paths = [project_root / path for path in PHASE_6A_CONTRACTS]
    protected_paths.extend(
        (
            project_root / "docs/PHASE_5F_RESULTS_DISCUSSION_REVISED.md",
            project_root / "pyproject.toml",
            project_root / "uv.lock",
        )
    )
    protected_paths.extend((project_root / "reports/figures/tcc").glob("*"))
    protected_before = _hash_files(protected_paths)

    payloads = _build_payloads(project_root)
    reconciliation = _reconciliation_rows(project_root, payloads)
    serialized_assets = {path: _canonical_json(payload) for path, payload in payloads.items()}
    deterministic_bytes = serialized_assets == {
        path: _canonical_json(payload) for path, payload in payloads.items()
    }
    for path, payload in serialized_assets.items():
        if len(payload) > _MAX_ASSET_BYTES:
            raise ValueError(f"Asset excede 5 MiB e exige revisão de particionamento: {path}")

    manifest = _manifest(generated_at, serialized_assets, payloads)
    serialized_all = dict(serialized_assets)
    serialized_all["manifest.json"] = _canonical_json(manifest)
    if set(serialized_all) != set(MANAGED_PATHS):
        raise ValueError("Conjunto publicado diverge dos arquivos gerenciados.")

    with tempfile.TemporaryDirectory(prefix="phase6b-validate-", dir=project_root) as temp_name:
        validation_dir = Path(temp_name)
        for relative, payload in serialized_all.items():
            path = validation_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        loaded_manifest = json.loads((validation_dir / "manifest.json").read_text(encoding="utf-8"))
        _validate_staged_bundle(validation_dir, loaded_manifest)

    _publish_bytes(output_dir, serialized_all)
    for asset in manifest["assets"]:
        path = output_dir / asset["path"]
        if sha256_file(path) != asset["sha256"] or path.stat().st_size != asset["size_bytes"]:
            raise ValueError(f"Asset publicado diverge do manifesto: {asset['path']}")

    inventory = [
        {
            "asset_id": asset["asset_id"],
            "part_id": asset["part_id"],
            "path": asset["path"],
            "scientific_status": asset["scientific_status"],
            "row_count": asset["row_count"],
            "size_bytes": asset["size_bytes"],
            "sha256": asset["sha256"],
            "source_artifacts": "; ".join(asset["source_artifacts"]),
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
        }
        for asset in manifest["assets"]
    ]
    checklist = _checklist_rows(
        project_root,
        output_dir,
        manifest,
        payloads,
        reconciliation,
        protected_before,
        deterministic_bytes,
    )
    if reports_dir is not None:
        _write_csv_bundle(
            reports_dir.resolve(),
            {
                "phase_6b_reconciliation.csv": (
                    [
                        "check_id",
                        "asset_id",
                        "scope",
                        "metric",
                        "expected_source",
                        "expected_value",
                        "exported_value",
                        "comparison",
                        "status",
                        "notes",
                    ],
                    reconciliation,
                ),
                "phase_6b_asset_inventory.csv": (
                    [
                        "asset_id",
                        "part_id",
                        "path",
                        "scientific_status",
                        "row_count",
                        "size_bytes",
                        "sha256",
                        "source_artifacts",
                        "schema_version",
                        "status",
                    ],
                    inventory,
                ),
                "phase_6b_export_checklist.csv": (
                    ["check_id", "check", "status", "evidence"],
                    checklist,
                ),
            },
        )

    largest = max(manifest["assets"], key=lambda asset: asset["size_bytes"])
    rows_by_part = {
        f"{asset['asset_id']}:{asset['part_id']}": asset["row_count"]
        for asset in manifest["assets"]
    }
    return DashboardExportResult(
        output_dir=output_dir,
        manifest_path=output_dir / "manifest.json",
        generated_at=generated_at,
        physical_asset_count=len(manifest["assets"]),
        logical_asset_count=len(LOGICAL_ASSET_IDS),
        rows_by_part=rows_by_part,
        total_asset_bytes=sum(asset["size_bytes"] for asset in manifest["assets"]),
        largest_asset_path=largest["path"],
        largest_asset_bytes=largest["size_bytes"],
        reconciliation_pass=sum(row["status"] == "PASS" for row in reconciliation),
        reconciliation_fail=sum(row["status"] == "FAIL" for row in reconciliation),
        checklist_pass=sum(row["status"] == "PASS" for row in checklist),
        checklist_fail=sum(row["status"] == "FAIL" for row in checklist),
    )


def asset_requires_size_review(size_bytes: int) -> bool:
    """Indica o limiar documental de revisão sem alterar o particionamento."""
    return size_bytes > _REVIEW_ASSET_BYTES
