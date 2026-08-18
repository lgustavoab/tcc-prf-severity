import polars as pl
import pytest
from pandera.errors import SchemaErrors

from tcc_prf_severity.data.ingest import standardize_types
from tcc_prf_severity.data.validation import validate_dataset


def _raw_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "id": ["1"],
            "data_inversa": ["2025-01-01"],
            "dia_semana": ["quarta-feira"],
            "horario": ["12:30:00"],
            "uf": ["SP"],
            "br": ["116"],
            "km": ["128,5"],
            "municipio": ["SAO PAULO"],
            "causa_acidente": ["Exemplo"],
            "tipo_acidente": ["Exemplo"],
            "classificacao_acidente": ["Com Vítimas Feridas"],
            "fase_dia": ["Pleno dia"],
            "sentido_via": ["Crescente"],
            "condicao_metereologica": ["Céu Claro"],
            "tipo_pista": ["Dupla"],
            "tracado_via": ["Reta;Declive"],
            "uso_solo": ["Sim"],
            "pessoas": ["2"],
            "mortos": ["0"],
            "feridos_leves": ["1"],
            "feridos_graves": ["1"],
            "ilesos": ["0"],
            "ignorados": ["0"],
            "feridos": ["2"],
            "veiculos": ["1"],
            "latitude": ["-23,55"],
            "longitude": ["-46,63"],
            "regional": ["SPRF-SP"],
            "delegacia": ["DEL01-SP"],
            "uop": ["UOP01-SP"],
        }
    )


def _valid_dataset() -> pl.DataFrame:
    return standardize_types(_raw_frame(), year=2025)


def test_valid_dataset_passes_complete_contract() -> None:
    df = _valid_dataset()

    assert validate_dataset(df).equals(df)


@pytest.mark.parametrize(
    ("mortos", "feridos_graves", "expected"),
    [(0, 0, False), (1, 0, True), (0, 1, True)],
)
def test_target_grave_is_created_from_physical_counts(
    mortos: int, feridos_graves: int, expected: bool
) -> None:
    raw = _raw_frame().with_columns(
        pl.lit(str(mortos)).alias("mortos"),
        pl.lit(str(feridos_graves)).alias("feridos_graves"),
        pl.lit(str(1 + feridos_graves)).alias("feridos"),
    )

    result = standardize_types(raw, year=2025)

    assert result["target_grave"].item() is expected


def test_invalid_uf_fails_schema() -> None:
    df = _valid_dataset().with_columns(pl.lit("XX").alias("uf"))

    with pytest.raises(SchemaErrors):
        validate_dataset(df)


def test_negative_count_fails_schema() -> None:
    df = _valid_dataset().with_columns(pl.lit(-1, dtype=pl.Int64).alias("mortos"))

    with pytest.raises(SchemaErrors):
        validate_dataset(df)


def test_inconsistent_injured_total_fails_invariants() -> None:
    df = _valid_dataset().with_columns(pl.lit(3, dtype=pl.Int64).alias("feridos"))

    with pytest.raises(ValueError, match="feridos != feridos_leves"):
        validate_dataset(df)


def test_source_year_different_from_date_fails_invariants() -> None:
    df = _valid_dataset().with_columns(pl.lit(2024, dtype=pl.Int64).alias("source_year"))

    with pytest.raises(ValueError, match="source_year"):
        validate_dataset(df)


def test_tampered_target_fails_invariants() -> None:
    df = _valid_dataset().with_columns(pl.lit(False).alias("target_grave"))

    with pytest.raises(ValueError, match="target_grave"):
        validate_dataset(df)


def test_duplicate_id_fails_invariants() -> None:
    df = _valid_dataset()

    with pytest.raises(ValueError, match="IDs duplicados"):
        validate_dataset(pl.concat([df, df]))


def test_weekday_incompatible_with_date_fails_invariants() -> None:
    df = _valid_dataset().with_columns(pl.lit("quinta-feira").alias("dia_semana"))

    with pytest.raises(ValueError, match="dia_semana incompatível"):
        validate_dataset(df)


def test_known_people_decomposition_difference_is_not_blocking() -> None:
    df = _valid_dataset().with_columns(pl.lit(3, dtype=pl.Int64).alias("pessoas"))

    assert validate_dataset(df).equals(df)
