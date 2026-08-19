"use client";

import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { VisualizationPlaceholder } from "@/components/feedback/visualization-placeholder";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger, formatMetric, formatPercent } from "@/lib/formatting/numbers";
import type { Threshold2025Asset } from "@/types/dashboard";

export function ThresholdFoundation() {
  const asset = useDashboardAsset<Threshold2025Asset>(DATA_PATHS.threshold2025, { assetId: "THRESHOLD_2025" });
  if (asset.status === "loading") return <LoadingState />;
  if (asset.status === "error") return <ErrorState message={asset.error} />;
  const result = asset.data.data[0];
  if (!result) return <EmptyState />;

  const metrics = [
    ["Limiar congelado", formatMetric(result.threshold)],
    ["Precisão positiva", formatPercent(result.positive_precision)],
    ["Sensibilidade", formatPercent(result.recall)],
    ["F1", formatMetric(result.f1)],
    ["Verdadeiros negativos", formatInteger(result.true_negative)],
    ["Falsos positivos", formatInteger(result.false_positive)],
    ["Falsos negativos", formatInteger(result.false_negative)],
    ["Verdadeiros positivos", formatInteger(result.true_positive)],
  ];

  return <div className="section-stack"><section className="surface"><div className="cards-grid">{metrics.map(([label, value]) => <article className="metric-card" key={label}><span>{label}</span><strong>{value}</strong></article>)}</div><p className="integration-note">Ponto de operação somente leitura. Não existe slider nem recomputação da matriz.</p></section><VisualizationPlaceholder title="Matriz de confusão publicada" description="Área reservada para a representação acessível dos quatro valores já carregados." asset="THRESHOLD_2025 · threshold_2025.json" /></div>;
}
