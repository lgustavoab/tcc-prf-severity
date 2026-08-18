from tcc_prf_severity.config import (
    AUDIT_DIR,
    RAW_DIR,
)
from tcc_prf_severity.data.audit import run_audit
from tcc_prf_severity.data.interim import build_interim_dataset, verify_interim_dataset


def audit_main() -> None:
    summary = run_audit(RAW_DIR, AUDIT_DIR)
    combined = summary["combined"]
    print("Auditoria concluída.")
    print(f"Registros: {combined['rows']:,}".replace(",", "."))
    print(f"Graves (target_grave): {combined['graves']:,}".replace(",", "."))
    print(f"Taxa de graves: {combined['grave_rate']:.2%}")
    print(f"Relatórios: {AUDIT_DIR}")


def build_interim_main() -> None:
    result = build_interim_dataset()
    print("Dataset intermediário criado.")
    print(f"Registros: {result.rows:,}".replace(",", "."))
    print(f"Colunas: {result.columns}")
    print(f"Graves: {result.graves:,}".replace(",", "."))
    print(f"Taxa de graves: {result.grave_rate:.2%}")
    print(f"Parquet: {result.parquet_path}")
    print(f"Manifesto: {result.manifest_path}")


def verify_interim_main() -> None:
    result = verify_interim_dataset()
    print("Dataset intermediário verificado.")
    print(f"Registros: {result.rows:,}".replace(",", "."))
    print(f"Colunas: {result.columns}")
    print(f"Graves: {result.graves:,}".replace(",", "."))
    print(f"Taxa de graves: {result.grave_rate:.2%}")
    print(f"SHA-256: {result.sha256}")
    print(f"RAW sources: {result.raw_sources_verified}/5 OK")
    print("Manifesto: OK")
