from __future__ import annotations

import os
import platform
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import sklearn
import xgboost
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted
from xgboost import XGBClassifier

from tcc_prf_severity.config import (
    PRIMARY_ANALYTICAL_PARQUET_PATH,
    PRIMARY_ANALYTICAL_SCHEMA_PATH,
    PROCESSED_DIR,
    PROJECT_ROOT,
    TABLES_DIR,
)
from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.modeling.experimental_design import (
    DEVELOPMENT_YEARS,
    METADATA_COLUMNS,
    TARGET_COLUMN,
    load_predictors_from_schema,
)
from tcc_prf_severity.modeling.final_refit import (
    EXPECTED_BOOSTING_ROUNDS,
    EXPECTED_PREDICTOR_COUNT,
    FINAL_PIPELINE_PATH,
    FROZEN_THRESHOLD_TEXT,
    load_final_pipeline,
)
from tcc_prf_severity.modeling.model_comparison import XGBOOST_MODEL_ID
from tcc_prf_severity.modeling.preprocessing import PreprocessingGroups, load_preprocessing_groups
from tcc_prf_severity.modeling.threshold_selection import (
    REFERENCE_THRESHOLD,
    SELECTED_MODEL_FAMILY,
    ThresholdMetrics,
    evaluate_threshold,
)
from tcc_prf_severity.modeling.xgboost_baseline import (
    extract_xgboost_positive_probability,
)

FINAL_TEST_YEAR = 2025
EXPECTED_FINAL_ROWS = 72_529
EXPECTED_FINAL_POSITIVE = 20_493
EXPECTED_MODEL_SHA256 = "c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351"
FINAL_PREDICTIONS_PATH = PROCESSED_DIR / "phase_4h_final_2025_predictions.parquet"
CALIBRATION_BINS = 10

PHASE_4G_DOCUMENT_PATH = PROJECT_ROOT / "docs" / "PHASE_4G_FINAL_REFIT.md"
PHASE_4F_DOCUMENT_PATH = PROJECT_ROOT / "docs" / "PHASE_4F_THRESHOLD_SELECTION.md"
PHASE_4E_DOCUMENT_PATH = PROJECT_ROOT / "docs" / "PHASE_4E_MODEL_SELECTION.md"
PREMODELING_ACCEPTANCE_PATH = PROJECT_ROOT / "docs" / "PHASE_3_PREMODELING_ACCEPTANCE.md"


@dataclass(frozen=True)
class InternalReferences:
    ap_mean: float
    ap_fold3: float
    mean_roc_auc: float
    mean_brier_score: float
    oof_precision: float
    oof_recall: float
    oof_f1: float


@dataclass(frozen=True)
class FinalEvaluationInputs:
    final_model_manifest: dict[str, str]
    refit_checklist: pl.DataFrame
    threshold_selection: dict[str, str]
    model_selection: dict[str, str]
    model_comparison: pl.DataFrame
    fold_metrics: pl.DataFrame
    final_partition: dict[str, Any]


@dataclass(frozen=True)
class ProbabilityMetrics:
    average_precision: float
    roc_auc: float
    brier_score: float


@dataclass(frozen=True)
class FinalEvaluationResult:
    model_sha256: str
    probability_metrics: ProbabilityMetrics
    frozen_threshold_metrics: ThresholdMetrics
    reference_threshold_metrics: ThresholdMetrics
    references: InternalReferences
    predictions: pl.DataFrame
    predictions_path: Path
    predictions_sha256: str
    predictions_size_bytes: int
    final_evaluation: pl.DataFrame
    threshold_evaluation: pl.DataFrame
    development_comparison: pl.DataFrame
    calibration: pl.DataFrame
    checklist: pl.DataFrame


@dataclass(frozen=True)
class FinalEvaluationRun:
    result: FinalEvaluationResult
    table_paths: tuple[Path, ...]


def _key_value_mapping(table: pl.DataFrame, source: str) -> dict[str, str]:
    if not {"key", "value"}.issubset(table.columns):
        raise ValueError(f"Tabela key/value inválida: {source}.")
    selected = table.select("key", "value")
    if selected.get_column("key").n_unique() != selected.height:
        raise ValueError(f"Chaves duplicadas em {source}.")
    return {str(row["key"]): str(row["value"]) for row in selected.iter_rows(named=True)}


