"use client";

import { CalibrationChart } from "@/components/charts/calibration-chart";
import { ModelComparisonChart } from "@/components/charts/model-comparison-chart";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger, formatMetric, formatPercent } from "@/lib/formatting/numbers";
import type { Calibration2025Asset, Final2025Asset, ModelComparisonAsset } from "@/types/dashboard";

export function ModelsFoundation() {
  const comparison = useDashboardAsset<ModelComparisonAsset>(DATA_PATHS.modelComparison, { assetId: "MODEL_COMPARISON" });
  const final2025 = useDashboardAsset<Final2025Asset>(DATA_PATHS.final2025, { assetId: "FINAL_2025" });
  const calibration = useDashboardAsset<Calibration2025Asset>(DATA_PATHS.calibration2025, { assetId: "CALIBRATION_2025" });

  if (comparison.status === "loading" || final2025.status === "loading" || calibration.status === "loading") return <LoadingState label="Carregando resultados congelados…" />;
  if (comparison.status === "error") return <ErrorState message={comparison.error} />;
  if (final2025.status === "error") return <ErrorState message={final2025.error} />;
  if (calibration.status === "error") return <ErrorState message={calibration.error} />;

  const metricLabels: Record<string, string> = {
    average_precision: "Average Precision",
    roc_auc: "ROC-AUC",
    brier_score: "Brier score",
    precision: "Precisão positiva",
    recall: "Sensibilidade",
    f1: "F1",
  };
  const displayMetric = (metric: string, value: number) => ["precision", "recall"].includes(metric) ? formatPercent(value) : formatMetric(value);

  return (
    <div className="section-stack">
      <section className="surface">
        <div className="cards-grid">
          <article className="metric-card"><span>Famílias comparadas</span><strong>{comparison.data.data.length}</strong><small>valores publicados</small></article>
          <article className="metric-card"><span>Modelo selecionado</span><strong>XGBoost</strong><small>{comparison.data.selected_model_id}</small></article>
          <article className="metric-card"><span>Avaliação final</span><strong>{final2025.data.final_test_year}</strong><small>{formatInteger(final2025.data.final_rows)} ocorrências</small></article>
          <article className="metric-card"><span>Faixas de calibração</span><strong>{calibration.data.data.length}</strong><small>diagnóstico publicado</small></article>
        </div>
      </section>
      <ModelComparisonChart asset={comparison.data} />
      <section className="surface">
        <div className="surface-header"><div><h2>Avaliação temporal final em 2025</h2><p>Valores congelados e respectivas referências de desenvolvimento; nenhum delta é recalculado.</p></div></div>
        <div className="metric-grid">{final2025.data.data.map((row) => <article className="metric-card" key={row.metric}><span>{metricLabels[row.metric] ?? row.metric}</span><strong>{displayMetric(row.metric, row.final_2025_value)}</strong><small>Referência: {displayMetric(row.metric, row.development_reference)}</small><small>Delta publicado: {displayMetric(row.metric, row.delta_final_minus_development)}</small></article>)}</div>
      </section>
      <CalibrationChart rows={calibration.data.data} />
    </div>
  );
}
