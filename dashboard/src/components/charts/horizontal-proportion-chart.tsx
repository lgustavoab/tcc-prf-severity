"use client";

import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/charts/chart-card";
import { CHART_COLORS } from "@/lib/constants/charts";
import { formatInteger, formatPercent } from "@/lib/formatting/numbers";
import type { DisplayAggregate } from "@/lib/data/exploration";

interface HorizontalProportionChartProps {
  id: string;
  title: string;
  description: string;
  rows: DisplayAggregate[];
  missingCategory?: string;
}

export function HorizontalProportionChart({ id, title, description, rows, missingCategory }: HorizontalProportionChartProps) {
  const height = Math.max(280, rows.length * 38 + 80);
  return (
    <ChartCard id={id} title={title} description={description}>
      <div className="chart-frame chart-horizontal-bars" style={{ height: `${height}px` }}>
        <BarChart responsive accessibilityLayer data={rows} layout="vertical" margin={{ top: 8, right: 24, left: 12, bottom: 4 }} style={{ width: "100%", height: "100%" }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" domain={[0, 1]} tickFormatter={(value) => formatPercent(Number(value))} tick={{ fill: CHART_COLORS.text }} />
          <YAxis dataKey="label" type="category" width={145} tick={{ fill: CHART_COLORS.text, fontSize: 12 }} />
          <Tooltip formatter={(value) => [formatPercent(Number(value)), "Proporção grave"]} />
          <Bar dataKey="severe_proportion" fill={CHART_COLORS.accent} radius={[0, 5, 5, 0]} isAnimationActive={false} />
        </BarChart>
      </div>
      {missingCategory && rows.some((row) => row.label === missingCategory) ? <p className="chart-note"><strong>{missingCategory}</strong> identifica informação ausente e permanece visível sem interpretação substantiva.</p> : null}
      <div className="data-table-wrap chart-data-table">
        <table><thead><tr><th>Categoria</th><th>Total</th><th>Graves</th><th>Não graves</th><th>Proporção grave</th></tr></thead><tbody>{rows.map((row) => <tr key={row.label}><td>{row.label}</td><td>{formatInteger(row.total_occurrences)}</td><td>{formatInteger(row.severe_occurrences)}</td><td>{formatInteger(row.non_severe_occurrences)}</td><td>{formatPercent(row.severe_proportion)}</td></tr>)}</tbody></table>
      </div>
    </ChartCard>
  );
}
