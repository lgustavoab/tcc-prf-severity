from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from tcc_prf_severity.config import (
    EXPERIMENTAL_CONTRACT_PATH,
    PROJECT_ROOT,
    TABLES_DIR,
    XGBOOST_OOF_PREDICTIONS_PATH,
)
from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.modeling.model_comparison import XGBOOST_MODEL_ID

SELECTED_MODEL_FAMILY = "xgboost_gradient_boosted_trees"
EXPECTED_COLUMNS = (
    "id",
    "source_year",
    "fold",
    "target_grave",
    "predicted_probability_grave",
)
EXPECTED_YEAR_FOLDS = {2022: 1, 2023: 2, 2024: 3}
REFERENCE_THRESHOLD = 0.5
PHASE_4E_DOCUMENT_PATH = PROJECT_ROOT / "docs" / "PHASE_4E_MODEL_SELECTION.md"
PREMODELING_ACCEPTANCE_PATH = PROJECT_ROOT / "docs" / "PHASE_3_PREMODELING_ACCEPTANCE.md"


@dataclass(frozen=True)
class ThresholdMetrics:
    threshold: float
    rows: int
    actual_positive: int
    actual_negative: int
    predicted_positive: int
    predicted_negative: int
    precision: float
    recall: float
    f1: float
    tn: int
    fp: int
    fn: int
    tp: int


@dataclass(frozen=True)
class ThresholdSearch:
    candidate_count: int
    maximum_f1: float
    candidates_at_maximum_f1: int
    tie_break_recall_applied: bool
    tie_break_lower_threshold_applied: bool
    selected: ThresholdMetrics


@dataclass(frozen=True)
class ThresholdSelectionInputs:
    model_selection: dict[str, str]
    model_contract: dict[str, str]
    experimental_contract: dict[str, str]
    fold_metrics: pl.DataFrame
    oof: pl.DataFrame
    oof_sha256: str


@dataclass(frozen=True)
class ThresholdSelectionResult:
    selected_model_id: str
    selected_model_family: str
    oof_sha256: str
    search: ThresholdSearch
    reference: ThresholdMetrics
    selection: pl.DataFrame
    evaluation: pl.DataFrame
    search_summary: pl.DataFrame
    checklist: pl.DataFrame


@dataclass(frozen=True)
class ThresholdSelectionRun:
    result: ThresholdSelectionResult
    table_paths: tuple[Path, ...]


def _key_value_mapping(table: pl.DataFrame, source: str) -> dict[str, str]:
    if not {"key", "value"}.issubset(table.columns):
        raise ValueError(f"Tabela key/value inválida: {source}.")
    selected = table.select("key", "value")
    if selected.get_column("key").n_unique() != selected.height:
        raise ValueError(f"Chaves duplicadas em {source}.")
    return {str(row["key"]): str(row["value"]) for row in selected.iter_rows(named=True)}


def load_threshold_selection_inputs(
    tables_dir: Path = TABLES_DIR,
    oof_path: Path = XGBOOST_OOF_PREDICTIONS_PATH,
    experimental_contract_path: Path = EXPERIMENTAL_CONTRACT_PATH,
    phase_4e_document_path: Path = PHASE_4E_DOCUMENT_PATH,
    premodeling_acceptance_path: Path = PREMODELING_ACCEPTANCE_PATH,
) -> ThresholdSelectionInputs:
    paths = {
        "seleção 4E": tables_dir / "phase_4e_model_selection.csv",
        "contrato XGBoost 4C": tables_dir / "phase_4c_xgboost_model_contract.csv",
        "métricas XGBoost 4C": tables_dir / "phase_4c_xgboost_fold_metrics.csv",
        "contrato experimental 3D": experimental_contract_path,
        "documento 4E": phase_4e_document_path,
        "aceite pré-modelagem 3F": premodeling_acceptance_path,
    }
    missing = [f"{name}: {path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Fontes autoritativas ausentes: {missing}")
    if not oof_path.is_file():
        raise FileNotFoundError(
            "OOF XGBoost 4C ausente. Reproduza explicitamente a Fase 4C com "
            "`uv run prf-run-xgboost-baseline` para materializar o OOF; a Fase 4F não treina "
            "modelos silenciosamente."
        )
    return ThresholdSelectionInputs(
        model_selection=_key_value_mapping(
            pl.read_csv(paths["seleção 4E"]), str(paths["seleção 4E"])
        ),
        model_contract=_key_value_mapping(
            pl.read_csv(paths["contrato XGBoost 4C"]), str(paths["contrato XGBoost 4C"])
        ),
        experimental_contract=_key_value_mapping(
            pl.read_csv(paths["contrato experimental 3D"]),
            str(paths["contrato experimental 3D"]),
        ),
        fold_metrics=pl.read_csv(paths["métricas XGBoost 4C"]),
        oof=pl.read_parquet(oof_path),
        oof_sha256=sha256_file(oof_path),
    )


