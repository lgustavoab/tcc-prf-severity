from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from polars.exceptions import ColumnNotFoundError

from tcc_prf_severity.config import EXPERIMENTAL_CONTRACT_PATH, PROJECT_ROOT, TABLES_DIR
from tcc_prf_severity.modeling.model_comparison import (
    LOGISTIC_MODEL_ID,
    RANDOM_FOREST_MODEL_ID,
    XGBOOST_MODEL_ID,
)

EXPECTED_MODEL_IDS = {LOGISTIC_MODEL_ID, RANDOM_FOREST_MODEL_ID, XGBOOST_MODEL_ID}
EXPECTED_FOLDS = (1, 2, 3)
EXPECTED_VALIDATION_YEARS = (2022, 2023, 2024)
SUMMARY_PRIMARY_METRIC = "Average Precision (AP)"
SELECTION_METRIC = "Average Precision"
SELECTION_AGGREGATION = "unweighted_fold_mean"
EXPERIMENTAL_AGGREGATION = "unweighted_mean_AP_plus_std_and_latest_fold"
PREMODELING_ACCEPTANCE_PATH = PROJECT_ROOT / "docs" / "PHASE_3_PREMODELING_ACCEPTANCE.md"
MODEL_COMPARISON_DOCUMENT_PATH = PROJECT_ROOT / "docs" / "PHASE_4D_MODEL_COMPARISON.md"


@dataclass(frozen=True)
class ModelSelectionInputs:
    comparison: pl.DataFrame
    fold_comparison: pl.DataFrame
    pairwise_ap_deltas: pl.DataFrame
    temporal_stability: pl.DataFrame
    experimental_contract: dict[str, str]
    model_contracts: dict[str, dict[str, str]]


@dataclass(frozen=True)
class ModelSelectionResult:
    selected_model_id: str
    selection: pl.DataFrame
    checklist: pl.DataFrame
    comparison: pl.DataFrame


@dataclass(frozen=True)
class ModelSelectionRun:
    result: ModelSelectionResult
    table_paths: tuple[Path, ...]


MODEL_CONTRACT_FILENAMES = {
    LOGISTIC_MODEL_ID: "phase_4a_logistic_model_contract.csv",
    RANDOM_FOREST_MODEL_ID: "phase_4b_random_forest_model_contract.csv",
    XGBOOST_MODEL_ID: "phase_4c_xgboost_model_contract.csv",
}


def _key_value_mapping(table: pl.DataFrame, source: str) -> dict[str, str]:
    if not {"key", "value"}.issubset(table.columns):
        raise ValueError(f"Tabela key/value inválida: {source}.")
    selected = table.select("key", "value")
    if selected.get_column("key").n_unique() != selected.height:
        raise ValueError(f"Chaves duplicadas em {source}.")
    return {str(row["key"]): str(row["value"]) for row in selected.iter_rows(named=True)}


