"use client";

import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/charts/chart-card";
import { CHART_COLORS, PREDICTOR_LABELS } from "@/lib/constants/charts";
import { formatMetric, formatPercent } from "@/lib/formatting/numbers";
import type { InterpretationSourceAsset, InterpretationTransformedAsset } from "@/types/dashboard";

type SourceRow = InterpretationSourceAsset["data"][number];
type TransformedRow = InterpretationTransformedAsset["data"][number];

const TRANSFORMED_AXIS_LABELS: Record<string, string> = {
  condicao_metereologica: "Condição met.",
};

interface PredictorContributionChartProps {
  view: "source" | "transformed";
  rows: SourceRow[] | TransformedRow[];
}

export function PredictorContributionChart({ view, rows }: PredictorContributionChartProps) {
  const data = rows.map((row) => {
    const sourcePredictor = (row as SourceRow).source_predictor;
    const friendlyLabel = PREDICTOR_LABELS[sourcePredictor] ?? sourcePredictor;
    const category = view === "transformed" ? (row as TransformedRow).category_or_level : null;
    const axisBaseLabel = view === "transformed" ? TRANSFORMED_AXIS_LABELS[sourcePredictor] ?? friendlyLabel : friendlyLabel;

    return {
      ...row,
      label: category ? `${friendlyLabel}: ${category}` : friendlyLabel,
      axisLabel: category ? `${axisBaseLabel}: ${category}` : axisBaseLabel,
    };
  });
  const height = Math.max(520, data.length * 36 + 80);

  return (
    <ChartCard
      id={`predictor-${view}`}
      title={view === "source" ? "Contribuições por variável de origem" : "Top 15 de features transformadas"}
      description="Mean absolute SHAP em margem do modelo, na ordem publicada."
    >
      <div className="chart-frame chart-horizontal-bars" style={{ height: `${height}px` }}>
        <BarChart responsive accessibilityLayer data={data} layout="vertical" margin={{ top: 8, right: 22, left: 20, bottom: 4 }} style={{ width: "100%", height: "100%" }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" domain={[0, "auto"]} tickFormatter={(value) => formatMetric(Number(value))} />
          <YAxis dataKey="axisLabel" type="category" width={145} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} />
          <Tooltip formatter={(value) => [formatMetric(Number(value)), "Mean absolute SHAP"]} />
          <Bar dataKey="mean_absolute_shap" fill={CHART_COLORS.accent} radius={[0, 5, 5, 0]} isAnimationActive={false} />
        </BarChart>
      </div>
      <div className="data-table-wrap chart-data-table"><table><thead><tr><th>Posição</th><th>Variável</th><th>Nome técnico</th><th>Mean absolute SHAP</th>{view === "source" ? <th>Participação</th> : null}</tr></thead><tbody>{data.map((row) => <tr key={row.rank}><td>{row.rank}</td><td>{row.label}</td><td><code>{view === "source" ? (row as SourceRow).source_predictor : (row as TransformedRow).transformed_feature}</code></td><td>{formatMetric(row.mean_absolute_shap)}</td>{view === "source" ? <td>{formatPercent((row as SourceRow).contribution_share)}</td> : null}</tr>)}</tbody></table></div>
    </ChartCard>
  );
}
