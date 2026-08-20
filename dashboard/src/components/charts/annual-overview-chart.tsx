"use client";

import { Bar, BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/charts/chart-card";
import { CHART_COLORS } from "@/lib/constants/charts";
import { formatInteger, formatPercent } from "@/lib/formatting/numbers";
import type { OverviewRow } from "@/types/dashboard";

export function AnnualOverviewChart({ rows }: { rows: OverviewRow[] }) {
  const data = rows.filter((row) => row.source_year !== null);

  return (
    <ChartCard
      id="annual-overview"
      title="Composição anual das ocorrências"
      description="Evolução descritiva das contagens registradas; não representa tendência estatística."
    >
      <div className="chart-frame chart-standard">
        <BarChart responsive accessibilityLayer data={data} margin={{ top: 12, right: 12, left: 8, bottom: 4 }} style={{ width: "100%", height: "100%" }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="source_year" tick={{ fill: CHART_COLORS.text }} />
          <YAxis tick={{ fill: CHART_COLORS.text }} tickFormatter={(value) => formatInteger(Number(value))} width={76} />
          <Tooltip formatter={(value, name) => [formatInteger(Number(value)), String(name)]} labelFormatter={(label) => `Ano ${label}`} />
          <Legend />
          <Bar dataKey="non_severe_occurrences" name="Não graves" stackId="occurrences" fill={CHART_COLORS.nonSevere} isAnimationActive={false} />
          <Bar dataKey="severe_occurrences" name="Graves" stackId="occurrences" fill={CHART_COLORS.severe} isAnimationActive={false} />
        </BarChart>
      </div>
      <div className="data-table-wrap chart-data-table">
        <table>
          <thead><tr><th>Ano</th><th>Total</th><th>Graves</th><th>Não graves</th><th>Proporção grave</th></tr></thead>
          <tbody>{data.map((row) => <tr key={row.source_year}><td>{row.source_year}</td><td>{formatInteger(row.total_occurrences)}</td><td>{formatInteger(row.severe_occurrences)}</td><td>{formatInteger(row.non_severe_occurrences)}</td><td>{formatPercent(row.severe_proportion)}</td></tr>)}</tbody>
        </table>
      </div>
    </ChartCard>
  );
}