def load_final_evaluation_inputs(tables_dir: Path = TABLES_DIR) -> FinalEvaluationInputs:
    paths = {
        "manifesto 4G": tables_dir / "phase_4g_final_model_manifest.csv",
        "checklist 4G": tables_dir / "phase_4g_refit_checklist.csv",
        "threshold 4F": tables_dir / "phase_4f_threshold_selection.csv",
        "seleção 4E": tables_dir / "phase_4e_model_selection.csv",
        "comparação 4D": tables_dir / "phase_4d_model_comparison.csv",
        "folds XGBoost 4C": tables_dir / "phase_4c_xgboost_fold_metrics.csv",
        "partições 3D": tables_dir / "phase_3d_partition_summary.csv",
        "documento 4G": PHASE_4G_DOCUMENT_PATH,
        "documento 4F": PHASE_4F_DOCUMENT_PATH,
        "documento 4E": PHASE_4E_DOCUMENT_PATH,
        "aceite pré-modelagem 3F": PREMODELING_ACCEPTANCE_PATH,
    }
    missing = [f"{name}: {path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Fontes autoritativas ausentes antes da avaliação: {missing}")
    partitions = pl.read_csv(paths["partições 3D"])
    final_partition = partitions.filter(
        (pl.col("partition_id") == "final_test") & (pl.col("partition_role") == "final_evaluation")
    )
    if final_partition.height != 1:
        raise ValueError("Partição final 2025 deve possuir exatamente uma linha autoritativa.")
    return FinalEvaluationInputs(
        final_model_manifest=_key_value_mapping(
            pl.read_csv(paths["manifesto 4G"]), str(paths["manifesto 4G"])
        ),
        refit_checklist=pl.read_csv(paths["checklist 4G"]),
        threshold_selection=_key_value_mapping(
            pl.read_csv(paths["threshold 4F"]), str(paths["threshold 4F"])
        ),
        model_selection=_key_value_mapping(
            pl.read_csv(paths["seleção 4E"]), str(paths["seleção 4E"])
        ),
        model_comparison=pl.read_csv(paths["comparação 4D"]),
        fold_metrics=pl.read_csv(paths["folds XGBoost 4C"]),
        final_partition=final_partition.row(0, named=True),
    )


def _derive_internal_references(inputs: FinalEvaluationInputs) -> InternalReferences:
    folds = inputs.fold_metrics.sort("fold")
    required_fold_columns = {
        "fold",
        "validation_year",
        "average_precision",
        "roc_auc",
        "brier_score",
    }
    if not required_fold_columns.issubset(folds.columns) or folds.height != 3:
        raise ValueError("Métricas 4C inválidas para comparação temporal final.")
    if folds["fold"].to_list() != [1, 2, 3] or folds["validation_year"].to_list() != [
        2022,
        2023,
        2024,
    ]:
        raise ValueError("Folds internos 4C divergem do desenho temporal congelado.")
    ap_values = folds["average_precision"].to_numpy()
    roc_values = folds["roc_auc"].to_numpy()
    brier_values = folds["brier_score"].to_numpy()
    derived = {
        "ap_mean": float(np.mean(ap_values)),
        "ap_fold3": float(ap_values[2]),
        "mean_roc_auc": float(np.mean(roc_values)),
        "mean_brier_score": float(np.mean(brier_values)),
    }
    comparison = inputs.model_comparison.filter(pl.col("model_id") == XGBOOST_MODEL_ID)
    if comparison.height != 1:
        raise ValueError("Comparação 4D deve conter exatamente uma linha do XGBoost selecionado.")
    row = comparison.row(0, named=True)
    published = {
        "ap_mean": float(row["ap_unweighted_mean"]),
        "ap_fold3": float(row["ap_fold3"]),
        "mean_roc_auc": float(row["mean_roc_auc"]),
        "mean_brier_score": float(row["mean_brier_score"]),
    }
    if not all(np.isclose(derived[key], published[key], rtol=0.0, atol=1e-15) for key in derived):
        raise ValueError(f"Referências internas 4C/4D não reconciliam: {derived} != {published}.")
    threshold = inputs.threshold_selection
    return InternalReferences(
        ap_mean=derived["ap_mean"],
        ap_fold3=derived["ap_fold3"],
        mean_roc_auc=derived["mean_roc_auc"],
        mean_brier_score=derived["mean_brier_score"],
        oof_precision=float(threshold["selected_precision"]),
        oof_recall=float(threshold["selected_recall"]),
        oof_f1=float(threshold["selected_f1"]),
    )


