from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from tcc_prf_severity.config import (
    PRIMARY_ANALYTICAL_PARQUET_PATH,
    PRIMARY_ANALYTICAL_SCHEMA_PATH,
    PROJECT_ROOT,
    TABLES_DIR,
)
from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.modeling.final_evaluation import (
    load_final_holdout,
    load_validated_frozen_pipeline,
    validate_final_holdout,
)
from tcc_prf_severity.modeling.final_refit import (
    EXPECTED_BOOSTING_ROUNDS,
    EXPECTED_PREDICTOR_COUNT,
)
from tcc_prf_severity.modeling.preprocessing import (
    PreprocessingGroups,
    load_preprocessing_groups,
)

EXPECTED_TRANSFORMED_FEATURE_COUNT = 226
EXPECTED_CONTRIBUTION_COLUMN_COUNT = EXPECTED_TRANSFORMED_FEATURE_COUNT + 1
PROBABILITY_RECONCILIATION_TOLERANCE = 1e-6
FINAL_TEST_YEAR = 2025

PREDICTION_COLUMNS = (
    "id",
    "source_year",
    "target_grave",
    "predicted_probability_grave",
    "predicted_grave_frozen_threshold",
)

REQUIRED_DOCUMENTS = (
    PROJECT_ROOT / "docs" / "PHASE_4H_FINAL_EVALUATION.md",
    PROJECT_ROOT / "docs" / "PHASE_4G_FINAL_REFIT.md",
    PROJECT_ROOT / "docs" / "PHASE_2_EDA_SYNTHESIS.md",
    PROJECT_ROOT / "docs" / "EDA_FINDINGS.md",
    PROJECT_ROOT / "docs" / "TCC_RESEARCH_LOG.md",
)


@dataclass(frozen=True)
class FinalInterpretationSources:
    final_evaluation: dict[str, str]
    threshold_evaluation: pl.DataFrame
    evaluation_checklist: pl.DataFrame
    final_model_manifest: dict[str, str]
    refit_checklist: pl.DataFrame
    threshold_selection: dict[str, str]
    model_selection: dict[str, str]


@dataclass(frozen=True)
class InterpretationContract:
    selected_model_id: str
    selected_model_family: str
    final_rows: int
    final_positive: int
    final_negative: int
    frozen_threshold: float
    pipeline_sha256: str
    predictions_path: str
    predictions_sha256: str
    tp: int
    fp: int
    fn: int
    tn: int


@dataclass(frozen=True)
class ContributionAudit:
    feature_contributions: np.ndarray[Any, np.dtype[np.float64]]
    bias: np.ndarray[Any, np.dtype[np.float64]]
    reconstructed_probabilities: np.ndarray[Any, np.dtype[np.float64]]
    maximum_probability_error: float
    mean_probability_error: float


@dataclass(frozen=True)
class FinalInterpretationResult:
    contract: InterpretationContract
    global_contributions: pl.DataFrame
    transformed_contributions: pl.DataFrame
    error_analysis: pl.DataFrame
    contributions_by_outcome: pl.DataFrame
    summary: pl.DataFrame
    checklist: pl.DataFrame


@dataclass(frozen=True)
class FinalInterpretationRun:
    result: FinalInterpretationResult
    table_paths: tuple[Path, ...]


def _key_value_mapping(table: pl.DataFrame, source: str) -> dict[str, str]:
    if not {"key", "value"}.issubset(table.columns):
        raise ValueError(f"Tabela key/value inválida: {source}.")
    selected = table.select("key", "value")
    if selected.get_column("key").n_unique() != selected.height:
        raise ValueError(f"Chaves duplicadas em {source}.")
    return {str(row["key"]): str(row["value"]) for row in selected.iter_rows(named=True)}


