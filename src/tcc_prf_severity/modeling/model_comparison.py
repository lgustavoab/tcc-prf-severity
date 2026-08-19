from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

from tcc_prf_severity.config import EXPERIMENTAL_CONTRACT_PATH, PROJECT_ROOT, TABLES_DIR

EXPECTED_FOLDS = (1, 2, 3)
EXPECTED_VALIDATION_YEARS = (2022, 2023, 2024)
SUMMARY_PRIMARY_METRIC = "Average Precision (AP)"
CONTRACT_PRIMARY_METRIC = "Average Precision"
MODEL_SELECTION_AGGREGATION = "unweighted_fold_mean"
PREMODELING_ACCEPTANCE_PATH = PROJECT_ROOT / "docs" / "PHASE_3_PREMODELING_ACCEPTANCE.md"

LOGISTIC_MODEL_ID = "phase_4a_logistic_baseline"
RANDOM_FOREST_MODEL_ID = "phase_4b_random_forest_baseline"
XGBOOST_MODEL_ID = "phase_4c_xgboost_baseline"


@dataclass(frozen=True)
class PublishedModel:
    model_id: str
    model_family: str
    fold_metrics: pl.DataFrame
    summary: dict[str, str]
    contract: dict[str, str]


@dataclass(frozen=True)
class ModelComparisonResult:
    model_comparison: pl.DataFrame
    fold_comparison: pl.DataFrame
    pairwise_ap_deltas: pl.DataFrame
    temporal_stability: pl.DataFrame
    final_selection_performed: bool = False
    final_test_used: bool = False


@dataclass(frozen=True)
class ModelComparisonRun:
    result: ModelComparisonResult
    table_paths: tuple[Path, ...]


MODEL_ARTIFACT_PREFIXES = (
    "phase_4a_logistic",
    "phase_4b_random_forest",
    "phase_4c_xgboost",
)


def _key_value_mapping(table: pl.DataFrame, source: str) -> dict[str, str]:
    if table.columns != ["key", "value"] or table.get_column("key").n_unique() != table.height:
        raise ValueError(f"Tabela key/value inválida: {source}.")
    return {str(row["key"]): str(row["value"]) for row in table.iter_rows(named=True)}