def validate_pre_evaluation_sources(inputs: FinalEvaluationInputs) -> InternalReferences:
    manifest = inputs.final_model_manifest
    expected_manifest = {
        "refit_status": "completed",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "training_period": "2021-2024",
        "predictor_count": str(EXPECTED_PREDICTOR_COUNT),
        "completed_boosting_rounds": str(EXPECTED_BOOSTING_ROUNDS),
        "all_rounds_completed": "true",
        "transformed_feature_count": "226",
        "threshold_source": "phase_4f",
        "frozen_threshold": FROZEN_THRESHOLD_TEXT,
        "model_artifact_path": FINAL_PIPELINE_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "model_artifact_sha256": EXPECTED_MODEL_SHA256,
        "final_test_year": "2025_reserved",
        "final_test_used": "false",
        "final_evaluation_performed": "false",
        "hyperparameter_tuning": "false",
        "early_stopping": "false",
    }
    manifest_divergences = {
        key: (manifest.get(key), expected)
        for key, expected in expected_manifest.items()
        if manifest.get(key) != expected
    }
    expected_4e = {
        "selection_status": "selected",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "final_test_used": "false",
        "refit_performed": "false",
    }
    expected_4f = {
        "selection_status": "selected",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "selected_threshold": FROZEN_THRESHOLD_TEXT,
        "final_test_used": "false",
        "refit_performed": "false",
    }
    selection_divergences = {
        f"4E.{key}": (inputs.model_selection.get(key), expected)
        for key, expected in expected_4e.items()
        if inputs.model_selection.get(key) != expected
    }
    selection_divergences.update(
        {
            f"4F.{key}": (inputs.threshold_selection.get(key), expected)
            for key, expected in expected_4f.items()
            if inputs.threshold_selection.get(key) != expected
        }
    )
    if manifest_divergences or selection_divergences:
        raise ValueError(
            "Estado congelado incompatível com a avaliação final: "
            f"manifesto={manifest_divergences}; seleções={selection_divergences}."
        )
    if not {"status"}.issubset(inputs.refit_checklist.columns):
        raise ValueError("Checklist 4G sem status.")
    if inputs.refit_checklist.height != 16 or set(inputs.refit_checklist["status"]) != {"PASS"}:
        raise ValueError("Checklist 4G não está integralmente aprovado.")
    partition = inputs.final_partition
    observed_partition = {
        "years": str(partition.get("years")),
        "rows": int(partition.get("rows", -1)),
        "severe": int(partition.get("severe", -1)),
        "non_severe": int(partition.get("non_severe", -1)),
    }
    expected_partition = {
        "years": str(FINAL_TEST_YEAR),
        "rows": EXPECTED_FINAL_ROWS,
        "severe": EXPECTED_FINAL_POSITIVE,
        "non_severe": EXPECTED_FINAL_ROWS - EXPECTED_FINAL_POSITIVE,
    }
    if observed_partition != expected_partition:
        raise ValueError(
            "Partição final 3D divergente: "
            f"observado={observed_partition}; esperado={expected_partition}."
        )
    return _derive_internal_references(inputs)


def _validate_runtime_versions(manifest: dict[str, str]) -> None:
    observed = {
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "xgboost_version": xgboost.__version__,
        "polars_version": pl.__version__,
    }
    expected = {key: manifest.get(key) for key in observed}
    if observed != expected:
        raise RuntimeError(
            "Versões incompatíveis com a materialização 4G: "
            f"observado={observed}; esperado={expected}."
        )


def load_validated_frozen_pipeline(
    manifest: dict[str, str],
    project_root: Path = PROJECT_ROOT,
) -> tuple[Pipeline, Path]:
    relative_path = manifest.get("model_artifact_path")
    expected_sha256 = manifest.get("model_artifact_sha256")
    if relative_path is None or expected_sha256 is None:
        raise ValueError("Manifesto 4G não registra caminho e SHA do pipeline.")
    path = project_root / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Pipeline congelado 4G ausente: {path}")
    observed_sha256 = sha256_file(path)
    if observed_sha256 != expected_sha256:
        raise ValueError(
            "SHA-256 do pipeline diverge antes do load: "
            f"esperado={expected_sha256}; observado={observed_sha256}."
        )
    pipeline = load_final_pipeline(path, expected_sha256)
    _validate_runtime_versions(manifest)
    check_is_fitted(pipeline)
    classifier = pipeline.named_steps.get("classifier")
    preprocessor = pipeline.named_steps.get("preprocessor")
    if not isinstance(classifier, XGBClassifier) or not isinstance(preprocessor, ColumnTransformer):
        raise TypeError("Pipeline 4G não preservou XGBClassifier e preprocessor contratados.")
    if classifier.classes_.tolist() != [0, 1]:
        raise ValueError("Classes do pipeline congelado devem ser exatamente [0, 1].")
    completed_rounds = int(classifier.get_booster().num_boosted_rounds())
    if completed_rounds != int(manifest["completed_boosting_rounds"]):
        raise ValueError("Rounds do pipeline divergem do manifesto 4G.")
    transformed_features = len(preprocessor.get_feature_names_out())
    if transformed_features != int(manifest["transformed_feature_count"]):
        raise ValueError("Dimensão transformada diverge do manifesto 4G.")
    return pipeline, path


