from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from tcc_prf_severity.config import (
    PRIMARY_ANALYTICAL_PARQUET_PATH,
    PRIMARY_ANALYTICAL_SCHEMA_PATH,
    TABLES_DIR,
)
from tcc_prf_severity.data.analytical import verify_primary_analytical_dataset

DEVELOPMENT_YEARS = (2021, 2022, 2023, 2024)
FINAL_TEST_YEAR = 2025
METADATA_COLUMNS = ("id", "source_year", "data_inversa")
TARGET_COLUMN = "target_grave"
PRIMARY_METRIC = "Average Precision (AP)"


@dataclass(frozen=True)
class TemporalFold:
    fold: int
    train_years: tuple[int, ...]
    validation_year: int


@dataclass(frozen=True)
class ExperimentalDesign:
    predictors: tuple[str, ...]
    folds: tuple[TemporalFold, ...]
    partition_summary: pl.DataFrame
    temporal_folds: pl.DataFrame
    experimental_contract: pl.DataFrame


@dataclass(frozen=True)
class ExperimentalDesignRun:
    design: ExperimentalDesign
    table_paths: tuple[Path, ...]


def build_temporal_folds() -> tuple[TemporalFold, ...]:
    """Define explicitamente os três folds expanding-window de desenvolvimento."""
    return (
        TemporalFold(1, (2021,), 2022),
        TemporalFold(2, (2021, 2022), 2023),
        TemporalFold(3, (2021, 2022, 2023), 2024),
    )