def load_published_models(tables_dir: Path = TABLES_DIR) -> tuple[PublishedModel, ...]:
    models: list[PublishedModel] = []
    for prefix in MODEL_ARTIFACT_PREFIXES:
        paths = {
            "fold": tables_dir / f"{prefix}_fold_metrics.csv",
            "summary": tables_dir / f"{prefix}_summary.csv",
            "contract": tables_dir / f"{prefix}_model_contract.csv",
        }
        missing = [str(path) for path in paths.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Artefatos publicados ausentes: {missing}")
        summary = _key_value_mapping(pl.read_csv(paths["summary"]), str(paths["summary"]))
        contract = _key_value_mapping(pl.read_csv(paths["contract"]), str(paths["contract"]))
        models.append(
            PublishedModel(
                model_id=summary.get("model_id", ""),
                model_family=contract.get("model_family", ""),
                fold_metrics=pl.read_csv(paths["fold"]),
                summary=summary,
                contract=contract,
            )
        )
    return tuple(models)


def _require_keys(mapping: dict[str, str], keys: tuple[str, ...], source: str) -> None:
    missing = sorted(set(keys) - set(mapping))
    if missing:
        raise ValueError(f"{source} sem campos obrigatórios: {missing}")


def _validate_experimental_contract(experimental_contract: pl.DataFrame) -> None:
    if not {"key", "value"}.issubset(experimental_contract.columns):
        raise ValueError("Contrato experimental 3D sem colunas key/value.")
    contract = {
        str(row["key"]): str(row["value"])
        for row in experimental_contract.select("key", "value").iter_rows(named=True)
    }
    expected = {
        "number_of_internal_folds": "3",
        "primary_metric": SUMMARY_PRIMARY_METRIC,
        "fold_aggregation": "unweighted_mean_AP_plus_std_and_latest_fold",
        "final_holdout_policy": "no_optimization_or_fit_on_2025",
    }
    divergences = {
        key: (contract.get(key), value)
        for key, value in expected.items()
        if contract.get(key) != value
    }
    if divergences:
        raise ValueError(f"Contrato experimental 3D incompatível com a comparação: {divergences}")


def validate_model_comparability(
    models: tuple[PublishedModel, ...],
    experimental_contract: pl.DataFrame,
) -> None:
    """Falha antes da comparação se os três experimentos não forem comparáveis."""
    if len(models) != 3:
        raise ValueError("A comparação formal exige exatamente três modelos publicados.")
    expected_ids = {LOGISTIC_MODEL_ID, RANDOM_FOREST_MODEL_ID, XGBOOST_MODEL_ID}
    model_ids = {model.model_id for model in models}
    if model_ids != expected_ids:
        raise ValueError(
            f"Conjunto de modelos divergente: esperado {expected_ids}, obtido {model_ids}."
        )
    _validate_experimental_contract(experimental_contract)

    required_fold_columns = {
        "fold",
        "train_years",
        "validation_year",
        "train_rows",
        "validation_rows",
        "output_feature_count",
        "validation_positive_rate",
        "average_precision",
        "roc_auc",
        "brier_score",
    }
    summary_keys = (
        "fold_count",
        "primary_metric",
        "ap_unweighted_mean",
        "ap_population_std",
        "ap_fold3",
        "mean_roc_auc",
        "mean_brier_score",
        "final_test_used",
        "threshold_selected",
    )
    contract_keys = ("primary_metric", "model_selection_aggregation", "final_test_year")
    structural_columns = (
        "fold",
        "train_years",
        "validation_year",
        "train_rows",
        "validation_rows",
        "validation_positive_rate",
        "output_feature_count",
    )
    reference_structure: pl.DataFrame | None = None

    for model in models:
        missing_columns = sorted(required_fold_columns - set(model.fold_metrics.columns))
        if missing_columns:
            raise ValueError(f"{model.model_id} sem colunas por fold: {missing_columns}")
        _require_keys(model.summary, summary_keys, f"Summary de {model.model_id}")
        _require_keys(model.contract, contract_keys, f"Contrato de {model.model_id}")
        folds = model.fold_metrics.sort("fold")
        if tuple(folds.get_column("fold")) != EXPECTED_FOLDS or folds.height != 3:
            raise ValueError(f"{model.model_id} não contém exatamente os três folds congelados.")
        if tuple(folds.get_column("validation_year")) != EXPECTED_VALIDATION_YEARS:
            raise ValueError(f"{model.model_id} possui anos de validação divergentes.")
        if 2025 in folds.get_column("validation_year"):
            raise ValueError("2025 é proibido na comparação interna da Fase 4D.")
        if model.summary["fold_count"] != "3":
            raise ValueError(f"Summary de {model.model_id} não confirma três folds.")
        if model.summary["primary_metric"] != SUMMARY_PRIMARY_METRIC:
            raise ValueError(f"Métrica primária divergente em {model.model_id}.")
        if model.contract["primary_metric"] != CONTRACT_PRIMARY_METRIC:
            raise ValueError(f"Contrato de métrica primária divergente em {model.model_id}.")
        if model.contract["model_selection_aggregation"] != MODEL_SELECTION_AGGREGATION:
            raise ValueError(f"Agregação principal divergente em {model.model_id}.")
        if model.contract["final_test_year"] != "2025_reserved":
            raise ValueError(f"Política de 2025 divergente em {model.model_id}.")
        if model.summary["final_test_used"] != "false":
            raise ValueError(f"{model.model_id} consultou o teste final.")
        if model.summary["threshold_selected"] != "false":
            raise ValueError(f"{model.model_id} selecionou threshold antes da 4D.")

        structure = folds.select(structural_columns)
        if reference_structure is None:
            reference_structure = structure
        elif not structure.equals(reference_structure):
            raise ValueError(f"Estrutura experimental de {model.model_id} não é comparável.")

        ap = folds.get_column("average_precision").to_numpy()
        expected_metrics = {
            "ap_unweighted_mean": float(np.mean(ap)),
            "ap_population_std": float(np.std(ap, ddof=0)),
            "ap_fold3": float(ap[2]),
            "mean_roc_auc": float(np.mean(folds.get_column("roc_auc").to_numpy())),
            "mean_brier_score": float(np.mean(folds.get_column("brier_score").to_numpy())),
        }
        for key, expected in expected_metrics.items():
            observed = float(model.summary[key])
            if not np.isclose(observed, expected, rtol=0.0, atol=1e-15):
                raise ValueError(
                    f"Summary de {model.model_id} diverge dos folds em {key}: "
                    f"{observed} != {expected}."
                )


def _model_comparison_table(models: tuple[PublishedModel, ...]) -> pl.DataFrame:
    rows: list[dict[str, str | float]] = []
    for model in models:
        folds = model.fold_metrics.sort("fold")
        ap = folds.get_column("average_precision").to_numpy()
        rows.append(
            {
                "model_id": model.model_id,
                "model_family": model.model_family,
                "ap_fold1": float(ap[0]),
                "ap_fold2": float(ap[1]),
                "ap_fold3": float(ap[2]),
                "ap_unweighted_mean": float(np.mean(ap)),
                "ap_population_std": float(np.std(ap, ddof=0)),
                "mean_roc_auc": float(np.mean(folds.get_column("roc_auc").to_numpy())),
                "mean_brier_score": float(np.mean(folds.get_column("brier_score").to_numpy())),
            }
        )
    return (
        pl.DataFrame(rows)
        .with_columns(
            pl.col("ap_unweighted_mean")
            .rank(method="min", descending=True)
            .cast(pl.Int64)
            .alias("primary_metric_rank"),
            pl.col("ap_fold3")
            .rank(method="min", descending=True)
            .cast(pl.Int64)
            .alias("ap_fold3_rank"),
            pl.col("ap_population_std").rank(method="min").cast(pl.Int64).alias("ap_std_rank"),
        )
        .sort("model_id")
    )


def _fold_comparison_table(models: tuple[PublishedModel, ...]) -> pl.DataFrame:
    tables = [
        model.fold_metrics.select(
            "fold",
            "validation_year",
            pl.lit(model.model_id).alias("model_id"),
            "average_precision",
            "roc_auc",
            "brier_score",
            "validation_positive_rate",
        )
        for model in models
    ]
    return pl.concat(tables, how="vertical").sort("fold", "model_id")


def _pairwise_ap_deltas_table(comparison: pl.DataFrame) -> pl.DataFrame:
    metrics = {str(row["model_id"]): row for row in comparison.iter_rows(named=True)}
    pairs = (
        (LOGISTIC_MODEL_ID, RANDOM_FOREST_MODEL_ID),
        (LOGISTIC_MODEL_ID, XGBOOST_MODEL_ID),
        (RANDOM_FOREST_MODEL_ID, XGBOOST_MODEL_ID),
    )
    rows = []
    for model_a, model_b in pairs:
        a = metrics[model_a]
        b = metrics[model_b]
        rows.append(
            {
                "model_a": model_a,
                "model_b": model_b,
                "ap_delta_fold1": float(b["ap_fold1"]) - float(a["ap_fold1"]),
                "ap_delta_fold2": float(b["ap_fold2"]) - float(a["ap_fold2"]),
                "ap_delta_fold3": float(b["ap_fold3"]) - float(a["ap_fold3"]),
                "ap_mean_delta": float(b["ap_unweighted_mean"]) - float(a["ap_unweighted_mean"]),
            }
        )
    return pl.DataFrame(rows)


def _temporal_stability_table(comparison: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for row in comparison.iter_rows(named=True):
        aps = np.asarray([row["ap_fold1"], row["ap_fold2"], row["ap_fold3"]], dtype=float)
        rows.append(
            {
                "model_id": str(row["model_id"]),
                "ap_min": float(np.min(aps)),
                "ap_max": float(np.max(aps)),
                "ap_range": float(np.max(aps) - np.min(aps)),
                "ap_population_std": float(np.std(aps, ddof=0)),
                "fold1_to_fold2_delta": float(aps[1] - aps[0]),
                "fold2_to_fold3_delta": float(aps[2] - aps[1]),
            }
        )
    return pl.DataFrame(rows).sort("model_id")


def compare_published_models(
    models: tuple[PublishedModel, ...],
    experimental_contract: pl.DataFrame,
) -> ModelComparisonResult:
    validate_model_comparability(models, experimental_contract)
    comparison = _model_comparison_table(models)
    return ModelComparisonResult(
        model_comparison=comparison,
        fold_comparison=_fold_comparison_table(models),
        pairwise_ap_deltas=_pairwise_ap_deltas_table(comparison),
        temporal_stability=_temporal_stability_table(comparison),
    )


def write_model_comparison_tables(
    result: ModelComparisonResult,
    tables_dir: Path,
) -> tuple[Path, ...]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (result.model_comparison, "phase_4d_model_comparison.csv"),
        (result.fold_comparison, "phase_4d_fold_comparison.csv"),
        (result.pairwise_ap_deltas, "phase_4d_pairwise_ap_deltas.csv"),
        (result.temporal_stability, "phase_4d_temporal_stability.csv"),
    )
    for table, filename in outputs:
        table.write_csv(tables_dir / filename)
    return tuple(tables_dir / filename for _, filename in outputs)


def run_model_comparison(
    source_tables_dir: Path = TABLES_DIR,
    output_tables_dir: Path = TABLES_DIR,
    experimental_contract_path: Path = EXPERIMENTAL_CONTRACT_PATH,
    premodeling_acceptance_path: Path = PREMODELING_ACCEPTANCE_PATH,
) -> ModelComparisonRun:
    """Compara somente resultados publicados, sem carregar dados ou treinar modelos."""
    if not experimental_contract_path.is_file():
        raise FileNotFoundError(f"Contrato experimental ausente: {experimental_contract_path}")
    if not premodeling_acceptance_path.is_file():
        raise FileNotFoundError(f"Aceite pré-modelagem ausente: {premodeling_acceptance_path}")
    models = load_published_models(source_tables_dir)
    result = compare_published_models(models, pl.read_csv(experimental_contract_path))
    return ModelComparisonRun(
        result=result,
        table_paths=write_model_comparison_tables(result, output_tables_dir),
    )