def validate_selected_model(inputs: ThresholdSelectionInputs) -> None:
    selection = inputs.model_selection
    expected_selection = {
        "selection_status": "selected",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "internal_validation_years": "2022,2023,2024",
        "final_test_year": "2025_reserved",
        "final_test_used": "false",
        "threshold_selected": "false",
        "refit_performed": "false",
    }
    divergences = {
        key: (selection.get(key), expected)
        for key, expected in expected_selection.items()
        if selection.get(key) != expected
    }
    if divergences:
        raise ValueError(
            f"A seleção 4E não autoriza a seleção de threshold do XGBoost 4C: {divergences}."
        )
    contract = inputs.model_contract
    expected_contract = {
        "model_family": SELECTED_MODEL_FAMILY,
        "preprocessing": "phase_3e",
        "validation": "expanding_window_3_folds",
        "primary_metric": "Average Precision",
        "model_selection_aggregation": "unweighted_fold_mean",
        "threshold_policy": "not_selected_0.5_reference_only",
        "final_test_year": "2025_reserved",
    }
    contract_divergences = {
        key: (contract.get(key), expected)
        for key, expected in expected_contract.items()
        if contract.get(key) != expected
    }
    experimental = inputs.experimental_contract
    expected_experimental = {
        "threshold_selection_source": "temporal_OOF_2022_2024",
        "threshold_objective": "maximize_positive_class_F1",
        "threshold_tie_break": "higher_recall_then_lower_threshold",
        "final_holdout_policy": "no_optimization_or_fit_on_2025",
    }
    experimental_divergences = {
        key: (experimental.get(key), expected)
        for key, expected in expected_experimental.items()
        if experimental.get(key) != expected
    }
    if contract_divergences or experimental_divergences:
        raise ValueError(
            "Contratos congelados 3D/4C divergentes: "
            f"4C={contract_divergences}; 3D={experimental_divergences}."
        )


def validate_oof(inputs: ThresholdSelectionInputs) -> None:
    oof = inputs.oof
    if tuple(oof.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Colunas do OOF devem ser exatamente {EXPECTED_COLUMNS}; observadas {oof.columns}."
        )
    if oof.is_empty():
        raise ValueError("OOF XGBoost 4C vazio.")
    if any(value != 0 for value in oof.null_count().row(0)):
        raise ValueError("OOF contém valores nulos.")
    if oof.get_column("id").n_unique() != oof.height:
        raise ValueError("IDs do OOF não são únicos.")
    years = set(oof.get_column("source_year").unique().to_list())
    if years != set(EXPECTED_YEAR_FOLDS):
        raise ValueError(
            f"OOF deve conter somente e integralmente 2022-2024; anos observados: {sorted(years)}."
        )
    observed_pairs = {
        (int(row["source_year"]), int(row["fold"]))
        for row in oof.select("source_year", "fold").unique().iter_rows(named=True)
    }
    expected_pairs = set(EXPECTED_YEAR_FOLDS.items())
    if observed_pairs != expected_pairs:
        raise ValueError(
            f"Mapeamento ano/fold inválido: {sorted(observed_pairs)}; "
            f"esperado {sorted(expected_pairs)}."
        )
    if oof.schema["target_grave"] != pl.Boolean:
        raise ValueError("target_grave deve possuir dtype booleano.")
    probability_dtype = oof.schema["predicted_probability_grave"]
    if not probability_dtype.is_numeric():
        raise ValueError("predicted_probability_grave deve possuir dtype numérico.")
    probabilities = oof.get_column("predicted_probability_grave")
    if not probabilities.is_finite().all():
        raise ValueError("Probabilidades do OOF devem ser finitas.")
    if not probabilities.is_between(0.0, 1.0, closed="both").all():
        raise ValueError("Probabilidades do OOF devem pertencer ao intervalo [0, 1].")

    required_fold_columns = {"fold", "validation_year", "validation_rows"}
    if not required_fold_columns.issubset(inputs.fold_metrics.columns):
        raise ValueError(
            "Métricas 4C sem colunas para reconciliar OOF: "
            f"{sorted(required_fold_columns - set(inputs.fold_metrics.columns))}."
        )
    expected_counts = {
        (int(row["validation_year"]), int(row["fold"])): int(row["validation_rows"])
        for row in inputs.fold_metrics.iter_rows(named=True)
    }
    observed_counts = {
        (int(row["source_year"]), int(row["fold"])): int(row["len"])
        for row in oof.group_by("source_year", "fold").len().iter_rows(named=True)
    }
    if expected_counts != observed_counts:
        raise ValueError(
            "Contagens do OOF não reconciliam com as métricas 4C: "
            f"OOF={observed_counts}; métricas={expected_counts}."
        )


