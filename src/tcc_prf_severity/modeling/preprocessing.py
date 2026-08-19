from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from tcc_prf_severity.config import (
    PRIMARY_ANALYTICAL_PARQUET_PATH,
    PRIMARY_ANALYTICAL_SCHEMA_PATH,
    TABLES_DIR,
    TEMPORAL_FOLDS_PATH,
)
from tcc_prf_severity.data.analytical import verify_primary_analytical_dataset
from tcc_prf_severity.modeling.experimental_design import (
    FINAL_TEST_YEAR,
    TemporalFold,
    build_temporal_folds,
    load_predictors_from_schema,
)


@dataclass(frozen=True)
class PreprocessingGroups:
    categorical: tuple[str, ...]
    numeric: tuple[str, ...]
    binary: tuple[str, ...]

    @property
    def predictors(self) -> tuple[str, ...]:
        return (*self.categorical, *self.numeric, *self.binary)


@dataclass(frozen=True)
class FoldPreprocessingResult:
    fold: int
    fit_years: tuple[int, ...]
    validation_year: int
    train_rows: int
    validation_rows: int
    input_predictor_count: int
    output_feature_count: int
    categorical_output_count: int
    numeric_output_count: int
    binary_output_count: int
    sparse_output: bool
    matrix_format: str
    fit_scope_verified: bool
    train_non_finite_count: int
    validation_non_finite_count: int
    unknown_feature_occurrences: int
    validation_rows_with_any_unknown: int
    feature_names: tuple[str, ...]
    unknown_audit: pl.DataFrame


@dataclass(frozen=True)
class PreprocessingValidation:
    groups: PreprocessingGroups
    folds: tuple[FoldPreprocessingResult, ...]
    preprocessing_contract: pl.DataFrame
    fold_summary: pl.DataFrame
    unknown_category_audit: pl.DataFrame


@dataclass(frozen=True)
class PreprocessingValidationRun:
    validation: PreprocessingValidation
    table_paths: tuple[Path, ...]


def load_preprocessing_groups(
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
) -> PreprocessingGroups:
    """Classifica os predictors usando somente os papéis e conceitos do esquema 3C."""
    predictors = load_predictors_from_schema(schema_path)
    schema = pl.read_csv(schema_path).filter(pl.col("column").is_in(predictors))
    binary = tuple(
        str(value)
        for value in schema.filter(
            pl.col("conceptual_feature") == "tracado_via_components"
        ).get_column("column")
    )
    numeric = tuple(
        str(value)
        for value in schema.filter(pl.col("conceptual_feature") == "km").get_column("column")
    )
    categorical = tuple(column for column in predictors if column not in {*binary, *numeric})
    groups = PreprocessingGroups(categorical, numeric, binary)

    failures: list[str] = []
    if set(groups.predictors) != set(predictors) or len(groups.predictors) != len(predictors):
        failures.append("os grupos não reconciliam com os predictors autorizados")
    if len(categorical) != 9:
        failures.append(f"categóricas: esperado=9, recebido={len(categorical)}")
    if numeric != ("km",):
        failures.append(f"grupo numérico deve conter somente km, recebido={numeric!r}")
    if len(binary) != 12:
        failures.append(f"binárias de traçado: esperado=12, recebido={len(binary)}")
    for semantic_categorical in ("hour", "br"):
        if semantic_categorical not in categorical:
            failures.append(f"{semantic_categorical} deve ser tratado como categórico")
    if failures:
        raise ValueError("Grupos de preprocessing inválidos:\n- " + "\n- ".join(failures))
    return groups


def load_temporal_folds(
    path: Path = TEMPORAL_FOLDS_PATH,
) -> tuple[TemporalFold, ...]:
    """Lê os folds autoritativos da 3D e rejeita qualquer divergência temporal."""
    if not path.is_file():
        raise FileNotFoundError(f"Tabela de folds da Fase 3D não encontrada: {path}")
    try:
        table = pl.read_csv(path)
    except Exception as error:
        raise ValueError(f"Não foi possível ler a tabela de folds da Fase 3D: {path}") from error
    required = {"fold", "train_years", "validation_year"}
    missing = sorted(required - set(table.columns))
    if missing:
        raise ValueError(f"Tabela de folds sem colunas obrigatórias: {missing}")

    folds = tuple(
        TemporalFold(
            int(row["fold"]),
            tuple(int(year) for year in str(row["train_years"]).split(",")),
            int(row["validation_year"]),
        )
        for row in table.iter_rows(named=True)
    )
    if folds != build_temporal_folds():
        raise ValueError("Tabela de folds diverge do desenho experimental congelado na Fase 3D.")
    return folds


