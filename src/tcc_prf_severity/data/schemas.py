import pandera.polars as pa
import polars as pl

NON_NEGATIVE = pa.Check.ge(0)

STANDARDIZED_SCHEMA = pa.DataFrameSchema(
    {
        "id": pa.Column(str, nullable=False),
        "data_inversa": pa.Column(pl.Date, nullable=False),
        "dia_semana": pa.Column(str, nullable=False),
        "horario": pa.Column(pl.Time, nullable=False),
        "uf": pa.Column(str, nullable=False),
        "br": pa.Column(int, nullable=True),
        "km": pa.Column(float, nullable=True),
        "municipio": pa.Column(str, nullable=False),
        "causa_acidente": pa.Column(str, nullable=False),
        "tipo_acidente": pa.Column(str, nullable=False),
        "classificacao_acidente": pa.Column(str, nullable=True),
        "fase_dia": pa.Column(str, nullable=False),
        "sentido_via": pa.Column(str, nullable=False),
        "condicao_metereologica": pa.Column(str, nullable=False),
        "tipo_pista": pa.Column(str, nullable=False),
        "tracado_via": pa.Column(str, nullable=False),
        "uso_solo": pa.Column(str, nullable=False),
        "pessoas": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "mortos": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "feridos_leves": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "feridos_graves": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "ilesos": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "ignorados": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "feridos": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "veiculos": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "latitude": pa.Column(float, nullable=True),
        "longitude": pa.Column(float, nullable=True),
        "regional": pa.Column(str, nullable=True),
        "delegacia": pa.Column(str, nullable=True),
        "uop": pa.Column(str, nullable=True),
        "source_year": pa.Column(int, checks=pa.Check.in_range(2021, 2025), nullable=False),
        "target_grave_provisorio": pa.Column(bool, nullable=False),
    },
    strict=True,
    coerce=False,
)


def validate_standardized(df: pl.DataFrame) -> pl.DataFrame:
    """Valida schema e regras básicas após a tipagem."""
    return STANDARDIZED_SCHEMA.validate(df, lazy=True)
