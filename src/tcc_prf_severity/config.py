from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
AUDIT_DIR = ARTIFACTS_DIR / "audit"
INTERIM_ARTIFACTS_DIR = ARTIFACTS_DIR / "interim"
INTERIM_PARQUET_PATH = INTERIM_DIR / "prf_accidents_2021_2025.parquet"
INTERIM_MANIFEST_PATH = INTERIM_ARTIFACTS_DIR / "interim_manifest.json"

EXPECTED_YEARS = tuple(range(2021, 2026))
RAW_FILE_TEMPLATE = "datatran{year}.csv"

EXPECTED_COLUMNS = (
    "id",
    "data_inversa",
    "dia_semana",
    "horario",
    "uf",
    "br",
    "km",
    "municipio",
    "causa_acidente",
    "tipo_acidente",
    "classificacao_acidente",
    "fase_dia",
    "sentido_via",
    "condicao_metereologica",
    "tipo_pista",
    "tracado_via",
    "uso_solo",
    "pessoas",
    "mortos",
    "feridos_leves",
    "feridos_graves",
    "ilesos",
    "ignorados",
    "feridos",
    "veiculos",
    "latitude",
    "longitude",
    "regional",
    "delegacia",
    "uop",
)

INTEGER_COLUMNS = (
    "pessoas",
    "mortos",
    "feridos_leves",
    "feridos_graves",
    "ilesos",
    "ignorados",
    "feridos",
    "veiculos",
)

FLOAT_COLUMNS = ("km", "latitude", "longitude")