def build_preprocessor(groups: PreprocessingGroups) -> ColumnTransformer:
    """Retorna uma fábrica não fitada e independente para um único fold."""
    categorical = OneHotEncoder(
        handle_unknown="ignore",
        drop=None,
        min_frequency=None,
        max_categories=None,
        sparse_output=True,
    )
    return ColumnTransformer(
        transformers=(
            ("categorical", categorical, list(groups.categorical)),
            ("numeric", StandardScaler(), list(groups.numeric)),
            ("binary", "passthrough", list(groups.binary)),
        ),
        remainder="drop",
        sparse_threshold=1.0,
        verbose_feature_names_out=True,
    )


def _validate_predictor_frame(df: pl.DataFrame, groups: PreprocessingGroups) -> None:
    missing = sorted(set(groups.predictors) - set(df.columns))
    if missing:
        raise ValueError(f"Predictors ausentes no dataset analítico: {missing}")
    nulls = {
        column: df.get_column(column).null_count()
        for column in groups.predictors
        if df.get_column(column).null_count() > 0
    }
    if nulls:
        raise ValueError(f"Predictors contêm valores nulos e não haverá imputação: {nulls}")
    invalid_binary: dict[str, list[object]] = {}
    for column in groups.binary:
        values = set(df.get_column(column).unique().to_list())
        if not values <= {0, 1}:
            invalid_binary[column] = sorted(values, key=str)
    if invalid_binary:
        raise ValueError(f"Indicadores binários fora de 0/1: {invalid_binary}")


def _validate_fold(fold: TemporalFold) -> None:
    if FINAL_TEST_YEAR in (*fold.train_years, fold.validation_year):
        raise ValueError("2025 é proibido no fit e na transformação da Fase 3E.")
    if fold.validation_year in fold.train_years or max(fold.train_years) >= fold.validation_year:
        raise ValueError(f"Fold {fold.fold} viola a ordem temporal train -> validation.")


def _non_finite_count(matrix: Any) -> int:
    values = matrix.data if sparse.issparse(matrix) else np.asarray(matrix)
    return int(np.size(values) - np.count_nonzero(np.isfinite(values)))


def _serialize_categories(values: list[object]) -> str:
    normalized = [value.item() if isinstance(value, np.generic) else value for value in values]
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))


def _unknown_category_audit(
    fold: TemporalFold,
    train: pl.DataFrame,
    validation: pl.DataFrame,
    groups: PreprocessingGroups,
    encoder: OneHotEncoder,
) -> tuple[pl.DataFrame, int, int]:
    rows: list[dict[str, Any]] = []
    any_unknown = np.zeros(validation.height, dtype=bool)
    total_feature_occurrences = 0
    for feature, learned_array in zip(groups.categorical, encoder.categories_, strict=True):
        learned = learned_array.tolist()
        learned_set = set(learned)
        validation_values = validation.get_column(feature).to_list()
        validation_categories = sorted(set(validation_values), key=str)
        unknown_categories = sorted(set(validation_categories) - learned_set, key=str)
        unknown_mask = np.fromiter(
            (value not in learned_set for value in validation_values),
            dtype=bool,
            count=validation.height,
        )
        unknown_rows = int(np.count_nonzero(unknown_mask))
        any_unknown |= unknown_mask
        total_feature_occurrences += unknown_rows
        rows.append(
            {
                "fold": fold.fold,
                "feature": feature,
                "train_category_count": len(learned),
                "train_categories": _serialize_categories(learned),
                "validation_category_count": len(validation_categories),
                "unknown_category_count": len(unknown_categories),
                "unknown_categories": _serialize_categories(unknown_categories),
                "validation_rows_with_unknown": unknown_rows,
                "validation_unknown_share_percent": round(
                    unknown_rows / validation.height * 100, 6
                ),
            }
        )
    return pl.DataFrame(rows), total_feature_occurrences, int(np.count_nonzero(any_unknown))


