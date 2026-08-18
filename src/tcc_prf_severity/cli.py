from tcc_prf_severity.config import (
    AUDIT_DIR,
    EXPECTED_YEARS,
    INTERIM_DIR,
    RAW_DIR,
    RAW_FILE_TEMPLATE,
)
from tcc_prf_severity.data.audit import run_audit
from tcc_prf_severity.data.ingest import concatenate_years, load_year
from tcc_prf_severity.data.validation import validate_dataset


def audit_main() -> None:
    summary = run_audit(RAW_DIR, AUDIT_DIR)
    combined = summary["combined"]
    print("Auditoria concluída.")
    print(f"Registros: {combined['rows']:,}".replace(",", "."))
    print(f"Graves (target_grave): {combined['graves']:,}".replace(",", "."))
    print(f"Taxa de graves: {combined['grave_rate']:.2%}")
    print(f"Relatórios: {AUDIT_DIR}")


def ingest_main() -> None:
    frames = []
    for year in EXPECTED_YEARS:
        path = RAW_DIR / RAW_FILE_TEMPLATE.format(year=year)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo obrigatório não encontrado: {path}")
        frame = load_year(path, year)
        validate_dataset(frame)
        frames.append(frame)

    combined = concatenate_years(frames)
    validate_dataset(combined)

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    output = INTERIM_DIR / "prf_2021_2025_standardized.parquet"
    combined.write_parquet(output, compression="zstd")
    print(f"Parquet padronizado criado: {output}")
    print(f"Registros: {combined.height:,}".replace(",", "."))