def load_model_selection_inputs(
    tables_dir: Path = TABLES_DIR,
    experimental_contract_path: Path = EXPERIMENTAL_CONTRACT_PATH,
) -> ModelSelectionInputs:
    paths = {
        "comparison": tables_dir / "phase_4d_model_comparison.csv",
        "fold": tables_dir / "phase_4d_fold_comparison.csv",
        "deltas": tables_dir / "phase_4d_pairwise_ap_deltas.csv",
        "stability": tables_dir / "phase_4d_temporal_stability.csv",
        "experimental": experimental_contract_path,
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    contract_paths = {
        model_id: tables_dir / filename for model_id, filename in MODEL_CONTRACT_FILENAMES.items()
    }
    missing.extend(str(path) for path in contract_paths.values() if not path.is_file())
    if missing:
        raise FileNotFoundError(f"Fontes autoritativas ausentes: {missing}")
    return ModelSelectionInputs(
        comparison=pl.read_csv(paths["comparison"]),
        fold_comparison=pl.read_csv(paths["fold"]),
        pairwise_ap_deltas=pl.read_csv(paths["deltas"]),
        temporal_stability=pl.read_csv(paths["stability"]),
        experimental_contract=_key_value_mapping(
            pl.read_csv(paths["experimental"]), str(paths["experimental"])
        ),
        model_contracts={
            model_id: _key_value_mapping(pl.read_csv(path), str(path))
            for model_id, path in contract_paths.items()
        },
    )


def _select_primary_rank_row(comparison: pl.DataFrame) -> dict[str, Any]:
    required = {
        "model_id",
        "model_family",
        "ap_fold1",
        "ap_fold2",
        "ap_fold3",
        "ap_unweighted_mean",
        "ap_population_std",
        "mean_roc_auc",
        "mean_brier_score",
        "primary_metric_rank",
        "ap_fold3_rank",
        "ap_std_rank",
    }
    missing = sorted(required - set(comparison.columns))
    if missing:
        raise ValueError(f"Comparação 4D sem colunas obrigatórias: {missing}")
    maximum = comparison.get_column("ap_unweighted_mean").max()
    if not isinstance(maximum, (int, float)):
        raise ValueError("AP média máxima inválida na comparação 4D.")
    argmax = comparison.filter(pl.col("ap_unweighted_mean") == maximum)
    if argmax.height != 1:
        raise ValueError("Empate exato na maior AP média; seleção interrompida sem desempate.")
    rank_one = comparison.filter(pl.col("primary_metric_rank") == 1)
    if rank_one.height != 1:
        raise ValueError("primary_metric_rank == 1 deve identificar exatamente um modelo.")
    argmax_id = str(argmax.get_column("model_id").item())
    rank_id = str(rank_one.get_column("model_id").item())
    if argmax_id != rank_id:
        raise ValueError("Argmax da AP média e primary_metric_rank == 1 não coincidem.")
    return argmax.row(0, named=True)


def _fold_summaries_are_consistent(inputs: ModelSelectionInputs) -> bool:
    try:
        if inputs.fold_comparison.height != 9:
            return False
        for row in inputs.comparison.iter_rows(named=True):
            model_id = str(row["model_id"])
            folds = inputs.fold_comparison.filter(pl.col("model_id") == model_id).sort("fold")
            if tuple(folds.get_column("fold")) != EXPECTED_FOLDS:
                return False
            ap = folds.get_column("average_precision").to_numpy()
            observed = (
                float(row["ap_fold1"]),
                float(row["ap_fold2"]),
                float(row["ap_fold3"]),
                float(row["ap_unweighted_mean"]),
                float(row["ap_population_std"]),
                float(row["mean_roc_auc"]),
                float(row["mean_brier_score"]),
            )
            expected = (
                float(ap[0]),
                float(ap[1]),
                float(ap[2]),
                float(np.mean(ap)),
                float(np.std(ap, ddof=0)),
                float(np.mean(folds.get_column("roc_auc").to_numpy())),
                float(np.mean(folds.get_column("brier_score").to_numpy())),
            )
            if not np.allclose(observed, expected, rtol=0.0, atol=1e-15):
                return False
        return True
    except ColumnNotFoundError, TypeError, ValueError, IndexError:
        return False


def _stability_is_consistent(inputs: ModelSelectionInputs) -> bool:
    try:
        if inputs.temporal_stability.height != 3:
            return False
        for row in inputs.comparison.iter_rows(named=True):
            model_id = str(row["model_id"])
            stability = inputs.temporal_stability.filter(pl.col("model_id") == model_id)
            if stability.height != 1:
                return False
            aps = np.asarray([row["ap_fold1"], row["ap_fold2"], row["ap_fold3"]], dtype=float)
            values = stability.row(0, named=True)
            observed = (
                float(values["ap_min"]),
                float(values["ap_max"]),
                float(values["ap_range"]),
                float(values["ap_population_std"]),
                float(values["fold1_to_fold2_delta"]),
                float(values["fold2_to_fold3_delta"]),
            )
            expected = (
                float(np.min(aps)),
                float(np.max(aps)),
                float(np.max(aps) - np.min(aps)),
                float(np.std(aps, ddof=0)),
                float(aps[1] - aps[0]),
                float(aps[2] - aps[1]),
            )
            if not np.allclose(observed, expected, rtol=0.0, atol=1e-15):
                return False
        return True
    except ColumnNotFoundError, KeyError, TypeError, ValueError:
        return False


def _deltas_are_consistent(inputs: ModelSelectionInputs) -> bool:
    try:
        if inputs.pairwise_ap_deltas.height != 3:
            return False
        metrics = {str(row["model_id"]): row for row in inputs.comparison.iter_rows(named=True)}
        for row in inputs.pairwise_ap_deltas.iter_rows(named=True):
            a = metrics[str(row["model_a"])]
            b = metrics[str(row["model_b"])]
            observed = np.asarray(
                [
                    row["ap_delta_fold1"],
                    row["ap_delta_fold2"],
                    row["ap_delta_fold3"],
                    row["ap_mean_delta"],
                ],
                dtype=float,
            )
            expected = np.asarray(
                [
                    float(b["ap_fold1"]) - float(a["ap_fold1"]),
                    float(b["ap_fold2"]) - float(a["ap_fold2"]),
                    float(b["ap_fold3"]) - float(a["ap_fold3"]),
                    float(b["ap_unweighted_mean"]) - float(a["ap_unweighted_mean"]),
                ]
            )
            if not np.allclose(observed, expected, rtol=0.0, atol=1e-15):
                return False
        return True
    except ColumnNotFoundError, KeyError, TypeError, ValueError:
        return False


def _selected_contract_is_valid(
    selected: dict[str, Any], contracts: dict[str, dict[str, str]]
) -> bool:
    model_id = str(selected["model_id"])
    contract = contracts.get(model_id)
    if contract is None:
        return False
    expected = {
        "model_family": str(selected["model_family"]),
        "preprocessing": "phase_3e",
        "validation": "expanding_window_3_folds",
        "primary_metric": SELECTION_METRIC,
        "model_selection_aggregation": SELECTION_AGGREGATION,
        "threshold_policy": "not_selected_0.5_reference_only",
        "final_test_year": "2025_reserved",
    }
    return bool(contract.get("role")) and all(
        contract.get(key) == value for key, value in expected.items()
    )


def build_selection_checklist(
    inputs: ModelSelectionInputs,
    selected: dict[str, Any] | None = None,
) -> pl.DataFrame:
    """Produz checks auditáveis; a seleção só é publicada quando todos passam."""
    comparison = inputs.comparison
    model_ids = (
        set(comparison.get_column("model_id")) if "model_id" in comparison.columns else set()
    )
    folds = (
        set(inputs.fold_comparison.get_column("fold"))
        if "fold" in inputs.fold_comparison.columns
        else set()
    )
    validation_years = (
        set(inputs.fold_comparison.get_column("validation_year"))
        if "validation_year" in inputs.fold_comparison.columns
        else set()
    )
    rank_one = (
        comparison.filter(pl.col("primary_metric_rank") == 1)
        if "primary_metric_rank" in comparison.columns
        else pl.DataFrame()
    )
    metric_ok = inputs.experimental_contract.get("primary_metric") == SUMMARY_PRIMARY_METRIC
    aggregation_ok = (
        inputs.experimental_contract.get("fold_aggregation") == EXPERIMENTAL_AGGREGATION
    )
    rank_argmax_ok = False
    if selected is not None and rank_one.height == 1:
        rank_argmax_ok = str(rank_one.get_column("model_id").item()) == str(selected["model_id"])

    contract_ok = selected is not None and _selected_contract_is_valid(
        selected, inputs.model_contracts
    )
    checks = (
        (
            "SEL001",
            "exatamente três modelos",
            "3 modelos esperados",
            f"{len(model_ids)} modelos",
            comparison.height == 3 and model_ids == EXPECTED_MODEL_IDS,
            "phase_4d_model_comparison.csv",
        ),
        (
            "SEL002",
            "exatamente três folds",
            "folds 1,2,3 para cada modelo",
            f"folds={sorted(folds)}; linhas={inputs.fold_comparison.height}",
            folds == set(EXPECTED_FOLDS) and inputs.fold_comparison.height == 9,
            "phase_4d_fold_comparison.csv",
        ),
        (
            "SEL003",
            "2025 ausente das validações internas",
            "2022,2023,2024",
            ",".join(str(year) for year in sorted(validation_years)),
            validation_years == set(EXPECTED_VALIDATION_YEARS),
            "phase_4d_fold_comparison.csv",
        ),
        (
            "SEL004",
            "métrica primária congelada",
            SUMMARY_PRIMARY_METRIC,
            inputs.experimental_contract.get("primary_metric", "ausente"),
            metric_ok,
            "phase_3d_experimental_contract.csv",
        ),
        (
            "SEL005",
            "agregação principal congelada",
            EXPERIMENTAL_AGGREGATION,
            inputs.experimental_contract.get("fold_aggregation", "ausente"),
            aggregation_ok,
            "phase_3d_experimental_contract.csv",
        ),
        (
            "SEL006",
            "rank primário único",
            "um modelo com rank 1",
            f"{rank_one.height} modelo(s)",
            rank_one.height == 1,
            "phase_4d_model_comparison.csv",
        ),
        (
            "SEL007",
            "rank e argmax da AP média coincidem",
            "mesmo model_id",
            str(selected["model_id"]) if selected else "indeterminado",
            rank_argmax_ok,
            "phase_4d_model_comparison.csv",
        ),
        (
            "SEL008",
            "summaries 4D consistentes",
            "folds, médias, std e métricas reconciliados",
            "consistente" if _fold_summaries_are_consistent(inputs) else "divergente",
            _fold_summaries_are_consistent(inputs)
            and _stability_is_consistent(inputs)
            and _deltas_are_consistent(inputs),
            "phase_4d_*",
        ),
        (
            "SEL009",
            "selecionado possui contrato versionado",
            "contrato compatível",
            "compatível" if contract_ok else "divergente ou ausente",
            contract_ok,
            MODEL_CONTRACT_FILENAMES.get(str(selected["model_id"]), "ausente")
            if selected
            else "ausente",
        ),
        ("SEL010", "nenhum threshold selecionado", "false", "false", True, "escopo da Fase 4E"),
        ("SEL011", "nenhum refit realizado", "false", "false", True, "escopo da Fase 4E"),
        ("SEL012", "nenhum tuning posterior", "false", "false", True, "escopo da Fase 4E"),
        (
            "SEL013",
            "nenhum resultado de 2025",
            "2025_reserved",
            inputs.experimental_contract.get("final_holdout_policy", "ausente"),
            inputs.experimental_contract.get("final_holdout_policy")
            == "no_optimization_or_fit_on_2025"
            and 2025 not in validation_years,
            "contrato 3D e tabelas 4D",
        ),
    )
    return pl.DataFrame(
        {
            "check_id": check_id,
            "check": check,
            "expected": expected,
            "observed": observed,
            "status": "PASS" if passed else "FAIL",
            "evidence": evidence,
        }
        for check_id, check, expected, observed, passed, evidence in checks
    )


def _selection_table(selected: dict[str, Any], inputs: ModelSelectionInputs) -> pl.DataFrame:
    selected_id = str(selected["model_id"])
    contract = inputs.model_contracts[selected_id]
    means = {
        str(row["model_id"]): float(row["ap_unweighted_mean"])
        for row in inputs.comparison.iter_rows(named=True)
    }
    values: tuple[tuple[str, str | float | int | bool], ...] = (
        ("selection_status", "selected"),
        ("selected_model_id", selected_id),
        ("selected_model_family", str(selected["model_family"])),
        ("selected_model_role", contract["role"]),
        ("selection_metric", SELECTION_METRIC),
        ("selection_aggregation", SELECTION_AGGREGATION),
        ("selected_ap_fold1", float(selected["ap_fold1"])),
        ("selected_ap_fold2", float(selected["ap_fold2"])),
        ("selected_ap_fold3", float(selected["ap_fold3"])),
        ("selected_ap_unweighted_mean", float(selected["ap_unweighted_mean"])),
        ("selected_ap_population_std", float(selected["ap_population_std"])),
        ("selected_mean_roc_auc", float(selected["mean_roc_auc"])),
        ("selected_mean_brier_score", float(selected["mean_brier_score"])),
        ("primary_metric_rank", int(selected["primary_metric_rank"])),
        ("ap_fold3_rank", int(selected["ap_fold3_rank"])),
        ("ap_std_rank", int(selected["ap_std_rank"])),
        ("delta_vs_logistic_ap_mean", means[selected_id] - means[LOGISTIC_MODEL_ID]),
        ("delta_vs_random_forest_ap_mean", means[selected_id] - means[RANDOM_FOREST_MODEL_ID]),
        ("development_period", "2021-2024"),
        ("internal_validation_years", "2022,2023,2024"),
        ("final_test_year", "2025_reserved"),
        ("final_test_used", False),
        ("threshold_selected", False),
        ("refit_performed", False),
        ("hyperparameter_tuning_after_comparison", False),
    )
    serialized = [
        str(value).lower() if isinstance(value, bool) else str(value) for _, value in values
    ]
    return pl.DataFrame({"key": [key for key, _ in values], "value": serialized})


def select_model(inputs: ModelSelectionInputs) -> ModelSelectionResult:
    """Seleciona exclusivamente pelo maior AP mean, sem desempate retrospectivo."""
    selected = _select_primary_rank_row(inputs.comparison)
    checklist = build_selection_checklist(inputs, selected)
    failures = checklist.filter(pl.col("status") == "FAIL")
    if not failures.is_empty():
        failed_ids = failures.get_column("check_id").to_list()
        raise ValueError(f"Seleção formal bloqueada por checks críticos: {failed_ids}")
    return ModelSelectionResult(
        selected_model_id=str(selected["model_id"]),
        selection=_selection_table(selected, inputs),
        checklist=checklist,
        comparison=inputs.comparison,
    )


def write_model_selection_tables(
    result: ModelSelectionResult, tables_dir: Path
) -> tuple[Path, ...]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (result.selection, "phase_4e_model_selection.csv"),
        (result.checklist, "phase_4e_selection_checklist.csv"),
    )
    for table, filename in outputs:
        table.write_csv(tables_dir / filename)
    return tuple(tables_dir / filename for _, filename in outputs)


def run_model_selection(
    source_tables_dir: Path = TABLES_DIR,
    output_tables_dir: Path = TABLES_DIR,
    experimental_contract_path: Path = EXPERIMENTAL_CONTRACT_PATH,
    premodeling_acceptance_path: Path = PREMODELING_ACCEPTANCE_PATH,
    model_comparison_document_path: Path = MODEL_COMPARISON_DOCUMENT_PATH,
) -> ModelSelectionRun:
    """Seleciona por tabelas publicadas, sem carregar dataset, OOF ou estimadores."""
    for path, label in (
        (premodeling_acceptance_path, "Aceite pré-modelagem"),
        (model_comparison_document_path, "Documento de comparação 4D"),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"{label} ausente: {path}")
    inputs = load_model_selection_inputs(source_tables_dir, experimental_contract_path)
    result = select_model(inputs)
    return ModelSelectionRun(
        result=result,
        table_paths=write_model_selection_tables(result, output_tables_dir),
    )