def load_final_holdout(
    analytical_path: Path,
    predictors: tuple[str, ...],
) -> pl.DataFrame:
    if not analytical_path.is_file():
        raise FileNotFoundError(f"Dataset analítico 3C ausente: {analytical_path}")
    columns = ("id", "source_year", TARGET_COLUMN, *predictors)
    try:
        return (
            pl.scan_parquet(analytical_path)
            .filter(pl.col("source_year") == FINAL_TEST_YEAR)
            .select(columns)
            .collect()
        )
    except Exception as error:
        raise ValueError("Não foi possível materializar exclusivamente o holdout 2025.") from error


def validate_final_holdout(
    holdout: pl.DataFrame,
    groups: PreprocessingGroups,
    partition: dict[str, Any],
) -> None:
    expected_columns = {"id", "source_year", TARGET_COLUMN, *groups.predictors}
    missing = sorted(expected_columns - set(holdout.columns))
    unexpected = sorted(set(holdout.columns) - expected_columns)
    failures: list[str] = []
    if missing or unexpected:
        failures.append(f"colunas ausentes={missing}; inesperadas={unexpected}")
    years = set(holdout["source_year"].unique().to_list())
    if years != {FINAL_TEST_YEAR}:
        failures.append(f"holdout deve conter somente 2025, observado={sorted(years)}")
    if set(DEVELOPMENT_YEARS) & years:
        failures.append("anos 2021-2024 estão proibidos no conjunto final")
    if holdout.height != int(partition["rows"]):
        failures.append(
            f"linhas não reconciliam: holdout={holdout.height}; contrato={partition['rows']}"
        )
    if holdout["id"].n_unique() != holdout.height:
        failures.append("IDs do holdout não são únicos")
    target = holdout[TARGET_COLUMN]
    if target.dtype != pl.Boolean or target.null_count() > 0:
        failures.append("target_grave deve ser booleano e não nulo")
    elif int(target.sum()) != int(partition["severe"]):
        failures.append(
            f"graves não reconciliam: holdout={int(target.sum())}; contrato={partition['severe']}"
        )
    if len(groups.predictors) != EXPECTED_PREDICTOR_COUNT:
        failures.append(f"predictor_count deve ser {EXPECTED_PREDICTOR_COUNT}")
    if set(METADATA_COLUMNS) & set(groups.predictors) or TARGET_COLUMN in groups.predictors:
        failures.append("metadata/target não podem integrar predictors")
    nulls = {
        column: holdout[column].null_count()
        for column in groups.predictors
        if holdout[column].null_count()
    }
    if nulls:
        failures.append(f"predictors contêm nulos: {nulls}")
    if failures:
        raise ValueError("Holdout 2025 inválido:\n- " + "\n- ".join(failures))


def generate_final_probabilities(
    pipeline: Pipeline,
    holdout: pl.DataFrame,
    predictors: tuple[str, ...],
) -> np.ndarray[Any, np.dtype[np.float64]]:
    classifier = pipeline.named_steps.get("classifier")
    if not isinstance(classifier, XGBClassifier) or classifier.classes_.tolist() != [0, 1]:
        raise ValueError("Classifier final deve possuir classes numéricas [0, 1].")
    raw_probabilities = np.asarray(pipeline.predict_proba(holdout.select(predictors)))
    probabilities = extract_xgboost_positive_probability(classifier, raw_probabilities)
    if not np.isfinite(probabilities).all():
        raise ValueError("Probabilidades finais devem ser finitas.")
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("Probabilidades finais devem pertencer ao intervalo [0, 1].")
    return probabilities