def load_final_interpretation_sources(
    tables_dir: Path = TABLES_DIR,
    required_documents: tuple[Path, ...] = REQUIRED_DOCUMENTS,
) -> FinalInterpretationSources:
    paths = {
        "avaliação 4H": tables_dir / "phase_4h_final_evaluation.csv",
        "thresholds 4H": tables_dir / "phase_4h_threshold_evaluation.csv",
        "checklist 4H": tables_dir / "phase_4h_final_evaluation_checklist.csv",
        "manifesto 4G": tables_dir / "phase_4g_final_model_manifest.csv",
        "checklist 4G": tables_dir / "phase_4g_refit_checklist.csv",
        "threshold 4F": tables_dir / "phase_4f_threshold_selection.csv",
        "seleção 4E": tables_dir / "phase_4e_model_selection.csv",
    }
    missing = [f"{name}: {path}" for name, path in paths.items() if not path.is_file()]
    missing.extend(f"documento: {path}" for path in required_documents if not path.is_file())
    if missing:
        raise FileNotFoundError(f"Fontes autoritativas ausentes antes da interpretação: {missing}")
    return FinalInterpretationSources(
        final_evaluation=_key_value_mapping(
            pl.read_csv(paths["avaliação 4H"]), str(paths["avaliação 4H"])
        ),
        threshold_evaluation=pl.read_csv(paths["thresholds 4H"]),
        evaluation_checklist=pl.read_csv(paths["checklist 4H"]),
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
    )


def _require_all_pass(table: pl.DataFrame, source: str) -> None:
    if "status" not in table.columns or table.is_empty() or set(table["status"]) != {"PASS"}:
        raise ValueError(f"{source} não está integralmente aprovado.")


def validate_final_interpretation_sources(
    sources: FinalInterpretationSources,
) -> InterpretationContract:
    evaluation = sources.final_evaluation
    manifest = sources.final_model_manifest
    threshold = sources.threshold_selection
    selection = sources.model_selection
    expected_evaluation = {
        "evaluation_status": "completed",
        "model_training_period": "2021-2024",
        "final_test_year": "2025",
        "model_retrained": "false",
        "threshold_reselected": "false",
        "hyperparameter_tuning": "false",
        "calibration_model_fitted": "false",
        "final_test_used": "true",
        "final_evaluation_performed": "true",
        "threshold_source": "phase_4f",
    }
    divergences: dict[str, object] = {
        f"4H.{key}": (evaluation.get(key), value)
        for key, value in expected_evaluation.items()
        if evaluation.get(key) != value
    }
    cross_source_expectations = {
        "selected_model_id": (
            evaluation.get("selected_model_id"),
            manifest.get("selected_model_id"),
            threshold.get("selected_model_id"),
            selection.get("selected_model_id"),
        ),
        "selected_model_family": (
            evaluation.get("selected_model_family"),
            manifest.get("selected_model_family"),
            threshold.get("selected_model_family"),
            selection.get("selected_model_family"),
        ),
        "pipeline_sha256": (
            evaluation.get("model_artifact_sha256"),
            manifest.get("model_artifact_sha256"),
        ),
        "pipeline_path": (
            evaluation.get("model_artifact_path"),
            manifest.get("model_artifact_path"),
        ),
        "frozen_threshold": (
            evaluation.get("frozen_threshold"),
            manifest.get("frozen_threshold"),
            threshold.get("selected_threshold"),
        ),
    }
    for name, observed in cross_source_expectations.items():
        if None in observed or len(set(observed)) != 1:
            divergences[name] = observed
    if manifest.get("refit_status") != "completed":
        divergences["4G.refit_status"] = manifest.get("refit_status")
    if manifest.get("predictor_count") != str(EXPECTED_PREDICTOR_COUNT):
        divergences["4G.predictor_count"] = manifest.get("predictor_count")
    if manifest.get("transformed_feature_count") != str(EXPECTED_TRANSFORMED_FEATURE_COUNT):
        divergences["4G.transformed_feature_count"] = manifest.get("transformed_feature_count")
    if manifest.get("completed_boosting_rounds") != str(EXPECTED_BOOSTING_ROUNDS):
        divergences["4G.completed_boosting_rounds"] = manifest.get("completed_boosting_rounds")
    if divergences:
        raise ValueError(f"Estado congelado incompatível com a interpretação 4I: {divergences}.")
    _require_all_pass(sources.evaluation_checklist, "Checklist 4H")
    _require_all_pass(sources.refit_checklist, "Checklist 4G")

    frozen_rows = sources.threshold_evaluation.filter(
        pl.col("threshold_role") == "frozen_threshold"
    )
    if frozen_rows.height != 1:
        raise ValueError("Tabela 4H deve conter exatamente um threshold congelado.")
    frozen_row = frozen_rows.row(0, named=True)
    threshold_value = float(evaluation["frozen_threshold"])
    threshold_checks = {
        "threshold": threshold_value,
        "rows": int(evaluation["final_rows"]),
        "actual_positive": int(evaluation["final_positive"]),
        "actual_negative": int(evaluation["final_negative"]),
        "tn": int(evaluation["frozen_threshold_tn"]),
        "fp": int(evaluation["frozen_threshold_fp"]),
        "fn": int(evaluation["frozen_threshold_fn"]),
        "tp": int(evaluation["frozen_threshold_tp"]),
    }
    inconsistent = {
        key: (frozen_row.get(key), value)
        for key, value in threshold_checks.items()
        if frozen_row.get(key) != value
    }
    if inconsistent:
        raise ValueError(f"Thresholds 4H não reconciliam com a avaliação final: {inconsistent}.")
    if int(evaluation["final_unique_ids"]) != int(evaluation["final_rows"]):
        raise ValueError("A avaliação 4H não registra IDs finais únicos.")

    return InterpretationContract(
        selected_model_id=evaluation["selected_model_id"],
        selected_model_family=evaluation["selected_model_family"],
        final_rows=int(evaluation["final_rows"]),
        final_positive=int(evaluation["final_positive"]),
        final_negative=int(evaluation["final_negative"]),
        frozen_threshold=threshold_value,
        pipeline_sha256=evaluation["model_artifact_sha256"],
        predictions_path=evaluation["final_predictions_path"],
        predictions_sha256=evaluation["final_predictions_sha256"],
        tp=int(evaluation["frozen_threshold_tp"]),
        fp=int(evaluation["frozen_threshold_fp"]),
        fn=int(evaluation["frozen_threshold_fn"]),
        tn=int(evaluation["frozen_threshold_tn"]),
    )


