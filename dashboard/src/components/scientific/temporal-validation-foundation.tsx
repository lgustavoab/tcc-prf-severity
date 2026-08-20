"use client";

import { TemporalValidationChart } from "@/components/charts/temporal-validation-chart";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { MODEL_LABELS } from "@/lib/constants/charts";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatMetric } from "@/lib/formatting/numbers";
import type { TemporalValidationAsset } from "@/types/dashboard";

export function TemporalValidationFoundation() {
  const asset = useDashboardAsset<TemporalValidationAsset>(DATA_PATHS.temporalValidation, { assetId: "TEMPORAL_VALIDATION" });
  if (asset.status === "loading") return <LoadingState />;
  if (asset.status === "error") return <ErrorState message={asset.error} />;

  return (
    <div className="section-stack">
      <section className="surface">
        <div className="surface-header"><div><h2>Nove resultados modelo/fold</h2><p>O ano de validação identifica o resultado publicado; não é filtro populacional.</p></div></div>
        <div className="data-table-wrap"><table><thead><tr><th>Fold</th><th>Ano de validação</th><th>Modelo</th><th>AP</th><th>ROC-AUC</th><th>Brier</th></tr></thead><tbody>{asset.data.data.map((row) => <tr key={`${row.model_id}-${row.fold}`}><td>{row.fold}</td><td>{row.validation_year}</td><td>{MODEL_LABELS[row.model_id] ?? row.model_id}</td><td>{formatMetric(row.average_precision)}</td><td>{formatMetric(row.roc_auc)}</td><td>{formatMetric(row.brier_score)}</td></tr>)}</tbody></table></div>
      </section>
      <TemporalValidationChart rows={asset.data.data} />
      <aside className="scientific-caveat" aria-label="Limite da validação temporal"><span className="caveat-mark" aria-hidden="true">i</span><div><strong>Leitura temporal</strong><p>Período/volume de treinamento e ano de validação mudam simultaneamente; a sequência não demonstra tendência temporal de melhora.</p></div></aside>
    </div>
  );
}