def calculate_probability_metrics(
    target: np.ndarray[Any, np.dtype[np.bool_]],
    probabilities: np.ndarray[Any, np.dtype[np.float64]],
) -> ProbabilityMetrics:
    return ProbabilityMetrics(
        average_precision=float(average_precision_score(target, probabilities)),
        roc_auc=float(roc_auc_score(target, probabilities)),
        brier_score=float(brier_score_loss(target, probabilities, pos_label=True)),
    )


def build_calibration_table(
    target: np.ndarray[Any, np.dtype[np.bool_]],
    probabilities: np.ndarray[Any, np.dtype[np.float64]],
    number_of_bins: int = CALIBRATION_BINS,
) -> pl.DataFrame:
    if number_of_bins < 1:
        raise ValueError("Número de bins de calibração deve ser positivo.")
    quantiles = np.percentile(probabilities, np.linspace(0.0, 100.0, number_of_bins + 1))
    bin_ids = np.searchsorted(quantiles[1:-1], probabilities)
    observed, predicted = calibration_curve(
        target, probabilities, pos_label=True, n_bins=number_of_bins, strategy="quantile"
    )
    occupied_bins = np.unique(bin_ids)
    if len(occupied_bins) != len(observed) or len(observed) != len(predicted):
        raise ValueError("Bins descritivos não reconciliam com calibration_curve do sklearn.")
    rows: list[dict[str, Any]] = []
    for output_bin, (bin_id, observed_rate, predicted_mean) in enumerate(
        zip(occupied_bins, observed, predicted, strict=True), start=1
    ):
        mask = bin_ids == bin_id
        bin_probabilities = probabilities[mask]
        rows.append(
            {
                "bin": output_bin,
                "rows": int(np.count_nonzero(mask)),
                "probability_min": float(np.min(bin_probabilities)),
                "probability_max": float(np.max(bin_probabilities)),
                "mean_predicted_probability": float(predicted_mean),
                "observed_positive_rate": float(observed_rate),
            }
        )
    return pl.DataFrame(rows)


def build_final_predictions(
    holdout: pl.DataFrame,
    probabilities: np.ndarray[Any, np.dtype[np.float64]],
    frozen_threshold: float,
) -> pl.DataFrame:
    if probabilities.shape != (holdout.height,):
        raise ValueError("Probabilidades não estão alinhadas ao holdout final.")
    return pl.DataFrame(
        {
            "id": holdout["id"],
            "source_year": holdout["source_year"],
            TARGET_COLUMN: holdout[TARGET_COLUMN],
            "predicted_probability_grave": probabilities,
            "predicted_grave_frozen_threshold": probabilities >= frozen_threshold,
        }
    ).sort("id")


def validate_final_predictions(predictions: pl.DataFrame, expected_rows: int) -> None:
    expected_columns = (
        "id",
        "source_year",
        TARGET_COLUMN,
        "predicted_probability_grave",
        "predicted_grave_frozen_threshold",
    )
    if tuple(predictions.columns) != expected_columns:
        raise ValueError(f"Colunas finais inválidas: {predictions.columns}")
    if predictions.height != expected_rows or predictions["id"].n_unique() != expected_rows:
        raise ValueError("Predictions finais não reconciliam em linhas/IDs.")
    if set(predictions["source_year"]) != {FINAL_TEST_YEAR}:
        raise ValueError("Predictions finais devem conter somente 2025.")
    probabilities = predictions["predicted_probability_grave"]
    if (
        not probabilities.is_finite().all()
        or not probabilities.is_between(0.0, 1.0, closed="both").all()
    ):
        raise ValueError("Probabilidades persistidas são inválidas.")
    if predictions["predicted_grave_frozen_threshold"].dtype != pl.Boolean:
        raise ValueError("Decisão final persistida deve ser booleana.")


def persist_final_predictions(
    predictions: pl.DataFrame,
    path: Path,
) -> tuple[str, int]:
    validate_final_predictions(predictions, predictions.height)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        predictions.write_parquet(temporary_path)
        persisted = pl.read_parquet(temporary_path)
        validate_final_predictions(persisted, predictions.height)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return sha256_file(path), path.stat().st_size