def _outcome_labels(
    target: np.ndarray[Any, np.dtype[np.bool_]],
    predicted: np.ndarray[Any, np.dtype[np.bool_]],
) -> np.ndarray[Any, np.dtype[np.str_]]:
    return np.select(
        (target & predicted, ~target & predicted, target & ~predicted),
        ("TP", "FP", "FN"),
        default="TN",
    )


def load_and_validate_final_predictions(
    contract: InterpretationContract,
    project_root: Path = PROJECT_ROOT,
) -> pl.DataFrame:
    path = project_root / contract.predictions_path
    if not path.is_file():
        raise FileNotFoundError(f"Predictions finais 4H ausentes: {path}")
    observed_sha256 = sha256_file(path)
    if observed_sha256 != contract.predictions_sha256:
        raise ValueError(
            "SHA-256 das predictions 4H diverge: "
            f"esperado={contract.predictions_sha256}; observado={observed_sha256}."
        )
    try:
        predictions = pl.read_parquet(path)
    except Exception as error:
        raise ValueError("Não foi possível ler as predictions congeladas da 4H.") from error
    failures: list[str] = []
    if tuple(predictions.columns) != PREDICTION_COLUMNS:
        failures.append(f"colunas devem ser exatamente {PREDICTION_COLUMNS}")
    if predictions.height != contract.final_rows:
        failures.append(f"linhas={predictions.height}; esperado={contract.final_rows}")
    if predictions["id"].n_unique() != predictions.height:
        failures.append("IDs não são únicos")
    if set(predictions["source_year"].unique().to_list()) != {FINAL_TEST_YEAR}:
        failures.append("predictions devem conter somente 2025")
    if predictions["target_grave"].dtype != pl.Boolean:
        failures.append("target_grave deve ser booleano")
    if predictions["predicted_grave_frozen_threshold"].dtype != pl.Boolean:
        failures.append("decisão congelada deve ser booleana")
    if predictions.null_count().select(pl.sum_horizontal(pl.all())).item() != 0:
        failures.append("predictions não podem conter nulos")
    probabilities = predictions["predicted_probability_grave"].to_numpy()
    if not np.isfinite(probabilities).all() or np.any((probabilities < 0) | (probabilities > 1)):
        failures.append("probabilidades devem ser finitas e pertencer a [0,1]")
    expected_decisions = probabilities >= contract.frozen_threshold
    observed_decisions = predictions["predicted_grave_frozen_threshold"].to_numpy()
    if not np.array_equal(expected_decisions, observed_decisions):
        failures.append("decisões persistidas não reconciliam com o threshold 4F")
    target = predictions["target_grave"].to_numpy()
    if int(np.count_nonzero(target)) != contract.final_positive:
        failures.append("quantidade de graves diverge da avaliação 4H")
    outcomes = _outcome_labels(target, observed_decisions)
    expected_outcomes = {
        "TP": contract.tp,
        "FP": contract.fp,
        "FN": contract.fn,
        "TN": contract.tn,
    }
    observed_outcomes = {
        name: int(np.count_nonzero(outcomes == name)) for name in expected_outcomes
    }
    if observed_outcomes != expected_outcomes:
        failures.append(f"matriz de confusão diverge: {observed_outcomes} != {expected_outcomes}")
    if failures:
        raise ValueError("Predictions finais 4H inválidas:\n- " + "\n- ".join(failures))
    return predictions