def evaluate_threshold(
    probabilities: np.ndarray[Any, np.dtype[np.float64]],
    targets: np.ndarray[Any, np.dtype[np.bool_]],
    threshold: float,
) -> ThresholdMetrics:
    predicted = probabilities >= threshold
    tp = int(np.count_nonzero(predicted & targets))
    fp = int(np.count_nonzero(predicted & ~targets))
    fn = int(np.count_nonzero(~predicted & targets))
    tn = int(np.count_nonzero(~predicted & ~targets))
    actual_positive = tp + fn
    actual_negative = tn + fp
    predicted_positive = tp + fp
    predicted_negative = tn + fn
    precision = tp / predicted_positive if predicted_positive else 0.0
    recall = tp / actual_positive if actual_positive else 0.0
    f1_denominator = 2 * tp + fp + fn
    f1 = 2 * tp / f1_denominator if f1_denominator else 0.0
    return ThresholdMetrics(
        threshold=threshold,
        rows=int(probabilities.size),
        actual_positive=actual_positive,
        actual_negative=actual_negative,
        predicted_positive=predicted_positive,
        predicted_negative=predicted_negative,
        precision=precision,
        recall=recall,
        f1=f1,
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp,
    )


def search_unique_probability_thresholds(
    probabilities: np.ndarray[Any, np.dtype[np.float64]],
    targets: np.ndarray[Any, np.dtype[np.bool_]],
) -> ThresholdSearch:
    if probabilities.ndim != 1 or targets.ndim != 1 or probabilities.size != targets.size:
        raise ValueError("Probabilidades e targets devem ser vetores unidimensionais alinhados.")
    if probabilities.size == 0:
        raise ValueError("Não há observações para selecionar threshold.")
    order = np.argsort(-probabilities, kind="stable")
    sorted_probabilities = probabilities[order]
    sorted_targets = targets[order]
    group_ends = np.flatnonzero(
        np.concatenate((sorted_probabilities[:-1] != sorted_probabilities[1:], [True]))
    )
    cumulative_tp = np.cumsum(sorted_targets, dtype=np.int64)
    total_positive = int(cumulative_tp[-1])
    total_negative = int(probabilities.size) - total_positive

    maximum_candidates: list[tuple[int, int, int, int, float]] = []
    best_numerator = -1
    best_denominator = 1
    for group_end in group_ends:
        tp = int(cumulative_tp[group_end])
        fp = int(group_end) + 1 - tp
        fn = total_positive - tp
        tn = total_negative - fp
        threshold = float(sorted_probabilities[group_end])
        candidate = (tp, fp, fn, tn, threshold)
        numerator = 2 * tp
        denominator = numerator + fp + fn
        if best_numerator < 0 or numerator * best_denominator > best_numerator * denominator:
            best_numerator = numerator
            best_denominator = denominator
            maximum_candidates = [candidate]
        elif numerator * best_denominator == best_numerator * denominator:
            maximum_candidates.append(candidate)

    maximum_tp = max(candidate[0] for candidate in maximum_candidates)
    recall_winners = [candidate for candidate in maximum_candidates if candidate[0] == maximum_tp]
    selected_counts = min(recall_winners, key=lambda candidate: candidate[4])
    selected = evaluate_threshold(probabilities, targets, selected_counts[4])
    return ThresholdSearch(
        candidate_count=int(group_ends.size),
        maximum_f1=best_numerator / best_denominator if best_denominator else 0.0,
        candidates_at_maximum_f1=len(maximum_candidates),
        tie_break_recall_applied=(
            len(maximum_candidates) > 1
            and any(candidate[0] != maximum_tp for candidate in maximum_candidates)
        ),
        tie_break_lower_threshold_applied=len(recall_winners) > 1,
        selected=selected,
    )