def build_development_comparison(
    final_metrics: ProbabilityMetrics,
    frozen_metrics: ThresholdMetrics,
    references: InternalReferences,
) -> pl.DataFrame:
    rows = (
        (
            "average_precision",
            "internal_fold_mean",
            references.ap_mean,
            final_metrics.average_precision,
        ),
        ("average_precision", "fold3_2024", references.ap_fold3, final_metrics.average_precision),
        ("roc_auc", "internal_fold_mean", references.mean_roc_auc, final_metrics.roc_auc),
        (
            "brier_score",
            "internal_fold_mean",
            references.mean_brier_score,
            final_metrics.brier_score,
        ),
        (
            "precision_frozen_threshold",
            "pooled_temporal_oof",
            references.oof_precision,
            frozen_metrics.precision,
        ),
        (
            "recall_frozen_threshold",
            "pooled_temporal_oof",
            references.oof_recall,
            frozen_metrics.recall,
        ),
        ("f1_frozen_threshold", "pooled_temporal_oof", references.oof_f1, frozen_metrics.f1),
    )
    return pl.DataFrame(
        [
            {
                "metric": metric,
                "development_reference": reference,
                "development_value": development_value,
                "final_2025_value": final_value,
                "delta_final_minus_development": final_value - development_value,
            }
            for metric, reference, development_value, final_value in rows
        ]
    )


def _threshold_row(role: str, metrics: ThresholdMetrics) -> dict[str, Any]:
    return {
        "threshold_role": role,
        "threshold": metrics.threshold,
        "rows": metrics.rows,
        "actual_positive": metrics.actual_positive,
        "actual_negative": metrics.actual_negative,
        "predicted_positive": metrics.predicted_positive,
        "predicted_negative": metrics.predicted_negative,
        "precision": metrics.precision,
        "recall": metrics.recall,
        "f1": metrics.f1,
        "tn": metrics.tn,
        "fp": metrics.fp,
        "fn": metrics.fn,
        "tp": metrics.tp,
    }


