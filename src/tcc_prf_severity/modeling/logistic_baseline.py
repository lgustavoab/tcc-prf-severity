from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from tcc_prf_severity.config import (
    EXPERIMENTAL_CONTRACT_PATH,
    LOGISTIC_OOF_PREDICTIONS_PATH,
    PREPROCESSING_CONTRACT_PATH,
    PRIMARY_ANALYTICAL_PARQUET_PATH,
    PRIMARY_ANALYTICAL_SCHEMA_PATH,
    TABLES_DIR,
    TEMPORAL_FOLDS_PATH,
)
from tcc_prf_severity.data.analytical import verify_primary_analytical_dataset
from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.modeling.experimental_design import (
    FINAL_TEST_YEAR,
    PRIMARY_METRIC,
    TARGET_COLUMN,
    TemporalFold,
    build_experimental_contract,
    build_temporal_folds,
    load_predictors_from_schema,
    validate_temporal_design,
)
from tcc_prf_severity.modeling.preprocessing import (
    PreprocessingGroups,
    build_preprocessing_contract,
    build_preprocessor,
    load_preprocessing_groups,
    load_temporal_folds,
)

MODEL_ID = "phase_4a_logistic_baseline"
REFERENCE_THRESHOLD = 0.5
CALIBRATION_BINS = 10


@dataclass(frozen=True)
class FoldLogisticResult:
    fold: int
    train_years: tuple[int, ...]
    validation_year: int
    train_rows: int
    validation_rows: int
    output_feature_count: int
    validation_positive_rate: float
    average_precision: float
    roc_auc: float
    brier_score: float
    recall_at_0_5: float
    precision_at_0_5: float
    f1_at_0_5: float
    tn_at_0_5: int
    fp_at_0_5: int
    fn_at_0_5: int
    tp_at_0_5: int
    iterations: int
    converged: bool
    oof_predictions: pl.DataFrame
    calibration: pl.DataFrame


@dataclass(frozen=True)
class LogisticBaselineResult:
    fold_results: tuple[FoldLogisticResult, ...]
    fold_metrics: pl.DataFrame
    summary: pl.DataFrame
    model_contract: pl.DataFrame
    calibration: pl.DataFrame
    oof_predictions: pl.DataFrame


@dataclass(frozen=True)
class LogisticBaselineRun:
    result: LogisticBaselineResult
    table_paths: tuple[Path, ...]
    oof_path: Path
    oof_sha256: str


def build_logistic_pipeline(groups: PreprocessingGroups) -> Pipeline:
    """Cria uma instância não fitada com a configuração baseline congelada."""
    return Pipeline(
        steps=(
            ("preprocessor", build_preprocessor(groups)),
            (
                "classifier",
                LogisticRegression(
                    solver="newton-cholesky",
                    C=1.0,
                    l1_ratio=0.0,
                    class_weight=None,
                    fit_intercept=True,
                    tol=1e-4,
                    max_iter=500,
                ),
            ),
        )
    )


def extract_positive_class_probability(
    classifier: LogisticRegression,
    predicted_probabilities: np.ndarray,
) -> np.ndarray:
    """Localiza explicitamente a coluna correspondente à classe booleana True."""
    classes = np.asarray(classifier.classes_)
    positive_indices = [
        index
        for index, value in enumerate(classes)
        if isinstance(value, (bool, np.bool_)) and bool(value)
    ]
    if len(positive_indices) != 1:
        raise ValueError(
            "A classe positiva True não foi localizada de forma unívoca em classifier.classes_."
        )
    probabilities = np.asarray(predicted_probabilities[:, positive_indices[0]], dtype=float)
    if probabilities.ndim != 1 or not np.isfinite(probabilities).all():
        raise ValueError("Probabilidades da classe grave devem ser unidimensionais e finitas.")
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("Probabilidades da classe grave devem pertencer ao intervalo [0, 1].")
    return probabilities


