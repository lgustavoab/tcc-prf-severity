from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import NotFittedError
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted

from tcc_prf_severity.modeling.experimental_design import TemporalFold, build_temporal_folds
from tcc_prf_severity.modeling.preprocessing import (
    PreprocessingGroups,
    build_preprocessing_contract,
    build_preprocessor,
    load_preprocessing_groups,
    validate_preprocessing,
    validate_preprocessing_fold,
    write_preprocessing_tables,
)

CATEGORICAL = (
    "month_name",
    "dia_semana",
    "hour",
    "uf",
    "br",
    "sentido_via",
    "condicao_metereologica",
    "tipo_pista",
    "uso_solo",
)
BINARY = tuple(f"tracado_{suffix}" for suffix in "abcdefghijkl")
PREDICTORS = (*CATEGORICAL, "km", *BINARY)


def _write_schema(path: Path) -> None:
    columns = ["id", "source_year", "data_inversa", "target_grave", *PREDICTORS]
    roles = ["metadata", "metadata", "metadata", "target", *(["predictor"] * 22)]
    concepts = [
        "not_applicable",
        "not_applicable",
        "not_applicable",
        "target_grave",
        *CATEGORICAL,
        "km",
        *(["tracado_via_components"] * 12),
    ]
    pl.DataFrame(
        {
            "column": columns,
            "role": roles,
            "conceptual_feature": concepts,
            "included_in_model_matrix": [False] * 4 + [True] * 22,
        }
    ).write_csv(path)


@pytest.fixture
def schema_path(tmp_path: Path) -> Path:
    path = tmp_path / "schema.csv"
    _write_schema(path)
    return path


def _dataset() -> pl.DataFrame:
    rows = 10
    data: dict[str, object] = {
        "id": [f"id-{index}" for index in range(rows)],
        "source_year": [2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024, 2025, 2025],
        "data_inversa": [
            date(year, 1, 1)
            for year in (2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024, 2025, 2025)
        ],
        "target_grave": [True, False] * 5,
        "month_name": ["Janeiro", "Fevereiro"] * 5,
        "dia_semana": ["segunda-feira", "terça-feira"] * 5,
        "hour": [8, 9, 8, 10, 9, 10, 8, 11, 12, 13],
        "uf": ["SP", "MG", "ZZ", "SP", "MG", "PR", "SP", "BA", "XX", "YY"],
        "br": [0, 101, 0, 116, 101, 116, 0, 999, 777, 888],
        "sentido_via": ["Não Informado", "Crescente"] * 5,
        "condicao_metereologica": ["Ignorado", "Chuva"] * 5,
        "tipo_pista": ["Simples", "Dupla"] * 5,
        "uso_solo": ["Sim", "Não"] * 5,
        "km": [0.0, 10.0, 100.0, 110.0, 200.0, 210.0, 300.0, 310.0, 400.0, 410.0],
    }
    for index, column in enumerate(BINARY):
        data[column] = [(row + index) % 2 for row in range(rows)]
    return pl.DataFrame(data)


@pytest.fixture
def groups(schema_path: Path) -> PreprocessingGroups:
    return load_preprocessing_groups(schema_path)


def test_groups_come_from_schema_and_exclude_metadata_and_target(
    groups: PreprocessingGroups,
) -> None:
    assert groups.categorical == CATEGORICAL
    assert groups.numeric == ("km",)
    assert groups.binary == BINARY
    assert len(groups.predictors) == 22
    assert not {"id", "source_year", "data_inversa", "target_grave"} & set(groups.predictors)


def test_hour_and_br_are_categorical_while_only_km_is_numeric(
    groups: PreprocessingGroups,
) -> None:
    assert "hour" in groups.categorical
    assert "br" in groups.categorical
    assert groups.numeric == ("km",)


def test_binary_features_are_inferred_by_concept_and_use_passthrough(
    groups: PreprocessingGroups,
) -> None:
    preprocessor = build_preprocessor(groups)
    transformers = {name: transformer for name, transformer, _ in preprocessor.transformers}

    assert len(groups.binary) == 12
    assert transformers["binary"] == "passthrough"


def test_factory_returns_independent_unfitted_column_transformers(
    groups: PreprocessingGroups,
) -> None:
    first = build_preprocessor(groups)
    second = build_preprocessor(groups)

    assert isinstance(first, ColumnTransformer)
    assert first is not second
    assert first.transformers[0][1] is not second.transformers[0][1]
    with pytest.raises(NotFittedError):
        check_is_fitted(first)


def test_encoder_configuration_preserves_all_train_categories(
    groups: PreprocessingGroups,
) -> None:
    preprocessor = build_preprocessor(groups)
    encoder = preprocessor.transformers[0][1]

    assert isinstance(encoder, OneHotEncoder)
    assert encoder.handle_unknown == "ignore"
    assert encoder.drop is None
    assert encoder.min_frequency is None
    assert encoder.max_categories is None
    assert encoder.sparse_output is True


def test_standard_scaler_is_used_only_for_km_and_no_imputer_exists(
    groups: PreprocessingGroups,
) -> None:
    preprocessor = build_preprocessor(groups)
    transformers = {
        name: (transformer, columns) for name, transformer, columns in preprocessor.transformers
    }

    numeric, columns = transformers["numeric"]
    assert isinstance(numeric, StandardScaler)
    assert columns == ["km"]
    assert all("imputer" not in name.lower() for name in transformers)