def _string(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _logical_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def build_final_evaluation_table(
    model_manifest: dict[str, str],
    holdout: pl.DataFrame,
    probability_metrics: ProbabilityMetrics,
    frozen_metrics: ThresholdMetrics,
    reference_metrics: ThresholdMetrics,
    references: InternalReferences,
    predictions_path: Path,
    predictions_sha256: str,
    predictions_size_bytes: int,
) -> pl.DataFrame:
    values: dict[str, object] = {
        "evaluation_status": "completed",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "model_training_period": "2021-2024",
        "final_test_year": FINAL_TEST_YEAR,
        "model_artifact_path": model_manifest["model_artifact_path"],
        "model_artifact_sha256": model_manifest["model_artifact_sha256"],
        "frozen_threshold": FROZEN_THRESHOLD_TEXT,
        "threshold_source": "phase_4f",
        "final_rows": holdout.height,
        "final_unique_ids": holdout["id"].n_unique(),
        "final_positive": frozen_metrics.actual_positive,
        "final_negative": frozen_metrics.actual_negative,
        "final_positive_rate": frozen_metrics.actual_positive / holdout.height,
        "average_precision": probability_metrics.average_precision,
        "roc_auc": probability_metrics.roc_auc,
        "brier_score": probability_metrics.brier_score,
        "frozen_threshold_precision": frozen_metrics.precision,
        "frozen_threshold_recall": frozen_metrics.recall,
        "frozen_threshold_f1": frozen_metrics.f1,
        "frozen_threshold_tn": frozen_metrics.tn,
        "frozen_threshold_fp": frozen_metrics.fp,
        "frozen_threshold_fn": frozen_metrics.fn,
        "frozen_threshold_tp": frozen_metrics.tp,
        "reference_threshold": REFERENCE_THRESHOLD,
        "reference_precision": reference_metrics.precision,
        "reference_recall": reference_metrics.recall,
        "reference_f1": reference_metrics.f1,
        "reference_tn": reference_metrics.tn,
        "reference_fp": reference_metrics.fp,
        "reference_fn": reference_metrics.fn,
        "reference_tp": reference_metrics.tp,
        "internal_ap_mean": references.ap_mean,
        "internal_ap_fold3": references.ap_fold3,
        "delta_ap_vs_internal_mean": probability_metrics.average_precision - references.ap_mean,
        "delta_ap_vs_fold3": probability_metrics.average_precision - references.ap_fold3,
        "internal_mean_roc_auc": references.mean_roc_auc,
        "delta_roc_auc_vs_internal_mean": probability_metrics.roc_auc - references.mean_roc_auc,
        "internal_mean_brier_score": references.mean_brier_score,
        "delta_brier_vs_internal_mean": probability_metrics.brier_score
        - references.mean_brier_score,
        "oof_threshold_precision": references.oof_precision,
        "oof_threshold_recall": references.oof_recall,
        "oof_threshold_f1": references.oof_f1,
        "delta_precision_vs_oof": frozen_metrics.precision - references.oof_precision,
        "delta_recall_vs_oof": frozen_metrics.recall - references.oof_recall,
        "delta_f1_vs_oof": frozen_metrics.f1 - references.oof_f1,
        "final_predictions_path": _logical_path(predictions_path),
        "final_predictions_sha256": predictions_sha256,
        "final_predictions_size_bytes": predictions_size_bytes,
        "model_retrained": False,
        "threshold_reselected": False,
        "hyperparameter_tuning": False,
        "calibration_model_fitted": False,
        "final_test_used": True,
        "final_evaluation_performed": True,
    }
    return pl.DataFrame(
        {"key": list(values), "value": [_string(value) for value in values.values()]}
    )


def build_final_evaluation_checklist(
    holdout: pl.DataFrame,
    probabilities: np.ndarray[Any, np.dtype[np.float64]],
    frozen_metrics: ThresholdMetrics,
    model_path: Path,
    predictions_path: Path,
    predictions_sha256: str,
    expected_model_sha256: str = EXPECTED_MODEL_SHA256,
    expected_final_rows: int = EXPECTED_FINAL_ROWS,
) -> pl.DataFrame:
    checks = (
        ("EVA001", "Manifesto 4G está válido", True, "refit_status=completed"),
        (
            "EVA002",
            "Pipeline congelado existe",
            model_path.is_file(),
            _logical_path(model_path),
        ),
        (
            "EVA003",
            "SHA coincide antes do load",
            sha256_file(model_path) == expected_model_sha256,
            expected_model_sha256,
        ),
        ("EVA004", "Pipeline está fitado", True, "check_is_fitted aprovado"),
        ("EVA005", "Modelo é o XGBoost selecionado", True, XGBOOST_MODEL_ID),
        ("EVA006", "Pipeline possui 300 rounds", True, "300/300"),
        (
            "EVA007",
            "Threshold 4F coincide exatamente",
            frozen_metrics.threshold == float(FROZEN_THRESHOLD_TEXT),
            FROZEN_THRESHOLD_TEXT,
        ),
        (
            "EVA008",
            "Holdout contém somente 2025",
            set(holdout["source_year"]) == {FINAL_TEST_YEAR},
            "2025",
        ),
        (
            "EVA009",
            "2021-2024 estão ausentes",
            not (set(DEVELOPMENT_YEARS) & set(holdout["source_year"])),
            "ausentes",
        ),
        (
            "EVA010",
            "Linhas e IDs foram reconciliados",
            holdout.height == holdout["id"].n_unique() == expected_final_rows,
            f"{holdout.height} linhas/IDs",
        ),
        ("EVA011", "Predictors permanecem congelados", True, "22 predictors"),
        ("EVA012", "Target final é válido", holdout[TARGET_COLUMN].dtype == pl.Boolean, "Boolean"),
        (
            "EVA013",
            "Probabilidades finais são válidas",
            np.isfinite(probabilities).all()
            and np.all((probabilities >= 0.0) & (probabilities <= 1.0)),
            f"{probabilities.size} probabilidades",
        ),
        (
            "EVA014",
            "AP usa average_precision_score",
            True,
            "sklearn.metrics.average_precision_score",
        ),
        ("EVA015", "Mesmo threshold 4F foi aplicado", True, FROZEN_THRESHOLD_TEXT),
        ("EVA016", "Threshold 0.5 é somente referência", True, "reference_0_5"),
        ("EVA017", "Nenhum threshold foi selecionado", True, "threshold_reselected=false"),
        ("EVA018", "Nenhum fit foi executado", True, "model_retrained=false"),
        ("EVA019", "Nenhum tuning foi executado", True, "hyperparameter_tuning=false"),
        ("EVA020", "Nenhum calibrador foi treinado", True, "calibration_model_fitted=false"),
        (
            "EVA021",
            "Predictions 2025 foram persistidas",
            predictions_path.is_file(),
            _logical_path(predictions_path),
        ),
        (
            "EVA022",
            "SHA das predictions foi calculado",
            len(predictions_sha256) == 64,
            predictions_sha256,
        ),
        ("EVA023", "Comparação é somente descritiva", True, "sem pass/fail de performance"),
        ("EVA024", "Teste final foi utilizado", True, "final_test_used=true"),
        ("EVA025", "Avaliação final foi realizada", True, "final_evaluation_performed=true"),
    )
    return pl.DataFrame(
        [
            {
                "check_id": check_id,
                "check": check,
                "status": "PASS" if passed else "FAIL",
                "evidence": evidence,
            }
            for check_id, check, passed, evidence in checks
        ]
    )


def write_final_evaluation_tables(
    result: FinalEvaluationResult,
    tables_dir: Path,
) -> tuple[Path, ...]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "phase_4h_final_evaluation.csv": result.final_evaluation,
        "phase_4h_threshold_evaluation.csv": result.threshold_evaluation,
        "phase_4h_development_comparison.csv": result.development_comparison,
        "phase_4h_calibration.csv": result.calibration,
        "phase_4h_final_evaluation_checklist.csv": result.checklist,
    }
    paths = tuple(tables_dir / filename for filename in tables)
    for path, table in zip(paths, tables.values(), strict=True):
        table.write_csv(path)
    return paths