def calculate_binary_metrics(
    target: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, float | int]:
    """Calcula métricas congeladas; 0,5 é somente uma referência descritiva."""
    predicted_at_0_5 = probabilities >= REFERENCE_THRESHOLD
    tn, fp, fn, tp = confusion_matrix(
        target,
        predicted_at_0_5,
        labels=[False, True],
    ).ravel()
    recall = float(tp / (tp + fn)) if tp + fn else 0.0
    precision = float(tp / (tp + fp)) if tp + fp else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "validation_positive_rate": float(np.mean(target)),
        "average_precision": float(average_precision_score(target, probabilities)),
        "roc_auc": float(roc_auc_score(target, probabilities)),
        "brier_score": float(brier_score_loss(target, probabilities, pos_label=True)),
        "recall_at_0_5": recall,
        "precision_at_0_5": precision,
        "f1_at_0_5": f1,
        "tn_at_0_5": int(tn),
        "fp_at_0_5": int(fp),
        "fn_at_0_5": int(fn),
        "tp_at_0_5": int(tp),
    }


def _calibration_table(
    fold: TemporalFold,
    target: np.ndarray,
    probabilities: np.ndarray,
) -> pl.DataFrame:
    observed, predicted = calibration_curve(
        target,
        probabilities,
        pos_label=True,
        n_bins=CALIBRATION_BINS,
        strategy="quantile",
    )
    return pl.DataFrame(
        {
            "fold": [fold.fold] * len(predicted),
            "validation_year": [fold.validation_year] * len(predicted),
            "bin": list(range(1, len(predicted) + 1)),
            "mean_predicted_probability": predicted,
            "observed_positive_rate": observed,
        }
    )


def _validate_modeling_fold(fold: TemporalFold) -> None:
    if FINAL_TEST_YEAR in (*fold.train_years, fold.validation_year):
        raise ValueError("2025 é proibido em treino, transformação e avaliação da Fase 4A.")
    if fold.validation_year in fold.train_years or max(fold.train_years) >= fold.validation_year:
        raise ValueError(f"Fold {fold.fold} viola a ordem temporal train -> validation.")


def run_logistic_fold(
    df: pl.DataFrame,
    groups: PreprocessingGroups,
    fold: TemporalFold,
) -> FoldLogisticResult:
    """Ajusta um pipeline novo somente no treino e avalia uma única validação temporal."""
    _validate_modeling_fold(fold)
    required = {"id", "source_year", TARGET_COLUMN, *groups.predictors}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Dataset analítico sem colunas exigidas pela baseline: {missing}")

    train = df.filter(pl.col("source_year").is_in(fold.train_years))
    validation = df.filter(pl.col("source_year") == fold.validation_year)
    if train.is_empty() or validation.is_empty():
        raise ValueError(f"Fold {fold.fold} possui treino ou validação sem linhas.")
    if train.get_column(TARGET_COLUMN).dtype != pl.Boolean:
        raise ValueError("target_grave deve permanecer booleano e True deve ser a classe positiva.")

    train_x = train.select(groups.predictors)
    validation_x = validation.select(groups.predictors)
    train_y = train.get_column(TARGET_COLUMN).to_numpy()
    validation_y = validation.get_column(TARGET_COLUMN).to_numpy()
    pipeline = build_logistic_pipeline(groups)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", ConvergenceWarning)
        pipeline.fit(train_x, train_y)
    convergence_warnings = [
        warning for warning in captured if issubclass(warning.category, ConvergenceWarning)
    ]
    if convergence_warnings:
        raise RuntimeError(
            f"Fold {fold.fold}: LogisticRegression emitiu ConvergenceWarning; "
            "execução interrompida."
        )

    classifier = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]
    if not isinstance(classifier, LogisticRegression) or not isinstance(
        preprocessor, ColumnTransformer
    ):
        raise TypeError("Pipeline baseline não preservou classifier/preprocessor contratados.")
    probabilities = extract_positive_class_probability(
        classifier,
        np.asarray(pipeline.predict_proba(validation_x)),
    )
    metrics = calculate_binary_metrics(validation_y, probabilities)
    iterations = int(np.max(classifier.n_iter_))
    output_feature_count = len(preprocessor.get_feature_names_out())

    oof = pl.DataFrame(
        {
            "id": validation.get_column("id"),
            "source_year": validation.get_column("source_year"),
            "fold": [fold.fold] * validation.height,
            TARGET_COLUMN: validation.get_column(TARGET_COLUMN),
            "predicted_probability_grave": probabilities,
        }
    )
    return FoldLogisticResult(
        fold=fold.fold,
        train_years=fold.train_years,
        validation_year=fold.validation_year,
        train_rows=train.height,
        validation_rows=validation.height,
        output_feature_count=output_feature_count,
        validation_positive_rate=float(metrics["validation_positive_rate"]),
        average_precision=float(metrics["average_precision"]),
        roc_auc=float(metrics["roc_auc"]),
        brier_score=float(metrics["brier_score"]),
        recall_at_0_5=float(metrics["recall_at_0_5"]),
        precision_at_0_5=float(metrics["precision_at_0_5"]),
        f1_at_0_5=float(metrics["f1_at_0_5"]),
        tn_at_0_5=int(metrics["tn_at_0_5"]),
        fp_at_0_5=int(metrics["fp_at_0_5"]),
        fn_at_0_5=int(metrics["fn_at_0_5"]),
        tp_at_0_5=int(metrics["tp_at_0_5"]),
        iterations=iterations,
        converged=True,
        oof_predictions=oof,
        calibration=_calibration_table(fold, validation_y, probabilities),
    )


