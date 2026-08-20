"use client";

import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
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

  return <div className="section-stack"><section className="surface"><div className="cards-grid">{metrics.slice(0, 4).map(([label, value]) => <article className="metric-card" key={label}><span>{label}</span><strong>{value}</strong></article>)}</div><p className="integration-note">Ponto de operação somente leitura. Não existe slider, simulação ou recomputação da matriz.</p></section><section className="surface"><div className="surface-header"><div><h2>Matriz de confusão publicada</h2><p>Decisões em 2025 no limiar congelado; valores copiados do asset.</p></div></div><div className="confusion-layout"><div className="confusion-matrix" role="img" aria-label={`Matriz de confusão: ${result.true_negative} verdadeiros negativos, ${result.false_positive} falsos positivos, ${result.false_negative} falsos negativos e ${result.true_positive} verdadeiros positivos.`}><span className="matrix-axis matrix-axis-predicted">Predição</span><span className="matrix-axis matrix-axis-actual">Real</span><span className="matrix-heading matrix-col-negative">Não grave</span><span className="matrix-heading matrix-col-positive">Grave</span><span className="matrix-heading matrix-row-heading matrix-row-negative">Não grave</span><article className="matrix-cell matrix-tn"><span>TN</span><strong>{formatInteger(result.true_negative)}</strong><small>verdadeiro negativo</small></article><article className="matrix-cell matrix-cell-emphasis matrix-fp"><span>FP</span><strong>{formatInteger(result.false_positive)}</strong><small>falso positivo</small></article><span className="matrix-heading matrix-row-heading matrix-row-positive">Grave</span><article className="matrix-cell matrix-cell-emphasis matrix-fn"><span>FN</span><strong>{formatInteger(result.false_negative)}</strong><small>falso negativo</small></article><article className="matrix-cell matrix-tp"><span>TP</span><strong>{formatInteger(result.true_positive)}</strong><small>verdadeiro positivo</small></article></div><div className="matrix-explanation"><p><strong>Precisão positiva:</strong> entre as ocorrências classificadas como positivas, {formatPercent(result.positive_precision)} eram graves.</p><p><strong>Sensibilidade:</strong> o modelo identificou {formatPercent(result.recall)} das ocorrências graves.</p><p><strong>F1:</strong> {formatMetric(result.f1)}, síntese do compromisso entre precisão positiva e sensibilidade.</p><p>Este ponto de operação é documentação científica, não recomendação de implantação.</p></div></div></section></div>;
}
