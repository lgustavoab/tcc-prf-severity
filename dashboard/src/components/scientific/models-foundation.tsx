"use client";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { VisualizationPlaceholder } from "@/components/feedback/visualization-placeholder";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger } from "@/lib/formatting/numbers";
import type { Calibration2025Asset, Final2025Asset, ModelComparisonAsset } from "@/types/dashboard";

export function ModelsFoundation() {
  const comparison = useDashboardAsset<ModelComparisonAsset>(DATA_PATHS.modelComparison, { assetId: "MODEL_COMPARISON" });
  const final2025 = useDashboardAsset<Final2025Asset>(DATA_PATHS.final2025, { assetId: "FINAL_2025" });
  const calibration = useDashboardAsset<Calibration2025Asset>(DATA_PATHS.calibration2025, { assetId: "CALIBRATION_2025" });

  if (comparison.status === "loading" || final2025.status === "loading" || calibration.status === "loading") return <LoadingState label="Carregando resultados congelados…" />;
  if (comparison.status === "error") return <ErrorState message={comparison.error} />;
  if (final2025.status === "error") return <ErrorState message={final2025.error} />;
  if (calibration.status === "error") return <ErrorState message={calibration.error} />;

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
      <VisualizationPlaceholder title="Comparação formal dos modelos" description="Estrutura reservada para AP média e dispersão entre folds." asset="MODEL_COMPARISON · model_comparison.json" />
      <VisualizationPlaceholder title="Avaliação final e calibração" description="Estrutura reservada para resultados finais de 2025 e diagnóstico de calibração." asset="FINAL_2025 + CALIBRATION_2025" />
    </div>
  );
}
