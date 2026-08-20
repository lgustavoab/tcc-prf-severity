"use client";

import { Bar, BarChart, CartesianGrid, Cell, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/charts/chart-card";
import { MODEL_COLORS, MODEL_LABELS } from "@/lib/constants/charts";
import { formatMetric } from "@/lib/formatting/numbers";
import type { ModelComparisonAsset } from "@/types/dashboard";

const MODEL_AXIS_LABELS: Record<string, string> = {
  XGBoost: "XGBoost",
  "Random Forest": "RF",
  "Regressão Logística": "RL",
};

export function ModelComparisonChart({ asset }: { asset: ModelComparisonAsset }) {
  const data = [...asset.data]
    .sort((a, b) => a.primary_metric_rank - b.primary_metric_rank)
    .map((row) => ({ ...row, label: MODEL_LABELS[row.model_id] ?? row.model_id, fill: MODEL_COLORS[row.model_id] }));

  return (
    <ChartCard id="model-comparison" headingLevel="h2" title="Average Precision média" description="Média não ponderada das três validações temporais, apresentada em escala de 0 a 1.">
      <div className="chart-frame chart-standard">
        <BarChart responsive accessibilityLayer data={data} margin={{ top: 12, right: 16, left: 4, bottom: 6 }} style={{ width: "100%", height: "100%" }}>
          <CartesianGrid stroke="#d6dee2" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "#34444b", fontSize: 12 }} tickFormatter={(value) => MODEL_AXIS_LABELS[String(value)] ?? String(value)} interval={0} />
          <YAxis domain={[0, 1]} tickFormatter={(value) => formatMetric(Number(value))} width={62} />
          <Tooltip formatter={(value) => [formatMetric(Number(value)), "Average Precision média"]} />
          <Bar dataKey="mean_average_precision" name="Average Precision média" radius={[6, 6, 0, 0]} isAnimationActive={false}>{data.map((row) => <Cell key={row.model_id} fill={row.fill} />)}</Bar>
        </BarChart>
      </div>
      <div className="data-table-wrap chart-data-table"><table><thead><tr><th>Modelo</th><th>AP média</th><th>Desvio padrão</th><th>ROC-AUC média</th><th>Brier médio</th></tr></thead><tbody>{data.map((row) => <tr key={row.model_id}><td><span className="series-key" style={{ backgroundColor: row.fill }} aria-hidden="true" />{row.label}</td><td>{formatMetric(row.mean_average_precision)}</td><td>{formatMetric(row.ap_standard_deviation)}</td><td>{formatMetric(row.mean_roc_auc)}</td><td>{formatMetric(row.mean_brier_score)}</td></tr>)}</tbody></table></div>
      <p className="chart-note">O XGBoost liderou sob a regra definida, mas as diferenças absolutas de AP média foram pequenas.</p>
    </ChartCard>
  );
}