def build_fold_metrics_table(results: tuple[FoldLogisticResult, ...]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "fold": result.fold,
            "train_years": ",".join(str(year) for year in result.train_years),
            "validation_year": result.validation_year,
            "train_rows": result.train_rows,
            "validation_rows": result.validation_rows,
            "output_feature_count": result.output_feature_count,
            "validation_positive_rate": result.validation_positive_rate,
            "average_precision": result.average_precision,
            "roc_auc": result.roc_auc,
            "brier_score": result.brier_score,
            "recall_at_0_5": result.recall_at_0_5,
            "precision_at_0_5": result.precision_at_0_5,
            "f1_at_0_5": result.f1_at_0_5,
            "tn_at_0_5": result.tn_at_0_5,
            "fp_at_0_5": result.fp_at_0_5,
            "fn_at_0_5": result.fn_at_0_5,
            "tp_at_0_5": result.tp_at_0_5,
            "iterations": result.iterations,
            "converged": result.converged,
        }
        for result in results
    )


def build_logistic_summary(fold_metrics: pl.DataFrame) -> pl.DataFrame:
    """Agrega AP sem ponderação e com desvio padrão populacional."""
    ap_values = fold_metrics.get_column("average_precision").to_numpy()
    fold3 = fold_metrics.filter(pl.col("fold") == 3)
    if len(ap_values) != 3 or fold3.height != 1:
        raise ValueError("Resumo da baseline exige exatamente os três folds congelados.")
    mean_roc_auc = fold_metrics.get_column("roc_auc").mean()
    mean_brier_score = fold_metrics.get_column("brier_score").mean()
    if not isinstance(mean_roc_auc, (int, float)) or not isinstance(mean_brier_score, (int, float)):
        raise TypeError("Não foi possível agregar ROC-AUC ou Brier entre os folds.")
    values: tuple[tuple[str, Any], ...] = (
        ("model_id", MODEL_ID),
        ("fold_count", len(ap_values)),
        ("primary_metric", PRIMARY_METRIC),
        ("ap_unweighted_mean", float(np.mean(ap_values))),
        ("ap_population_std", float(np.std(ap_values, ddof=0))),
        ("ap_fold3", float(fold3.get_column("average_precision").item())),
        ("mean_roc_auc", float(mean_roc_auc)),
        ("mean_brier_score", float(mean_brier_score)),
        ("all_folds_converged", bool(fold_metrics.get_column("converged").all())),
        ("final_test_used", False),
        ("threshold_selected", False),
    )
    serialized = [
        str(value).lower() if isinstance(value, bool) else str(value) for _, value in values
    ]
    return pl.DataFrame({"key": [key for key, _ in values], "value": serialized})