def align_holdout_to_predictions(
    holdout: pl.DataFrame,
    predictions: pl.DataFrame,
) -> pl.DataFrame:
    holdout_ids = holdout.select("id")
    prediction_ids = predictions.select("id")
    missing_from_holdout = prediction_ids.join(holdout_ids, on="id", how="anti").height
    missing_from_predictions = holdout_ids.join(prediction_ids, on="id", how="anti").height
    if missing_from_holdout or missing_from_predictions:
        raise ValueError(
            "IDs do dataset analítico e das predictions 4H divergem: "
            f"ausentes no analítico={missing_from_holdout}; "
            f"ausentes nas predictions={missing_from_predictions}."
        )
    ordered_metadata = predictions.select("id", "source_year", "target_grave").with_row_index(
        "_prediction_order"
    )
    joined = ordered_metadata.join(
        holdout,
        on="id",
        how="left",
        suffix="_analytical",
        validate="1:1",
    ).sort("_prediction_order")
    mismatches = joined.filter(
        (pl.col("source_year") != pl.col("source_year_analytical"))
        | (pl.col("target_grave") != pl.col("target_grave_analytical"))
    ).height
    if mismatches:
        raise ValueError(
            f"Ano/target do dataset analítico divergem das predictions 4H para {mismatches} IDs."
        )
    predictor_columns = [
        column for column in holdout.columns if column not in {"id", "source_year", "target_grave"}
    ]
    aligned = joined.select(
        "id",
        pl.col("source_year_analytical").alias("source_year"),
        pl.col("target_grave_analytical").alias("target_grave"),
        *predictor_columns,
    )
    expected_metadata = predictions.select("id", "source_year", "target_grave")
    if not aligned.select("id", "source_year", "target_grave").equals(expected_metadata):
        raise ValueError("Falha ao alinhar o dataset analítico às predictions 4H por ID.")
    return aligned


def transform_interpretation_population(
    pipeline: Pipeline,
    holdout: pl.DataFrame,
    predictors: tuple[str, ...],
) -> Any:
    preprocessor = pipeline.named_steps.get("preprocessor")
    if not isinstance(preprocessor, ColumnTransformer):
        raise TypeError("Pipeline final não contém o ColumnTransformer contratado.")
    transformed = preprocessor.transform(holdout.select(predictors))
    expected_shape = (holdout.height, EXPECTED_TRANSFORMED_FEATURE_COUNT)
    if transformed.shape != expected_shape:
        raise ValueError(
            f"Matriz transformada divergente: observado={transformed.shape}; "
            f"esperado={expected_shape}."
        )
    return transformed


def _category_text(value: object) -> str:
    if isinstance(value, np.generic):
        value = value.item()
    return str(value)


