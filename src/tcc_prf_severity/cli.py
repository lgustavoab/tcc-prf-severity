from tcc_prf_severity.analysis.general import run_general_analysis
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


def eda_general_main() -> None:
    result = run_general_analysis()
    analysis = result.analysis
    summary = analysis.annual_summary
    stability = analysis.stability
    rows = int(summary.get_column("total_occurrences").sum())
    graves = int(summary.get_column("severe_occurrences").sum())
    years = summary.get_column("source_year")

    print("Fase 2A concluída.")
    print(f"Registros: {rows:,}".replace(",", "."))
    print(f"Período: {years.min()}-{years.max()}")
    print(f"Graves: {graves:,}".replace(",", "."))
    print(f"Taxa global: {stability.weighted_global_rate_percent:.2f}%")
    print(f"Menor taxa anual: {stability.minimum_annual_rate_percent:.2f}%")
    print(f"Maior taxa anual: {stability.maximum_annual_rate_percent:.2f}%")
    print(f"Tabelas: {result.table_paths[0].parent}")
    print(f"Figuras: {result.figure_paths[0].parent}")