def run_final_evaluation(
    analytical_path: Path = PRIMARY_ANALYTICAL_PARQUET_PATH,
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
    tables_dir: Path = TABLES_DIR,
    predictions_path: Path = FINAL_PREDICTIONS_PATH,
) -> FinalEvaluationRun:
    inputs = load_final_evaluation_inputs(tables_dir)
    references = validate_pre_evaluation_sources(inputs)
    pipeline, model_path = load_validated_frozen_pipeline(inputs.final_model_manifest)
    predictors = load_predictors_from_schema(schema_path)
    groups = load_preprocessing_groups(schema_path)
    if (
        set(predictors) != set(groups.predictors)
        or len(predictors) != len(groups.predictors)
        or len(predictors) != EXPECTED_PREDICTOR_COUNT
    ):
        raise ValueError("Predictors 3C/3E divergem antes da abertura de 2025.")

    holdout = load_final_holdout(analytical_path, predictors)
    validate_final_holdout(holdout, groups, inputs.final_partition)
    probabilities = generate_final_probabilities(pipeline, holdout, groups.predictors)
    target = holdout[TARGET_COLUMN].to_numpy()
    probability_metrics = calculate_probability_metrics(target, probabilities)
    frozen_metrics = evaluate_threshold(probabilities, target, float(FROZEN_THRESHOLD_TEXT))
    reference_metrics = evaluate_threshold(probabilities, target, REFERENCE_THRESHOLD)
    calibration = build_calibration_table(target, probabilities)
    predictions = build_final_predictions(holdout, probabilities, float(FROZEN_THRESHOLD_TEXT))
    predictions_sha256, predictions_size_bytes = persist_final_predictions(
        predictions, predictions_path
    )
    checklist = build_final_evaluation_checklist(
        holdout,
        probabilities,
        frozen_metrics,
        model_path,
        predictions_path,
        predictions_sha256,
    )
    failed = checklist.filter(pl.col("status") != "PASS")
    if not failed.is_empty():
        raise ValueError(
            "Checks críticos da Fase 4H falharam; avaliação não será publicada: "
            f"{failed.to_dicts()}"
        )
    result = FinalEvaluationResult(
        model_sha256=inputs.final_model_manifest["model_artifact_sha256"],
        probability_metrics=probability_metrics,
        frozen_threshold_metrics=frozen_metrics,
        reference_threshold_metrics=reference_metrics,
        references=references,
        predictions=predictions,
        predictions_path=predictions_path,
        predictions_sha256=predictions_sha256,
        predictions_size_bytes=predictions_size_bytes,
        final_evaluation=build_final_evaluation_table(
            inputs.final_model_manifest,
            holdout,
            probability_metrics,
            frozen_metrics,
            reference_metrics,
            references,
            predictions_path,
            predictions_sha256,
            predictions_size_bytes,
        ),
        threshold_evaluation=pl.DataFrame(
            (
                _threshold_row("frozen_threshold", frozen_metrics),
                _threshold_row("reference_0_5", reference_metrics),
            )
        ),
        development_comparison=build_development_comparison(
            probability_metrics, frozen_metrics, references
        ),
        calibration=calibration,
        checklist=checklist,
    )
    return FinalEvaluationRun(
        result=result,
        table_paths=write_final_evaluation_tables(result, tables_dir),
    )
