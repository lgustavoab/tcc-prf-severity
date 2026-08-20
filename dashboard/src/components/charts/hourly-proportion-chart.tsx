"use client";

import { CartesianGrid, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/charts/chart-card";
import { CHART_COLORS } from "@/lib/constants/charts";
import { formatInteger, formatPercent } from "@/lib/formatting/numbers";
import type { DisplayAggregate } from "@/lib/data/exploration";

export function HourlyProportionChart({ rows }: { rows: DisplayAggregate[] }) {
  return (
    <ChartCard id="hourly-proportion" title="Hora registrada" description="Proporção grave por hora nas células compatíveis com os filtros temporais.">
      <div className="chart-frame chart-standard">
        <LineChart responsive accessibilityLayer data={rows} margin={{ top: 12, right: 18, left: 4, bottom: 4 }} style={{ width: "100%", height: "100%" }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fill: CHART_COLORS.text }} interval="preserveStartEnd" minTickGap={16} />
          <YAxis domain={[0, 1]} tickFormatter={(value) => formatPercent(Number(value))} tick={{ fill: CHART_COLORS.text }} width={64} />
          <Tooltip formatter={(value) => [formatPercent(Number(value)), "Proporção grave"]} labelFormatter={(label) => `Hora ${label}`} />
          <Line dataKey="severe_proportion" name="Proporção grave" stroke={CHART_COLORS.accent} strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} isAnimationActive={false} />
        </LineChart>
      </div>
      <div className="compact-values" aria-label="Valores por hora">{rows.map((row) => <span key={row.label}><strong>{row.label}</strong> {formatPercent(row.severe_proportion)} · n={formatInteger(row.total_occurrences)}</span>)}</div>
    </ChartCard>
  );
}