def build_logistic_model_contract() -> pl.DataFrame:
    values = (
        ("model_family", "logistic_regression"),
        ("role", "baseline"),
        ("solver", "newton-cholesky"),
        ("regularization", "L2"),
        ("C", "1.0"),
        ("l1_ratio", "0.0"),
        ("class_weight", "none"),
        ("fit_intercept", "true"),
        ("tol", "1e-4"),
        ("max_iter", "500"),
        ("preprocessing", "phase_3e"),
        ("validation", "expanding_window_3_folds"),
        ("primary_metric", "Average Precision"),
        ("model_selection_aggregation", "unweighted_fold_mean"),
        ("threshold_policy", "not_selected_0.5_reference_only"),
        ("final_test_year", "2025_reserved"),
    )
    return pl.DataFrame(values, schema=("key", "value"), orient="row")


def validate_oof_predictions(
    oof: pl.DataFrame,
    source: pl.DataFrame,
    folds: tuple[TemporalFold, ...],
) -> None:
    expected_columns = (
        "id",
        "source_year",
        "fold",
        TARGET_COLUMN,
        "predicted_probability_grave",
    )
    failures: list[str] = []
    if tuple(oof.columns) != expected_columns:
        failures.append(f"colunas inesperadas: {oof.columns}")
    expected_rows = sum(
        source.filter(pl.col("source_year") == fold.validation_year).height for fold in folds
    )
    if oof.height != expected_rows:
        failures.append(f"linhas: esperado={expected_rows}, recebido={oof.height}")
    if oof.get_column("id").n_unique() != oof.height:
        failures.append("IDs OOF não são únicos")
    expected_years = {fold.validation_year for fold in folds}
    observed_years = set(oof.get_column("source_year").to_list())
    if (
        observed_years != expected_years
        or 2021 in observed_years
        or FINAL_TEST_YEAR in observed_years
    ):
        failures.append(f"anos OOF inválidos: {sorted(observed_years)}")
    fold_by_year = {fold.validation_year: fold.fold for fold in folds}
    invalid_folds = oof.filter(
        pl.col("fold")
        != pl.col("source_year").replace_strict(
            fold_by_year,
            default=-1,
            return_dtype=pl.Int64,
        )
    )
    if not invalid_folds.is_empty():
        failures.append("há linhas atribuídas ao fold incorreto")
    probabilities = oof.get_column("predicted_probability_grave").to_numpy()
    if not np.isfinite(probabilities).all() or np.any(
        (probabilities < 0.0) | (probabilities > 1.0)
    ):
        failures.append("probabilidades OOF não são finitas ou estão fora de [0, 1]")

    expected_target = source.select("id", TARGET_COLUMN).rename(
        {TARGET_COLUMN: "expected_target_grave"}
    )
    target_check = oof.join(expected_target, on="id", how="left", validate="m:1")
    if (
        target_check.get_column("expected_target_grave").null_count()
        or not target_check.filter(
            pl.col(TARGET_COLUMN) != pl.col("expected_target_grave")
        ).is_empty()
    ):
        failures.append("target OOF diverge do dataset analítico")
    if failures:
        raise ValueError("Previsões OOF inválidas:\n- " + "\n- ".join(failures))


def analyze_logistic_baseline(
    df: pl.DataFrame,
    groups: PreprocessingGroups,
    folds: tuple[TemporalFold, ...],
) -> LogisticBaselineResult:
    """Executa somente os três folds internos e não seleciona threshold ou modelo final."""
    if folds != build_temporal_folds():
        raise ValueError("A Fase 4A aceita somente os folds congelados na Fase 3D.")
    validate_temporal_design(df, groups.predictors, folds)
    results = tuple(run_logistic_fold(df, groups, fold) for fold in folds)
    fold_metrics = build_fold_metrics_table(results)
    oof = pl.concat([result.oof_predictions for result in results], how="vertical").sort(
        "source_year", "id"
    )
    validate_oof_predictions(oof, df, folds)
    return LogisticBaselineResult(
        fold_results=results,
        fold_metrics=fold_metrics,
        summary=build_logistic_summary(fold_metrics),
        model_contract=build_logistic_model_contract(),
        calibration=pl.concat([result.calibration for result in results], how="vertical"),
        oof_predictions=oof,
    )