def load_predictors_from_schema(
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
) -> tuple[str, ...]:
    """Obtém predictors somente dos papéis formais registrados pelo esquema da Fase 3C."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Esquema analítico da Fase 3C não encontrado: {schema_path}")
    try:
        schema = pl.read_csv(schema_path)
    except Exception as error:
        raise ValueError(f"Não foi possível ler o esquema analítico: {schema_path}") from error

    required = {"column", "role", "included_in_model_matrix"}
    missing = sorted(required - set(schema.columns))
    if missing:
        raise ValueError(f"Esquema analítico sem colunas obrigatórias: {missing}")
    if schema.get_column("column").n_unique() != schema.height:
        raise ValueError("Esquema analítico contém nomes de coluna duplicados.")

    role_by_column = {
        str(row["column"]): (str(row["role"]), bool(row["included_in_model_matrix"]))
        for row in schema.iter_rows(named=True)
    }
    failures: list[str] = []
    for column in METADATA_COLUMNS:
        if role_by_column.get(column) != ("metadata", False):
            failures.append(f"{column} não está registrado exclusivamente como metadata")
    if role_by_column.get(TARGET_COLUMN) != ("target", False):
        failures.append(f"{TARGET_COLUMN} não está registrado exclusivamente como target")

    predictors = tuple(
        str(row["column"])
        for row in schema.filter(
            (pl.col("role") == "predictor") & pl.col("included_in_model_matrix")
        ).iter_rows(named=True)
    )
    invalid_inclusions = schema.filter(
        pl.col("included_in_model_matrix") & (pl.col("role") != "predictor")
    )
    if not invalid_inclusions.is_empty():
        failures.append("há colunas não preditoras marcadas para a matriz de modelo")
    if not predictors:
        failures.append("nenhum predictor foi autorizado pelo esquema")
    if failures:
        raise ValueError(
            "Esquema analítico incompatível com o desenho experimental: " + "; ".join(failures)
        )
    return predictors


def _require_analytical_columns(df: pl.DataFrame, predictors: tuple[str, ...]) -> None:
    required = {*METADATA_COLUMNS, TARGET_COLUMN, *predictors}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Dataset analítico sem colunas exigidas pelo esquema: {missing}")
    if df.is_empty():
        raise ValueError("O dataset analítico não pode estar vazio.")


def validate_temporal_design(
    df: pl.DataFrame,
    predictors: tuple[str, ...],
    folds: tuple[TemporalFold, ...],
) -> None:
    """Valida fronteiras, cobertura e ausência de leakage temporal ou overlap por ID."""
    _require_analytical_columns(df, predictors)
    failures: list[str] = []
    observed_years = tuple(sorted(int(year) for year in df.get_column("source_year").unique()))
    expected_years = (*DEVELOPMENT_YEARS, FINAL_TEST_YEAR)
    if observed_years != expected_years:
        failures.append(f"anos: esperado={list(expected_years)}, recebido={list(observed_years)}")
    if int(df.get_column("id").n_unique()) != df.height:
        failures.append("IDs não são únicos no dataset analítico")
    target = df.get_column(TARGET_COLUMN)
    if target.dtype != pl.Boolean or target.null_count() > 0:
        failures.append("target_grave deve permanecer booleano e não nulo")

    development = df.filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS))
    final_test = df.filter(pl.col("source_year") == FINAL_TEST_YEAR)
    if development.height + final_test.height != df.height:
        failures.append("partições development/final_test não preservam todas as linhas")
    overlap = set(development.get_column("id").to_list()) & set(
        final_test.get_column("id").to_list()
    )
    if overlap:
        failures.append("partições development e final_test possuem IDs em comum")
    if set(development.get_column("source_year").unique()) != set(DEVELOPMENT_YEARS):
        failures.append("development não corresponde exatamente a 2021-2024")
    if set(final_test.get_column("source_year").unique()) != {FINAL_TEST_YEAR}:
        failures.append("final_test não corresponde exatamente a 2025")

    validation_years: list[int] = []
    if folds != build_temporal_folds():
        failures.append("folds divergem da especificação expanding-window congelada")
    for fold in folds:
        validation_years.append(fold.validation_year)
        if not fold.train_years:
            failures.append(f"fold {fold.fold} não possui anos de treino")
            continue
        if fold.validation_year in fold.train_years:
            failures.append(f"fold {fold.fold}: validação aparece no próprio treino")
        if max(fold.train_years) >= fold.validation_year:
            failures.append(f"fold {fold.fold}: ano futuro ou contemporâneo aparece no treino")
        if FINAL_TEST_YEAR in (*fold.train_years, fold.validation_year):
            failures.append(f"fold {fold.fold}: 2025 aparece na validação interna")
        if not set((*fold.train_years, fold.validation_year)) <= set(DEVELOPMENT_YEARS):
            failures.append(f"fold {fold.fold}: período fora do desenvolvimento")

        train = df.filter(pl.col("source_year").is_in(fold.train_years))
        validation = df.filter(pl.col("source_year") == fold.validation_year)
        fold_overlap = set(train.get_column("id").to_list()) & set(
            validation.get_column("id").to_list()
        )
        if fold_overlap:
            failures.append(f"fold {fold.fold}: treino e validação possuem IDs em comum")
        if train.is_empty() or validation.is_empty():
            failures.append(f"fold {fold.fold}: treino ou validação sem linhas")

    if tuple(validation_years) != DEVELOPMENT_YEARS[1:]:
        failures.append(
            "anos de validação interna devem ser exatamente 2022, 2023 e 2024, uma vez cada"
        )
    if len({fold.fold for fold in folds}) != len(folds):
        failures.append("identificadores de folds duplicados")
    if failures:
        raise ValueError("Desenho experimental temporal inválido:\n- " + "\n- ".join(failures))


def _partition_row(
    df: pl.DataFrame,
    partition_id: str,
    partition_role: str,
    years: tuple[int, ...],
) -> dict[str, Any]:
    partition = df.filter(pl.col("source_year").is_in(years))
    severe = int(partition.get_column(TARGET_COLUMN).sum())
    return {
        "partition_id": partition_id,
        "partition_role": partition_role,
        "years": ",".join(str(year) for year in years),
        "rows": partition.height,
        "severe": severe,
        "non_severe": partition.height - severe,
        "severe_rate_percent": round(severe / partition.height * 100, 6),
    }


def build_partition_summary(
    df: pl.DataFrame,
    folds: tuple[TemporalFold, ...],
) -> pl.DataFrame:
    """Resume prevalência anual, partições principais e lados de cada fold."""
    rows = [
        _partition_row(df, f"year_{year}", "annual", (year,))
        for year in (*DEVELOPMENT_YEARS, FINAL_TEST_YEAR)
    ]
    rows.extend(
        (
            _partition_row(df, "development", "development", DEVELOPMENT_YEARS),
            _partition_row(df, "final_test", "final_evaluation", (FINAL_TEST_YEAR,)),
        )
    )
    for fold in folds:
        rows.append(_partition_row(df, f"fold_{fold.fold}_train", "fold_train", fold.train_years))
        rows.append(
            _partition_row(
                df,
                f"fold_{fold.fold}_validation",
                "fold_validation",
                (fold.validation_year,),
            )
        )
    return pl.DataFrame(rows)


def build_temporal_folds_table(
    df: pl.DataFrame,
    folds: tuple[TemporalFold, ...],
) -> pl.DataFrame:
    """Materializa uma linha descritiva por fold expanding-window."""
    rows: list[dict[str, Any]] = []
    for fold in folds:
        train = _partition_row(df, "", "", fold.train_years)
        validation = _partition_row(df, "", "", (fold.validation_year,))
        rows.append(
            {
                "fold": fold.fold,
                "train_years": ",".join(str(year) for year in fold.train_years),
                "validation_year": fold.validation_year,
                "train_rows": train["rows"],
                "validation_rows": validation["rows"],
                "train_severe": train["severe"],
                "validation_severe": validation["severe"],
                "train_severe_rate_percent": train["severe_rate_percent"],
                "validation_severe_rate_percent": validation["severe_rate_percent"],
            }
        )
    return pl.DataFrame(rows)


def build_experimental_contract(predictors: tuple[str, ...]) -> pl.DataFrame:
    """Congela decisões experimentais anteriores a qualquer fitting ou avaliação."""
    rows = (
        ("development_period", "2021-2024", "Período exclusivo de desenvolvimento."),
        ("final_evaluation_period", "2025", "Avaliação temporal somente após congelamento."),
        (
            "validation_strategy",
            "expanding_window_by_source_year",
            "Treino sempre antecede validação.",
        ),
        ("number_of_internal_folds", "3", "Validações em 2022, 2023 e 2024."),
        ("physical_predictors", str(len(predictors)), "Obtidos do esquema 3C, sem lista paralela."),
        (
            "primary_metric",
            PRIMARY_METRIC,
            "Calcular para target_grave=True pela definição operacional de "
            "sklearn.metrics.average_precision_score; não calculada na Fase 3D.",
        ),
        (
            "secondary_metrics",
            "ROC-AUC; recall; precision; F1; confusion_matrix; calibration; Brier_score",
            "Reporte futuro de discriminação, decisão e calibração.",
        ),
        (
            "diagnostic_outputs",
            "Precision-Recall_curve",
            "Curva futura para diagnóstico gráfico; não é uma segunda métrica primária.",
        ),
        (
            "fold_aggregation",
            "unweighted_mean_AP_plus_std_and_latest_fold",
            "Ranking pela média aritmética não ponderada das três APs; reportar desvio padrão "
            "e Fold 3 separadamente; não usar o melhor fold nem AP única no OOF concatenado.",
        ),
        (
            "threshold_selection_source",
            "temporal_OOF_2022_2024",
            "Concatenar OOF somente para threshold; não para ranking de modelo. "
            "2021 não possui previsão OOF e 2025 é proibido.",
        ),
        (
            "threshold_objective",
            "maximize_positive_class_F1",
            "Sem requisito operacional externo disponível.",
        ),
        ("threshold_tie_break", "higher_recall_then_lower_threshold", "Desempate determinístico."),
        (
            "final_refit_period",
            "2021-2024",
            "Refit futuro após seleção somente nos folds internos.",
        ),
        (
            "fitting_policy",
            "fit_train_only_within_each_fold",
            "Encoder, scaler, imputer e modelo nunca veem a validação no fit.",
        ),
        (
            "metadata_policy",
            "id_source_year_data_inversa_excluded_from_X",
            "Metadata serve somente à rastreabilidade e auditoria temporal.",
        ),
        (
            "final_holdout_policy",
            "no_optimization_or_fit_on_2025",
            "2025 não orienta features, modelo, hiperparâmetros, threshold ou preprocessing.",
        ),
        (
            "deterministic_features",
            "month_name; hour; tracado_via_components",
            "Derivações 3C não aprendem parâmetros e podem preceder o split.",
        ),
    )
    return pl.DataFrame(rows, schema=("key", "value", "rationale"), orient="row")


def analyze_experimental_design(
    df: pl.DataFrame,
    predictors: tuple[str, ...],
) -> ExperimentalDesign:
    """Constrói e valida a descrição experimental sem modificar o DataFrame recebido."""
    folds = build_temporal_folds()
    validate_temporal_design(df, predictors, folds)
    return ExperimentalDesign(
        predictors=predictors,
        folds=folds,
        partition_summary=build_partition_summary(df, folds),
        temporal_folds=build_temporal_folds_table(df, folds),
        experimental_contract=build_experimental_contract(predictors),
    )


def write_experimental_design_tables(
    design: ExperimentalDesign,
    output_dir: Path,
) -> tuple[Path, ...]:
    """Publica somente as três tabelas pequenas e versionáveis da Fase 3D."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (design.partition_summary, "phase_3d_partition_summary.csv"),
        (design.temporal_folds, "phase_3d_temporal_folds.csv"),
        (design.experimental_contract, "phase_3d_experimental_contract.csv"),
    )
    for table, filename in outputs:
        table.write_csv(output_dir / filename)
    return tuple(output_dir / filename for _, filename in outputs)


def run_experimental_design(
    analytical_path: Path = PRIMARY_ANALYTICAL_PARQUET_PATH,
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
    tables_dir: Path = TABLES_DIR,
) -> ExperimentalDesignRun:
    """Verifica a cadeia de dados e materializa somente o desenho experimental da 3D."""
    verification = verify_primary_analytical_dataset(
        parquet_path=analytical_path,
        schema_path=schema_path,
    )
    predictors = load_predictors_from_schema(schema_path)
    if len(predictors) != verification.predictor_columns:
        raise ValueError(
            "Quantidade de predictors no esquema diverge do manifesto 3C: "
            f"esquema={len(predictors)}, manifesto={verification.predictor_columns}"
        )
    design = analyze_experimental_design(pl.read_parquet(analytical_path), predictors)
    return ExperimentalDesignRun(design, write_experimental_design_tables(design, tables_dir))