def build_transformed_feature_mapping(
    preprocessor: ColumnTransformer,
    groups: PreprocessingGroups,
    expected_feature_count: int = EXPECTED_TRANSFORMED_FEATURE_COUNT,
) -> pl.DataFrame:
    feature_names = [str(value) for value in preprocessor.get_feature_names_out()]
    encoder = preprocessor.named_transformers_.get("categorical")
    if not isinstance(encoder, OneHotEncoder):
        raise TypeError("Transformer categórico fitado deve ser OneHotEncoder.")
    if len(encoder.categories_) != len(groups.categorical):
        raise ValueError("Categorias aprendidas não reconciliam com predictors categóricos.")
    encoded_names = [str(value) for value in encoder.get_feature_names_out(groups.categorical)]
    rows: list[dict[str, str]] = []
    cursor = 0
    encoded_cursor = 0
    for predictor, categories in zip(groups.categorical, encoder.categories_, strict=True):
        for category in categories:
            actual = feature_names[cursor]
            expected = f"categorical__{encoded_names[encoded_cursor]}"
            if actual != expected:
                raise ValueError(
                    "Feature OHE fora da ordem contratada: "
                    f"observado={actual}; esperado={expected}."
                )
            rows.append(
                {
                    "transformed_feature": actual,
                    "source_predictor": predictor,
                    "predictor_group": "categorical",
                    "category_or_level": _category_text(category),
                }
            )
            cursor += 1
            encoded_cursor += 1
    for predictor in groups.numeric:
        actual = feature_names[cursor]
        if actual != f"numeric__{predictor}":
            raise ValueError(f"Feature numérica mapeada incorretamente: {actual}.")
        rows.append(
            {
                "transformed_feature": actual,
                "source_predictor": predictor,
                "predictor_group": "numeric",
                "category_or_level": "",
            }
        )
        cursor += 1
    for predictor in groups.binary:
        actual = feature_names[cursor]
        if actual != f"binary__{predictor}":
            raise ValueError(f"Feature binária mapeada incorretamente: {actual}.")
        rows.append(
            {
                "transformed_feature": actual,
                "source_predictor": predictor,
                "predictor_group": "binary",
                "category_or_level": "",
            }
        )
        cursor += 1
    mapping = pl.DataFrame(rows)
    if cursor != len(feature_names) or mapping.height != expected_feature_count:
        raise ValueError(
            "Mapeamento transformado incompleto: "
            f"mapeadas={mapping.height}; nomes={len(feature_names)}; "
            f"esperado={expected_feature_count}."
        )
    if mapping["source_predictor"].n_unique() != len(groups.predictors):
        raise ValueError("Mapeamento não preserva todos os predictors de origem.")
    return mapping


def stable_logistic(
    margins: np.ndarray[Any, np.dtype[np.float64]],
) -> np.ndarray[Any, np.dtype[np.float64]]:
    margins = np.asarray(margins, dtype=np.float64)
    probabilities = np.empty_like(margins)
    positive = margins >= 0
    probabilities[positive] = 1.0 / (1.0 + np.exp(-margins[positive]))
    exp_margin = np.exp(margins[~positive])
    probabilities[~positive] = exp_margin / (1.0 + exp_margin)
    return probabilities


def calculate_native_contributions(
    pipeline: Pipeline,
    transformed: Any,
    official_probabilities: np.ndarray[Any, np.dtype[np.float64]],
    tolerance: float = PROBABILITY_RECONCILIATION_TOLERANCE,
    expected_feature_count: int = EXPECTED_TRANSFORMED_FEATURE_COUNT,
) -> ContributionAudit:
    classifier = pipeline.named_steps.get("classifier")
    if not isinstance(classifier, XGBClassifier):
        raise TypeError("Pipeline final não contém XGBClassifier.")
    contribution_matrix = np.asarray(
        classifier.get_booster().predict(xgboost.DMatrix(transformed), pred_contribs=True),
        dtype=np.float64,
    )
    expected_shape = (len(official_probabilities), expected_feature_count + 1)
    if contribution_matrix.shape != expected_shape:
        raise ValueError(
            "pred_contribs deve possuir feature_count + bias: "
            f"{contribution_matrix.shape} != {expected_shape}."
        )
    feature_contributions = contribution_matrix[:, :-1]
    bias = contribution_matrix[:, -1]
    margins = bias + np.sum(feature_contributions, axis=1)
    reconstructed = stable_logistic(margins)
    differences = np.abs(reconstructed - np.asarray(official_probabilities, dtype=np.float64))
    maximum_error = float(np.max(differences))
    mean_error = float(np.mean(differences))
    if not np.isfinite(differences).all() or maximum_error > tolerance:
        raise ValueError(
            "Contribuições não reconciliam com probabilities 4H: "
            f"máximo={maximum_error}; tolerância={tolerance}."
        )
    return ContributionAudit(
        feature_contributions=feature_contributions,
        bias=bias,
        reconstructed_probabilities=reconstructed,
        maximum_probability_error=maximum_error,
        mean_probability_error=mean_error,
    )