def _validate_authoritative_contracts(
    groups: PreprocessingGroups,
    experimental_contract_path: Path,
    preprocessing_contract_path: Path,
) -> None:
    if not experimental_contract_path.is_file():
        raise FileNotFoundError(f"Contrato experimental 3D ausente: {experimental_contract_path}")
    if not preprocessing_contract_path.is_file():
        raise FileNotFoundError(
            f"Contrato de preprocessing 3E ausente: {preprocessing_contract_path}"
        )
    if not pl.read_csv(experimental_contract_path).equals(
        build_experimental_contract(groups.predictors)
    ):
        raise ValueError("Contrato experimental 3D diverge da especificação congelada.")
    if not pl.read_csv(preprocessing_contract_path).equals(build_preprocessing_contract(groups)):
        raise ValueError("Contrato de preprocessing 3E diverge da receita congelada.")


def write_logistic_baseline_artifacts(
    result: LogisticBaselineResult,
    tables_dir: Path,
    oof_path: Path,
) -> tuple[tuple[Path, ...], Path]:
    """Persiste somente tabelas e OOF; nenhum objeto fitado é serializado."""
    tables_dir.mkdir(parents=True, exist_ok=True)
    oof_path.parent.mkdir(parents=True, exist_ok=True)
    outputs = (
        (result.fold_metrics, "phase_4a_logistic_fold_metrics.csv"),
        (result.summary, "phase_4a_logistic_summary.csv"),
        (result.model_contract, "phase_4a_logistic_model_contract.csv"),
        (result.calibration, "phase_4a_logistic_calibration.csv"),
    )
    for table, filename in outputs:
        table.write_csv(tables_dir / filename)
    result.oof_predictions.write_parquet(oof_path)
    return tuple(tables_dir / filename for _, filename in outputs), oof_path


def run_logistic_baseline(
    analytical_path: Path = PRIMARY_ANALYTICAL_PARQUET_PATH,
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
    folds_path: Path = TEMPORAL_FOLDS_PATH,
    experimental_contract_path: Path = EXPERIMENTAL_CONTRACT_PATH,
    preprocessing_contract_path: Path = PREPROCESSING_CONTRACT_PATH,
    tables_dir: Path = TABLES_DIR,
    oof_path: Path = LOGISTIC_OOF_PREDICTIONS_PATH,
) -> LogisticBaselineRun:
    """Verifica a cadeia 3C-3E e executa a primeira baseline preditiva somente até 2024."""
    verification = verify_primary_analytical_dataset(
        parquet_path=analytical_path,
        schema_path=schema_path,
    )
    predictors = load_predictors_from_schema(schema_path)
    groups = load_preprocessing_groups(schema_path)
    if (
        set(predictors) != set(groups.predictors)
        or len(predictors) != len(groups.predictors)
        or len(predictors) != verification.predictor_columns
    ):
        raise ValueError(
            "Predictors da baseline não reconciliam com esquema, grupos e manifesto 3C."
        )
    folds = load_temporal_folds(folds_path)
    _validate_authoritative_contracts(
        groups,
        experimental_contract_path,
        preprocessing_contract_path,
    )
    result = analyze_logistic_baseline(pl.read_parquet(analytical_path), groups, folds)
    table_paths, published_oof_path = write_logistic_baseline_artifacts(
        result,
        tables_dir,
        oof_path,
    )
    return LogisticBaselineRun(
        result=result,
        table_paths=table_paths,
        oof_path=published_oof_path,
        oof_sha256=sha256_file(published_oof_path),
    )
