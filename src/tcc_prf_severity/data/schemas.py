import pandera.polars as pa
import polars as pl

NON_NEGATIVE = pa.Check.ge(0)

UFS = (
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
)
DAYS_OF_WEEK = (
    "domingo",
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
)
DAY_PHASES = ("Amanhecer", "Anoitecer", "Plena Noite", "Pleno dia")
ROAD_DIRECTIONS = ("Crescente", "Decrescente", "Não Informado")
WEATHER_CONDITIONS = (
    "Chuva",
    "Céu Claro",
    "Garoa/Chuvisco",
    "Granizo",
    "Ignorado",
    "Neve",
    "Nevoeiro/Neblina",
    "Nublado",
    "Sol",
    "Vento",
)
ROAD_TYPES = ("Dupla", "Múltipla", "Simples")
LAND_USE = ("Não", "Sim")
ACCIDENT_CLASSIFICATIONS = ("Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais")

STANDARDIZED_SCHEMA = pa.DataFrameSchema(
    {
        "id": pa.Column(str, nullable=False),
        "data_inversa": pa.Column(pl.Date, nullable=False),
        "dia_semana": pa.Column(str, checks=pa.Check.isin(DAYS_OF_WEEK), nullable=False),
        "horario": pa.Column(pl.Time, nullable=False),
        "uf": pa.Column(str, checks=pa.Check.isin(UFS), nullable=False),
        "br": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "km": pa.Column(float, checks=NON_NEGATIVE, nullable=False),
        "municipio": pa.Column(str, nullable=False),
        "causa_acidente": pa.Column(str, nullable=False),
        "tipo_acidente": pa.Column(str, nullable=False),
        "classificacao_acidente": pa.Column(
            str, checks=pa.Check.isin(ACCIDENT_CLASSIFICATIONS), nullable=True
        ),
        "fase_dia": pa.Column(str, checks=pa.Check.isin(DAY_PHASES), nullable=False),
        "sentido_via": pa.Column(str, checks=pa.Check.isin(ROAD_DIRECTIONS), nullable=False),
        "condicao_metereologica": pa.Column(
            str, checks=pa.Check.isin(WEATHER_CONDITIONS), nullable=False
        ),
        "tipo_pista": pa.Column(str, checks=pa.Check.isin(ROAD_TYPES), nullable=False),
        "tracado_via": pa.Column(str, nullable=False),
        "uso_solo": pa.Column(str, checks=pa.Check.isin(LAND_USE), nullable=False),
        "pessoas": pa.Column(int, checks=pa.Check.ge(1), nullable=False),
        "mortos": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "feridos_leves": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "feridos_graves": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "ilesos": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "ignorados": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "feridos": pa.Column(int, checks=NON_NEGATIVE, nullable=False),
        "veiculos": pa.Column(int, checks=pa.Check.ge(1), nullable=False),
        "latitude": pa.Column(float, checks=pa.Check.in_range(-35, 6), nullable=False),
        "longitude": pa.Column(float, checks=pa.Check.in_range(-75, -32), nullable=False),
        "regional": pa.Column(str, nullable=True),
        "delegacia": pa.Column(str, nullable=True),
        "uop": pa.Column(str, nullable=True),
        "source_year": pa.Column(int, checks=pa.Check.in_range(2021, 2025), nullable=False),
        "target_grave": pa.Column(bool, nullable=False),
    },
    strict=True,
    coerce=False,
)


def validate_standardized(df: pl.DataFrame) -> pl.DataFrame:
    """Valida tipos, nulabilidade, categorias e limites por coluna."""
    return STANDARDIZED_SCHEMA.validate(df, lazy=True)