def _metric_row(
    scope: str,
    validation_year: int | None,
    threshold_role: str,
    metrics: ThresholdMetrics,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "validation_year": validation_year,
        "threshold_role": threshold_role,
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


def _selection_table(
    inputs: ThresholdSelectionInputs,
    search: ThresholdSearch,
    reference: ThresholdMetrics,
) -> pl.DataFrame:
    selected = search.selected
    values: dict[str, object] = {
        "selection_status": "selected",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "threshold_objective": "F1_positive_class",
        "positive_class": "target_grave=True",
        "threshold_candidate_policy": "unique_oof_probabilities",
        "prediction_rule": "predicted_probability_grave>=threshold",
        "tie_break_1": "higher_recall",
        "tie_break_2": "lower_threshold",
        "oof_years": "2022,2023,2024",
        "oof_rows": selected.rows,
        "oof_unique_ids": inputs.oof.get_column("id").n_unique(),
        "oof_sha256": inputs.oof_sha256,
        "candidate_threshold_count": search.candidate_count,
        "max_f1_tie_count": search.candidates_at_maximum_f1,
        "selected_threshold": selected.threshold,
        "selected_precision": selected.precision,
        "selected_recall": selected.recall,
        "selected_f1": selected.f1,
        "selected_tn": selected.tn,
        "selected_fp": selected.fp,
        "selected_fn": selected.fn,
        "selected_tp": selected.tp,
        "reference_threshold": reference.threshold,
        "reference_precision": reference.precision,
        "reference_recall": reference.recall,
        "reference_f1": reference.f1,
        "final_test_year": "2025_reserved",
        "final_test_used": False,
        "refit_performed": False,
    }
    return pl.DataFrame(
        {"key": list(values), "value": [_string(value) for value in values.values()]}
    )


def _checklist(inputs: ThresholdSelectionInputs, search: ThresholdSearch) -> pl.DataFrame:
    selected = search.selected
    checks = (
        ("THR001", "Modelo selecionado é o XGBoost 4C", True, XGBOOST_MODEL_ID),
        (
            "THR002",
            "OOF 4C existe e foi carregado",
            inputs.oof.height > 0,
            f"{inputs.oof.height} linhas",
        ),
        (
            "THR003",
            "OOF contém somente 2022-2024",
            set(inputs.oof["source_year"]) == set(EXPECTED_YEAR_FOLDS),
            "2022,2023,2024",
        ),
        (
            "THR004",
            "2025 está ausente",
            2025 not in set(inputs.oof["source_year"]),
            "2025 reservado",
        ),
        (
            "THR005",
            "IDs são únicos",
            inputs.oof["id"].n_unique() == inputs.oof.height,
            f"{inputs.oof['id'].n_unique()} IDs",
        ),
        ("THR006", "Ano e fold seguem o contrato", True, "2022→1; 2023→2; 2024→3"),
        ("THR007", "Probabilidades são finitas e pertencem a [0,1]", True, "válidas"),
        (
            "THR008",
            "Targets são booleanos",
            inputs.oof.schema["target_grave"] == pl.Boolean,
            "Boolean",
        ),
        (
            "THR009",
            "Candidatos equivalem aos scores únicos",
            search.candidate_count == inputs.oof["predicted_probability_grave"].n_unique(),
            f"{search.candidate_count} candidatos",
        ),
        (
            "THR010",
            "Seleção maximiza F1 positivo",
            selected.f1 == search.maximum_f1,
            f"F1={selected.f1}",
        ),
        (
            "THR011",
            "Desempate segue recall e menor threshold",
            True,
            "comparação exata por inteiros",
        ),
        (
            "THR012",
            "Existe exatamente um threshold final",
            np.isfinite(selected.threshold),
            _string(selected.threshold),
        ),
        (
            "THR013",
            "Threshold 0.5 é somente referência",
            True,
            "não inserido como candidato especial",
        ),
        ("THR014", "Não há threshold específico por ano", True, "um cutoff congelado"),
        ("THR015", "Nenhum modelo foi treinado", True, "somente OOF existente"),
        ("THR016", "Nenhum refit foi realizado", True, "refit=false"),
        ("THR017", "2025 não foi usado", True, "final_test_used=false"),
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


def select_threshold(inputs: ThresholdSelectionInputs) -> ThresholdSelectionResult:
    validate_selected_model(inputs)
    validate_oof(inputs)
    probabilities = inputs.oof.get_column("predicted_probability_grave").to_numpy()
    targets = inputs.oof.get_column("target_grave").to_numpy()
    search = search_unique_probability_thresholds(probabilities, targets)
    reference = evaluate_threshold(probabilities, targets, REFERENCE_THRESHOLD)
    evaluation_rows = [
        _metric_row("pooled_oof", None, "selected_threshold", search.selected),
        _metric_row("pooled_oof", None, "reference_0_5", reference),
    ]
    for year in EXPECTED_YEAR_FOLDS:
        annual = inputs.oof.filter(pl.col("source_year") == year)
        annual_metrics = evaluate_threshold(
            annual.get_column("predicted_probability_grave").to_numpy(),
            annual.get_column("target_grave").to_numpy(),
            search.selected.threshold,
        )
        evaluation_rows.append(_metric_row(str(year), year, "selected_threshold", annual_metrics))
    evaluation = pl.DataFrame(evaluation_rows).with_columns(
        pl.col("validation_year").cast(pl.Int64)
    )
    checklist = _checklist(inputs, search)
    failed = checklist.filter(pl.col("status") != "PASS")
    if not failed.is_empty():
        raise ValueError(
            "Checks críticos da Fase 4F falharam; threshold não será publicado: "
            f"{failed.to_dicts()}"
        )
    search_summary = pl.DataFrame(
        {
            "candidate_count": [search.candidate_count],
            "maximum_f1": [search.maximum_f1],
            "number_of_candidates_at_maximum_f1": [search.candidates_at_maximum_f1],
            "tie_break_recall_applied": [search.tie_break_recall_applied],
            "tie_break_lower_threshold_applied": [search.tie_break_lower_threshold_applied],
            "selected_threshold": [search.selected.threshold],
            "selected_recall": [search.selected.recall],
            "selected_f1": [search.selected.f1],
        }
    )
    return ThresholdSelectionResult(
        selected_model_id=XGBOOST_MODEL_ID,
        selected_model_family=SELECTED_MODEL_FAMILY,
        oof_sha256=inputs.oof_sha256,
        search=search,
        reference=reference,
        selection=_selection_table(inputs, search, reference),
        evaluation=evaluation,
        search_summary=search_summary,
        checklist=checklist,
    )


def write_threshold_selection_tables(
    result: ThresholdSelectionResult, tables_dir: Path
) -> tuple[Path, ...]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "phase_4f_threshold_selection.csv": result.selection,
        "phase_4f_threshold_evaluation.csv": result.evaluation,
        "phase_4f_threshold_search_summary.csv": result.search_summary,
        "phase_4f_threshold_checklist.csv": result.checklist,
    }
    paths = tuple(tables_dir / filename for filename in tables)
    for path, table in zip(paths, tables.values(), strict=True):
        table.write_csv(path)
    return paths


def run_threshold_selection(
    source_tables_dir: Path = TABLES_DIR,
    output_tables_dir: Path = TABLES_DIR,
    oof_path: Path = XGBOOST_OOF_PREDICTIONS_PATH,
    experimental_contract_path: Path = EXPERIMENTAL_CONTRACT_PATH,
    phase_4e_document_path: Path = PHASE_4E_DOCUMENT_PATH,
    premodeling_acceptance_path: Path = PREMODELING_ACCEPTANCE_PATH,
) -> ThresholdSelectionRun:
    inputs = load_threshold_selection_inputs(
        tables_dir=source_tables_dir,
        oof_path=oof_path,
        experimental_contract_path=experimental_contract_path,
        phase_4e_document_path=phase_4e_document_path,
        premodeling_acceptance_path=premodeling_acceptance_path,
    )
    result = select_threshold(inputs)
    return ThresholdSelectionRun(
        result=result,
        table_paths=write_threshold_selection_tables(result, output_tables_dir),
    )