def validate_preprocessing_fold(
    df: pl.DataFrame,
    groups: PreprocessingGroups,
    fold: TemporalFold,
) -> FoldPreprocessingResult:
    """Ajusta uma receita nova somente no treino e transforma os dois lados do fold."""
    _validate_fold(fold)
    if "source_year" not in df.columns:
        raise ValueError("source_year é obrigatório para selecionar o fold.")
    train = df.filter(pl.col("source_year").is_in(fold.train_years))
    validation = df.filter(pl.col("source_year") == fold.validation_year)
    if train.is_empty() or validation.is_empty():
        raise ValueError(f"Fold {fold.fold} possui treino ou validação sem linhas.")
    _validate_predictor_frame(train, groups)
    _validate_predictor_frame(validation, groups)

    train_x = train.select(groups.predictors)
    validation_x = validation.select(groups.predictors)
    preprocessor = build_preprocessor(groups)
    train_matrix = preprocessor.fit_transform(train_x)
    validation_matrix = preprocessor.transform(validation_x)
    feature_names = tuple(str(name) for name in preprocessor.get_feature_names_out())
    encoder = preprocessor.named_transformers_["categorical"]
    scaler = preprocessor.named_transformers_["numeric"]
    if not isinstance(encoder, OneHotEncoder) or not isinstance(scaler, StandardScaler):
        raise TypeError("ColumnTransformer retornou transformers incompatíveis com o contrato.")

    unknown_audit, feature_occurrences, rows_with_any_unknown = _unknown_category_audit(
        fold, train, validation, groups, encoder
    )
    categorical_output_count = sum(len(categories) for categories in encoder.categories_)
    expected_output_count = categorical_output_count + len(groups.numeric) + len(groups.binary)
    failures: list[str] = []
    if train_matrix.shape != (train.height, expected_output_count):
        failures.append(f"shape de treino inesperado: {train_matrix.shape}")
    if validation_matrix.shape != (validation.height, expected_output_count):
        failures.append(f"shape de validação inesperado: {validation_matrix.shape}")
    if len(feature_names) != expected_output_count:
        failures.append("nomes de saída não reconciliam com a dimensionalidade")
    if not sparse.issparse(train_matrix) or not sparse.issparse(validation_matrix):
        failures.append("a saída deveria permanecer sparse")
    matrix_format = type(train_matrix).__name__
    if type(validation_matrix).__name__ != matrix_format:
        failures.append("treino e validação produziram formatos de matriz diferentes")
    train_non_finite = _non_finite_count(train_matrix)
    validation_non_finite = _non_finite_count(validation_matrix)
    if train_non_finite or validation_non_finite:
        failures.append(
            f"valores não finitos: treino={train_non_finite}, validação={validation_non_finite}"
        )
    train_km_mean_value = train.get_column("km").mean()
    if not isinstance(train_km_mean_value, (int, float)):
        raise TypeError("Não foi possível calcular a média de km no treino.")
    scaler_mean = scaler.mean_
    if scaler_mean is None:
        raise ValueError("StandardScaler não registrou a média de km do treino.")
    train_km_mean = float(train_km_mean_value)
    if not np.isclose(float(np.asarray(scaler_mean).ravel()[0]), train_km_mean):
        failures.append("StandardScaler não foi ajustado exclusivamente com km do treino")
    if failures:
        raise ValueError(f"Preprocessing inválido no fold {fold.fold}: " + "; ".join(failures))

    return FoldPreprocessingResult(
        fold=fold.fold,
        fit_years=fold.train_years,
        validation_year=fold.validation_year,
        train_rows=train.height,
        validation_rows=validation.height,
        input_predictor_count=len(groups.predictors),
        output_feature_count=expected_output_count,
        categorical_output_count=categorical_output_count,
        numeric_output_count=len(groups.numeric),
        binary_output_count=len(groups.binary),
        sparse_output=True,
        matrix_format=matrix_format,
        fit_scope_verified=True,
        train_non_finite_count=train_non_finite,
        validation_non_finite_count=validation_non_finite,
        unknown_feature_occurrences=feature_occurrences,
        validation_rows_with_any_unknown=rows_with_any_unknown,
        feature_names=feature_names,
        unknown_audit=unknown_audit,
    )