def build_contribution_tables(
    contributions: np.ndarray[Any, np.dtype[np.float64]],
    mapping: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    if contributions.ndim != 2 or contributions.shape[1] != mapping.height:
        raise ValueError("Contribuições e mapeamento possuem dimensões incompatíveis.")
    feature_abs = np.mean(np.abs(contributions), axis=0)
    feature_signed = np.mean(contributions, axis=0)
    transformed = mapping.with_columns(
        pl.Series("mean_abs_margin_contribution", feature_abs),
        pl.Series("mean_signed_margin_contribution", feature_signed),
    ).sort(["mean_abs_margin_contribution", "transformed_feature"], descending=[True, False])
    transformed = transformed.with_row_index("rank", offset=1).select(
        "rank",
        "transformed_feature",
        "source_predictor",
        "predictor_group",
        "category_or_level",
        "mean_abs_margin_contribution",
        "mean_signed_margin_contribution",
    )

    global_rows: list[dict[str, Any]] = []
    mapping_sources = mapping["source_predictor"].to_numpy()
    for source in mapping["source_predictor"].unique(maintain_order=True):
        indices = np.flatnonzero(mapping_sources == source)
        selected = contributions[:, indices]
        group_name = mapping.filter(pl.col("source_predictor") == source)["predictor_group"].item(0)
        global_rows.append(
            {
                "source_predictor": source,
                "predictor_group": group_name,
                "transformed_feature_count": len(indices),
                "mean_abs_margin_contribution": float(np.mean(np.sum(np.abs(selected), axis=1))),
                "mean_signed_margin_contribution": float(np.mean(np.sum(selected, axis=1))),
            }
        )
    global_table = pl.DataFrame(global_rows)
    total = float(global_table["mean_abs_margin_contribution"].sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("Contribuição absoluta global deve ser positiva e finita.")
    global_table = (
        global_table.with_columns(
            (pl.col("mean_abs_margin_contribution") / total).alias(
                "share_of_total_mean_abs_contribution"
            )
        )
        .sort(["mean_abs_margin_contribution", "source_predictor"], descending=[True, False])
        .with_row_index("rank", offset=1)
        .select(
            "rank",
            "source_predictor",
            "predictor_group",
            "transformed_feature_count",
            "mean_abs_margin_contribution",
            "mean_signed_margin_contribution",
            "share_of_total_mean_abs_contribution",
        )
    )
    return global_table, transformed


def build_error_analysis(
    predictions: pl.DataFrame,
) -> tuple[pl.DataFrame, np.ndarray[Any, np.dtype[np.str_]]]:
    target = predictions["target_grave"].to_numpy()
    predicted = predictions["predicted_grave_frozen_threshold"].to_numpy()
    probabilities = predictions["predicted_probability_grave"].to_numpy()
    outcomes = _outcome_labels(target, predicted)
    rows: list[dict[str, Any]] = []
    for outcome in ("TP", "FP", "FN", "TN"):
        values = probabilities[outcomes == outcome]
        if len(values) == 0:
            raise ValueError(f"Outcome {outcome} não possui observações.")
        rows.append(
            {
                "outcome": outcome,
                "rows": len(values),
                "share_of_final_rows": float(len(values) / len(probabilities)),
                "mean_probability": float(np.mean(values)),
                "median_probability": float(np.median(values)),
                "p10_probability": float(np.percentile(values, 10)),
                "p25_probability": float(np.percentile(values, 25)),
                "p75_probability": float(np.percentile(values, 75)),
                "p90_probability": float(np.percentile(values, 90)),
                "minimum_probability": float(np.min(values)),
                "maximum_probability": float(np.max(values)),
            }
        )
    return pl.DataFrame(rows), outcomes


def build_contributions_by_outcome(
    contributions: np.ndarray[Any, np.dtype[np.float64]],
    mapping: pl.DataFrame,
    outcomes: np.ndarray[Any, np.dtype[np.str_]],
) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    sources = mapping["source_predictor"].unique(maintain_order=True)
    mapping_sources = mapping["source_predictor"].to_numpy()
    for source in sources:
        indices = np.flatnonzero(mapping_sources == source)
        selected = contributions[:, indices]
        absolute = np.sum(np.abs(selected), axis=1)
        signed = np.sum(selected, axis=1)
        for outcome in ("TP", "FP", "FN", "TN"):
            mask = outcomes == outcome
            rows.append(
                {
                    "source_predictor": source,
                    "outcome": outcome,
                    "rows": int(np.count_nonzero(mask)),
                    "mean_abs_margin_contribution": float(np.mean(absolute[mask])),
                    "mean_signed_margin_contribution": float(np.mean(signed[mask])),
                }
            )
    return pl.DataFrame(rows)


def _string(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def build_interpretation_summary(
    contract: InterpretationContract,
    audit: ContributionAudit,
    global_contributions: pl.DataFrame,
) -> pl.DataFrame:
    top = global_contributions.head(5).to_dicts()
    values: list[tuple[str, object]] = [
        ("interpretation_status", "completed"),
        ("selected_model_id", contract.selected_model_id),
        ("selected_model_family", contract.selected_model_family),
        ("interpretation_population", "2025_post_final_evaluation"),
        ("final_rows", contract.final_rows),
        ("predictor_count", global_contributions.height),
        ("transformed_feature_count", audit.feature_contributions.shape[1]),
        ("interpretation_method", "xgboost_native_tree_shap_pred_contribs"),
        ("contribution_scale", "raw_margin"),
        ("model_artifact_sha256", contract.pipeline_sha256),
        ("predictions_sha256", contract.predictions_sha256),
        ("maximum_probability_reconciliation_error", audit.maximum_probability_error),
        ("mean_probability_reconciliation_error", audit.mean_probability_error),
    ]
    for rank, row in enumerate(top, start=1):
        values.extend(
            (
                (f"top_{rank}_predictor", row["source_predictor"]),
                (f"top_{rank}_mean_abs_contribution", row["mean_abs_margin_contribution"]),
            )
        )
    values.extend(
        (
            ("tp", contract.tp),
            ("fp", contract.fp),
            ("fn", contract.fn),
            ("tn", contract.tn),
            ("frozen_threshold", contract.frozen_threshold),
            ("model_modified", False),
            ("threshold_modified", False),
            ("features_modified", False),
            ("preprocessing_modified", False),
            ("hyperparameters_modified", False),
            ("post_final_evaluation_interpretation", True),
            ("causal_interpretation", False),
        )
    )
    return pl.DataFrame(
        {"key": [key for key, _ in values], "value": [_string(v) for _, v in values]}
    )


def build_interpretation_checklist(
    contract: InterpretationContract,
    audit: ContributionAudit,
    mapping: pl.DataFrame,
    global_contributions: pl.DataFrame,
    transformed_contributions: pl.DataFrame,
    error_analysis: pl.DataFrame,
) -> pl.DataFrame:
    outcomes = {
        str(row["outcome"]): int(row["rows"]) for row in error_analysis.iter_rows(named=True)
    }
    expected_outcomes = {
        "TP": contract.tp,
        "FP": contract.fp,
        "FN": contract.fn,
        "TN": contract.tn,
    }
    share = float(global_contributions["share_of_total_mean_abs_contribution"].sum())
    checks = (
        ("phase_4h_completed", True, "evaluation_status=completed"),
        ("phase_4h_did_not_modify_model", True, "model_retrained=false"),
        ("pipeline_sha_valid", True, contract.pipeline_sha256),
        ("predictions_sha_valid", True, contract.predictions_sha256),
        ("pipeline_fitted", True, "pipeline 4G validado antes da interpretação"),
        ("boosting_rounds", EXPECTED_BOOSTING_ROUNDS == 300, "300 rounds"),
        ("predictor_count", global_contributions.height == 22, str(global_contributions.height)),
        ("transformed_feature_count", mapping.height == 226, str(mapping.height)),
        (
            "feature_mapping_complete",
            mapping["transformed_feature"].n_unique() == 226,
            "226 features mapeadas sem duplicação",
        ),
        (
            "pred_contribs_columns",
            audit.feature_contributions.shape[1] + 1 == 227,
            str(audit.feature_contributions.shape[1] + 1),
        ),
        ("bias_separated", audit.bias.ndim == 1, "última coluna tratada como bias"),
        (
            "probabilities_reconciled",
            audit.maximum_probability_error <= PROBABILITY_RECONCILIATION_TOLERANCE,
            str(audit.maximum_probability_error),
        ),
        ("global_table_rows", global_contributions.height == 22, str(global_contributions.height)),
        (
            "transformed_table_rows",
            transformed_contributions.height == 226,
            str(transformed_contributions.height),
        ),
        ("global_shares_reconciled", bool(np.isclose(share, 1.0)), str(share)),
        ("frozen_threshold_preserved", True, str(contract.frozen_threshold)),
        ("confusion_matrix_reconciled", outcomes == expected_outcomes, str(outcomes)),
        ("no_fit", True, "nenhum fit/fit_transform executado"),
        ("no_tuning", True, "nenhum tuning executado"),
        ("no_new_threshold", True, "decisões 4H reutilizadas"),
        ("no_calibration", True, "nenhum calibrador executado"),
        ("no_feature_selection", True, "ranking somente interpretativo"),
        ("no_retrospective_change", True, "estado 4E-4H preservado"),
        ("non_causal_interpretation", True, "contribuição não é efeito causal"),
        ("post_final_evaluation", True, "população 2025 já avaliada e congelada"),
    )
    table = pl.DataFrame(
        {
            "check": [name for name, _, _ in checks],
            "status": ["PASS" if passed else "FAIL" for _, passed, _ in checks],
            "details": [details for _, _, details in checks],
        }
    )
    failures = table.filter(pl.col("status") == "FAIL")
    if not failures.is_empty():
        raise ValueError(f"Checklist 4I falhou: {failures.to_dicts()}")
    return table


def write_final_interpretation_tables(
    result: FinalInterpretationResult,
    tables_dir: Path = TABLES_DIR,
) -> tuple[Path, ...]:
    tables = (
        ("phase_4i_global_feature_contributions.csv", result.global_contributions),
        ("phase_4i_transformed_feature_contributions.csv", result.transformed_contributions),
        ("phase_4i_error_analysis.csv", result.error_analysis),
        ("phase_4i_contributions_by_outcome.csv", result.contributions_by_outcome),
        ("phase_4i_interpretation_summary.csv", result.summary),
        ("phase_4i_interpretation_checklist.csv", result.checklist),
    )
    tables_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, table in tables:
        destination = tables_dir / filename
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.stem}.", suffix=".tmp", dir=tables_dir
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            table.write_csv(temporary)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        written.append(destination)
    return tuple(written)


def run_final_interpretation(
    analytical_path: Path = PRIMARY_ANALYTICAL_PARQUET_PATH,
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
    tables_dir: Path = TABLES_DIR,
    project_root: Path = PROJECT_ROOT,
) -> FinalInterpretationRun:
    sources = load_final_interpretation_sources(tables_dir)
    contract = validate_final_interpretation_sources(sources)
    pipeline, _ = load_validated_frozen_pipeline(sources.final_model_manifest, project_root)
    predictions = load_and_validate_final_predictions(contract, project_root)
    groups = load_preprocessing_groups(schema_path)
    holdout = load_final_holdout(analytical_path, groups.predictors)
    partition = {
        "rows": contract.final_rows,
        "severe": contract.final_positive,
        "non_severe": contract.final_negative,
    }
    validate_final_holdout(holdout, groups, partition)
    holdout = align_holdout_to_predictions(holdout, predictions)
    transformed = transform_interpretation_population(pipeline, holdout, groups.predictors)
    preprocessor = pipeline.named_steps["preprocessor"]
    mapping = build_transformed_feature_mapping(preprocessor, groups)
    official_probabilities = predictions["predicted_probability_grave"].to_numpy()
    audit = calculate_native_contributions(pipeline, transformed, official_probabilities)
    global_contributions, transformed_contributions = build_contribution_tables(
        audit.feature_contributions, mapping
    )
    error_analysis, outcomes = build_error_analysis(predictions)
    contributions_by_outcome = build_contributions_by_outcome(
        audit.feature_contributions, mapping, outcomes
    )
    summary = build_interpretation_summary(contract, audit, global_contributions)
    checklist = build_interpretation_checklist(
        contract,
        audit,
        mapping,
        global_contributions,
        transformed_contributions,
        error_analysis,
    )
    result = FinalInterpretationResult(
        contract=contract,
        global_contributions=global_contributions,
        transformed_contributions=transformed_contributions,
        error_analysis=error_analysis,
        contributions_by_outcome=contributions_by_outcome,
        summary=summary,
        checklist=checklist,
    )
    return FinalInterpretationRun(result, write_final_interpretation_tables(result, tables_dir))
