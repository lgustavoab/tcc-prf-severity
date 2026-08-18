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
EXPECTED_RAW_SHA256 = {
    2021: "b8ebf8352a5ad0d9d79a91a4dada665a1ec0bfca9fc2649e1c73fe80cfe6c4dd",
    2022: "d11bbfdec9b5df6f08a083c63acb2c1b4d3bad71d31481d7ce1368d5fa38783a",
    2023: "2e6a9eac714524822fc3150be4d0614e27c7f14aa674520c94e5d2e4089356dd",
    2024: "a3b7423cf643acd5de12742f319d5456930b1f105b44df4b81fae560b40af64c",
    2025: "bb844d45a07b5b50f5f76011e28f47e370fa6742e9211edac5510dcbe72ce4d8",
}

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
