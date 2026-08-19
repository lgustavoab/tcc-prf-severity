"""CLI fina para exportar os JSONs estáticos do dashboard."""

from __future__ import annotations

import argparse

from tcc_prf_severity.config import PROJECT_ROOT, TABLES_DIR
from tcc_prf_severity.dashboard.export import export_dashboard_data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generated-at",
        required=True,
        help="Timestamp ISO-8601 com fuso UTC gravado no manifesto.",
    )
    args = parser.parse_args()
    result = export_dashboard_data(
        generated_at=args.generated_at,
        project_root=PROJECT_ROOT,
        reports_dir=TABLES_DIR,
    )
    print("Dados estáticos do dashboard exportados.")
    print(f"Generated at: {result.generated_at}")
    print(f"Assets lógicos: {result.logical_asset_count}")
    print(f"Partes físicas: {result.physical_asset_count}")
    print(f"Manifesto: {result.manifest_path}")
    print(
        "Linhas exploratórias: "
        f"temporal={result.rows_by_part['EXPLORATION:temporal']}; "
        f"contextual={result.rows_by_part['EXPLORATION:contextual']}; "
        f"geography={result.rows_by_part['GEOGRAPHY:default']}"
    )
    print(f"Maior asset: {result.largest_asset_path} ({result.largest_asset_bytes} bytes)")
    print(f"Tamanho total dos assets: {result.total_asset_bytes} bytes")
    print(f"Reconciliação: {result.reconciliation_pass} PASS / {result.reconciliation_fail} FAIL")
    print(f"Checklist: {result.checklist_pass} PASS / {result.checklist_fail} FAIL")


if __name__ == "__main__":
    main()
