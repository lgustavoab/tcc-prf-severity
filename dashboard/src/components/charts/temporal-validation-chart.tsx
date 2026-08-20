"use client";

import { CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/charts/chart-card";
import { CHART_COLORS, MODEL_LABELS } from "@/lib/constants/charts";
import { formatMetric } from "@/lib/formatting/numbers";
import type { TemporalValidationAsset } from "@/types/dashboard";

export function TemporalValidationChart({ rows }: { rows: TemporalValidationAsset["data"] }) {
  const years = [...new Set(rows.map((row) => row.validation_year))].sort();
  const data = years.map((year) => ({
    validation_year: year,
    logistic: rows.find((row) => row.validation_year === year && row.model_id === "phase_4a_logistic_baseline")?.average_precision,
    random_forest: rows.find((row) => row.validation_year === year && row.model_id === "phase_4b_random_forest_baseline")?.average_precision,
    xgboost: rows.find((row) => row.validation_year === year && row.model_id === "phase_4c_xgboost_baseline")?.average_precision,
  }));

  return (
    <ChartCard id="temporal-validation" title="Average Precision por fold temporal" description="Três séries publicadas para validações em 2022, 2023 e 2024.">
      <div className="chart-frame chart-standard">
        <LineChart responsive accessibilityLayer data={data} margin={{ top: 12, right: 16, left: 8, bottom: 4 }} style={{ width: "100%", height: "100%" }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
          <XAxis dataKey="validation_year" tick={{ fill: CHART_COLORS.text }} />
          <YAxis domain={[0, 1]} tickFormatter={(value) => formatMetric(Number(value))} width={62} />
          <Tooltip formatter={(value, name) => [formatMetric(Number(value)), String(name)]} labelFormatter={(label) => `Validação ${label}`} />
          <Legend />
          <Line dataKey="logistic" name={MODEL_LABELS.phase_4a_logistic_baseline} stroke={CHART_COLORS.logistic} strokeWidth={2.5} dot={{ r: 4 }} isAnimationActive={false} />
          <Line dataKey="random_forest" name={MODEL_LABELS.phase_4b_random_forest_baseline} stroke={CHART_COLORS.randomForest} strokeWidth={2.5} strokeDasharray="7 4" dot={{ r: 4 }} isAnimationActive={false} />
          <Line dataKey="xgboost" name={MODEL_LABELS.phase_4c_xgboost_baseline} stroke={CHART_COLORS.xgboost} strokeWidth={3} dot={{ r: 4 }} isAnimationActive={false} />
        </LineChart>
      </div>
    </ChartCard>
  );
}
