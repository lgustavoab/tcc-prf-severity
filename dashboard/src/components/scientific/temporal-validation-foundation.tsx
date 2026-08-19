"use client";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { VisualizationPlaceholder } from "@/components/feedback/visualization-placeholder";
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
        <div className="data-table-wrap"><table><thead><tr><th>Fold</th><th>Ano de validação</th><th>Modelo</th><th>AP</th><th>ROC-AUC</th><th>Brier</th></tr></thead><tbody>{asset.data.data.map((row) => <tr key={`${row.model_id}-${row.fold}`}><td>{row.fold}</td><td>{row.validation_year}</td><td>{row.model_id.replace("phase_4a_logistic_baseline", "Regressão Logística").replace("phase_4b_random_forest_baseline", "Random Forest").replace("phase_4c_xgboost_baseline", "XGBoost")}</td><td>{formatMetric(row.average_precision)}</td><td>{formatMetric(row.roc_auc)}</td><td>{formatMetric(row.brier_score)}</td></tr>)}</tbody></table></div>
      </section>
      <VisualizationPlaceholder title="Consistência temporal" description="Área reservada para a apresentação dos três folds com janela expansiva." asset="TEMPORAL_VALIDATION · temporal_validation.json" />
    </div>
  );
}