def test_unknown_validation_category_is_tolerated_and_audited(
    groups: PreprocessingGroups,
) -> None:
    result = validate_preprocessing_fold(_dataset(), groups, build_temporal_folds()[0])
    uf = result.unknown_audit.filter(pl.col("feature") == "uf").row(0, named=True)

    assert uf["unknown_category_count"] == 1
    assert uf["unknown_categories"] == '["ZZ"]'
    assert uf["validation_rows_with_unknown"] == 1
    assert result.validation_rows_with_any_unknown > 0


def test_existing_category_is_not_unknown_and_validation_only_category_is_not_learned(
    groups: PreprocessingGroups,
) -> None:
    result = validate_preprocessing_fold(_dataset(), groups, build_temporal_folds()[0])
    uf = result.unknown_audit.filter(pl.col("feature") == "uf").row(0, named=True)

    assert '"SP"' in uf["train_categories"]
    assert '"ZZ"' not in uf["train_categories"]
    assert '"SP"' not in uf["unknown_categories"]


def test_scaler_uses_train_mean_instead_of_validation(groups: PreprocessingGroups) -> None:
    df = _dataset()
    fold = build_temporal_folds()[0]
    train = df.filter(pl.col("source_year").is_in(fold.train_years)).select(groups.predictors)
    validation = df.filter(pl.col("source_year") == fold.validation_year).select(groups.predictors)
    preprocessor = build_preprocessor(groups)

    preprocessor.fit(train)
    scaler = preprocessor.named_transformers_["numeric"]
    assert isinstance(scaler, StandardScaler)
    assert scaler.mean_ is not None
    scaler_mean = float(np.asarray(scaler.mean_).ravel()[0])
    validation_mean = validation.get_column("km").mean()
    assert isinstance(validation_mean, (int, float))
    assert scaler_mean == 5.0
    assert scaler_mean != float(validation_mean)


def test_three_folds_record_exact_fit_years_and_never_use_2025(
    groups: PreprocessingGroups,
) -> None:
    validation = validate_preprocessing(_dataset(), groups, build_temporal_folds())

    assert tuple(result.fit_years for result in validation.folds) == (
        (2021,),
        (2021, 2022),
        (2021, 2022, 2023),
    )
    assert tuple(result.validation_year for result in validation.folds) == (2022, 2023, 2024)
    assert all(
        2025 not in (*result.fit_years, result.validation_year) for result in validation.folds
    )


def test_fold_with_2025_is_rejected(groups: PreprocessingGroups) -> None:
    with pytest.raises(ValueError, match="2025 é proibido"):
        validate_preprocessing_fold(
            _dataset(), groups, TemporalFold(4, (2021, 2022, 2023, 2024), 2025)
        )


def test_null_and_non_binary_predictors_fail(groups: PreprocessingGroups) -> None:
    null_df = _dataset().with_columns(
        pl.when(pl.col("id") == "id-0").then(None).otherwise(pl.col("uf")).alias("uf")
    )
    with pytest.raises(ValueError, match="valores nulos"):
        validate_preprocessing_fold(null_df, groups, build_temporal_folds()[0])

    binary_df = _dataset().with_columns(pl.lit(2).alias(BINARY[0]))
    with pytest.raises(ValueError, match="fora de 0/1"):
        validate_preprocessing_fold(binary_df, groups, build_temporal_folds()[0])


def test_outputs_are_sparse_finite_and_have_traceable_names(
    groups: PreprocessingGroups,
) -> None:
    result = validate_preprocessing_fold(_dataset(), groups, build_temporal_folds()[0])

    assert result.sparse_output is True
    assert result.matrix_format == "csr_matrix"
    assert result.fit_scope_verified is True
    assert result.train_non_finite_count == 0
    assert result.validation_non_finite_count == 0
    assert len(result.feature_names) == result.output_feature_count
    assert "numeric__km" in result.feature_names
    assert f"binary__{BINARY[0]}" in result.feature_names
    assert any(name.startswith("categorical__uf_") for name in result.feature_names)


def test_preprocessing_does_not_consult_target_or_modify_source(
    groups: PreprocessingGroups,
) -> None:
    source = _dataset().drop("target_grave")
    before = source.clone()

    result = validate_preprocessing_fold(source, groups, build_temporal_folds()[0])

    assert result.train_rows == 2
    assert source.equals(before)


def test_contract_and_tables_are_written_without_fitted_artifacts(
    tmp_path: Path, groups: PreprocessingGroups
) -> None:
    validation = validate_preprocessing(_dataset(), groups, build_temporal_folds())
    contract = build_preprocessing_contract(groups)
    categorical = contract.filter(pl.col("group") == "categorical").row(0, named=True)

    assert categorical["transformer"] == "OneHotEncoder"
    assert categorical["fit_scope"] == "fold_train_only"
    assert categorical["unknown_policy"] == "handle_unknown=ignore; audit_separately"

    paths = write_preprocessing_tables(validation, tmp_path)
    assert {path.name for path in paths} == {
        "phase_3e_preprocessing_contract.csv",
        "phase_3e_fold_preprocessing_summary.csv",
        "phase_3e_unknown_category_audit.csv",
    }
    assert all(path.is_file() for path in paths)
    assert not list(tmp_path.glob("*.pkl"))
    assert not list(tmp_path.glob("*.joblib"))