def build_preprocessing_contract(groups: PreprocessingGroups) -> pl.DataFrame:
    """Materializa a receita de preprocessing sem estado fitado."""
    rows = (
        {
            "group": "categorical",
            "source_features": ",".join(groups.categorical),
            "transformer": "OneHotEncoder",
            "learned_parameters": "categories_",
            "fit_scope": "fold_train_only",
            "unknown_policy": "handle_unknown=ignore; audit_separately",
            "output_type": "sparse one-hot columns",
            "notes": "drop=None; min_frequency=None; max_categories=None; "
            "all train categories preserved",
        },
        {
            "group": "numeric",
            "source_features": ",".join(groups.numeric),
            "transformer": "StandardScaler",
            "learned_parameters": "mean_; scale_; var_",
            "fit_scope": "fold_train_only",
            "unknown_policy": "not_applicable",
            "output_type": "scaled numeric column in sparse combined matrix",
            "notes": "km only; no bins, clipping, log, winsorization or imputation",
        },
        {
            "group": "binary",
            "source_features": ",".join(groups.binary),
            "transformer": "passthrough",
            "learned_parameters": "none",
            "fit_scope": "not_applicable",
            "unknown_policy": "strict_binary_0_1_validation",
            "output_type": "unchanged binary columns in sparse combined matrix",
            "notes": "no encoding, scaling or imputation",
        },
    )
    return pl.DataFrame(rows)


def _fold_summary(results: tuple[FoldPreprocessingResult, ...]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "fold": result.fold,
            "train_years": ",".join(str(year) for year in result.fit_years),
            "validation_year": result.validation_year,
            "train_rows": result.train_rows,
            "validation_rows": result.validation_rows,
            "input_predictor_count": result.input_predictor_count,
            "output_feature_count": result.output_feature_count,
            "categorical_output_count": result.categorical_output_count,
            "numeric_output_count": result.numeric_output_count,
            "binary_output_count": result.binary_output_count,
            "sparse_output": result.sparse_output,
            "matrix_format": result.matrix_format,
            "fit_scope_verified": result.fit_scope_verified,
            "train_non_finite_count": result.train_non_finite_count,
            "validation_non_finite_count": result.validation_non_finite_count,
            "unknown_feature_occurrences": result.unknown_feature_occurrences,
            "validation_rows_with_any_unknown": result.validation_rows_with_any_unknown,
            "notes": "unknown_feature_occurrences soma linhas por feature; "
            "validation_rows_with_any_unknown deduplica linhas entre features",
        }
        for result in results
    )


def validate_preprocessing(
    df: pl.DataFrame,
    groups: PreprocessingGroups,
    folds: tuple[TemporalFold, ...],
) -> PreprocessingValidation:
    """Valida a receita nos três folds internos sem transformar ou inspecionar 2025."""
    if folds != build_temporal_folds():
        raise ValueError("A Fase 3E aceita somente os três folds congelados na Fase 3D.")
    results = tuple(validate_preprocessing_fold(df, groups, fold) for fold in folds)
    return PreprocessingValidation(
        groups=groups,
        folds=results,
        preprocessing_contract=build_preprocessing_contract(groups),
        fold_summary=_fold_summary(results),
        unknown_category_audit=pl.concat(
            [result.unknown_audit for result in results], how="vertical"
        ),
    )


def write_preprocessing_tables(
    validation: PreprocessingValidation,
    output_dir: Path,
) -> tuple[Path, ...]:
    """Escreve somente auditorias e contrato; nenhum transformer fitado é persistido."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (validation.preprocessing_contract, "phase_3e_preprocessing_contract.csv"),
        (validation.fold_summary, "phase_3e_fold_preprocessing_summary.csv"),
        (validation.unknown_category_audit, "phase_3e_unknown_category_audit.csv"),
    )
    for table, filename in outputs:
        table.write_csv(output_dir / filename)
    return tuple(output_dir / filename for _, filename in outputs)


def run_preprocessing_validation(
    analytical_path: Path = PRIMARY_ANALYTICAL_PARQUET_PATH,
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
    folds_path: Path = TEMPORAL_FOLDS_PATH,
    tables_dir: Path = TABLES_DIR,
) -> PreprocessingValidationRun:
    """Verifica a cadeia e executa somente preprocessing train-only nos folds internos."""
    verification = verify_primary_analytical_dataset(
        parquet_path=analytical_path,
        schema_path=schema_path,
    )
    groups = load_preprocessing_groups(schema_path)
    if len(groups.predictors) != verification.predictor_columns:
        raise ValueError(
            "Quantidade de predictors diverge do manifesto 3C: "
            f"grupos={len(groups.predictors)}, manifesto={verification.predictor_columns}"
        )
    folds = load_temporal_folds(folds_path)
    validation = validate_preprocessing(pl.read_parquet(analytical_path), groups, folds)
    return PreprocessingValidationRun(
        validation,
        write_preprocessing_tables(validation, tables_dir),
    )
