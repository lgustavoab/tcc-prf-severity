"use client";

import { CartesianGrid, Line, LineChart, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/charts/chart-card";
import { CHART_COLORS } from "@/lib/constants/charts";
import { formatInteger, formatPercent } from "@/lib/formatting/numbers";
import type { Calibration2025Asset } from "@/types/dashboard";

export function CalibrationChart({ rows }: { rows: Calibration2025Asset["data"] }) {
  return (
    <ChartCard id="calibration-2025" title="Calibração descritiva em 2025" description="Dez faixas quantílicas publicadas; a diagonal indica a referência y = x.">
      <div className="chart-frame chart-standard">
        <LineChart responsive accessibilityLayer data={rows} margin={{ top: 12, right: 20, left: 8, bottom: 8 }} style={{ width: "100%", height: "100%" }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
          <XAxis type="number" dataKey="mean_predicted_probability" domain={[0, 1]} tickFormatter={(value) => formatPercent(Number(value))} tick={{ fill: CHART_COLORS.text }} />
          <YAxis domain={[0, 1]} tickFormatter={(value) => formatPercent(Number(value))} tick={{ fill: CHART_COLORS.text }} width={64} />
          <Tooltip formatter={(value) => [formatPercent(Number(value)), "Proporção grave observada"]} labelFormatter={(value) => `Probabilidade média: ${formatPercent(Number(value))}`} />
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke={CHART_COLORS.reference} strokeDasharray="6 5" label="Referência y = x" />
          <Line dataKey="observed_severe_proportion" name="Observado" stroke={CHART_COLORS.xgboost} strokeWidth={2.5} dot={{ r: 4 }} isAnimationActive={false} />
        </LineChart>
      </div>
      <div className="data-table-wrap chart-data-table"><table><thead><tr><th>Faixa</th><th>n</th><th>Probabilidade média</th><th>Proporção observada</th></tr></thead><tbody>{rows.map((row) => <tr key={row.quantile_bin}><td>{row.quantile_bin}</td><td>{formatInteger(row.bin_count)}</td><td>{formatPercent(row.mean_predicted_probability)}</td><td>{formatPercent(row.observed_severe_proportion)}</td></tr>)}</tbody></table></div>
      <p className="chart-note">Diagnóstico visual congelado; não constitui prova categórica de calibração nem recalcula as faixas.</p>
    </ChartCard>
  );
}
