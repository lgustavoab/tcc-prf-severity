"use client";

import { useMemo, useState } from "react";

import { HorizontalProportionChart } from "@/components/charts/horizontal-proportion-chart";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { MultiSelectFilter } from "@/components/filters/multi-select-filter";
import { YearSelect } from "@/components/filters/year-select";
import { DATA_PATHS } from "@/lib/data/paths";
import { groupExploratoryRows, selectedOrAll, sumExploratoryCounts } from "@/lib/data/exploration";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger, formatPercent } from "@/lib/formatting/numbers";
import type { GeographyAsset } from "@/types/dashboard";

export function GeographyFoundation() {
  const asset = useDashboardAsset<GeographyAsset>(DATA_PATHS.geography, { assetId: "GEOGRAPHY" });
  const [year, setYear] = useState<number | "all">("all");
  const [uf, setUf] = useState("all");
  const [brs, setBrs] = useState(new Set<string>());

  const compatibleBrs = asset.status === "success" ? (uf === "all" ? asset.data.filters.brs : asset.data.filters.br_by_uf[uf] ?? []) : [];
  const selectedRows = useMemo(() => {
    if (asset.status !== "success") return [];
    return asset.data.data.filter(
      (row) =>
        (year === "all" || row.source_year === year) &&
        (uf === "all" || row.uf === uf) &&
        selectedOrAll(brs, row.br),
    );
  }, [asset, brs, uf, year]);

  if (asset.status === "loading") return <LoadingState />;
  if (asset.status === "error") return <ErrorState message={asset.error} />;

  const changeUf = (nextUf: string) => {
    setUf(nextUf);
    setBrs(new Set());
  };
  const summary = sumExploratoryCounts(selectedRows);
  const grouped = uf === "all"
    ? groupExploratoryRows(selectedRows, (row) => row.uf)
    : groupExploratoryRows(selectedRows, (row) => `BR ${row.br}`, (a, b) => Number.parseInt(a.label.replace("BR ", "")) - Number.parseInt(b.label.replace("BR ", "")));

  return (
    <div className="section-stack">
      <section className="surface">
        <div className="surface-header"><div><h2>Recorte geográfico</h2><p>As opções de BR são lidas de <code>br_by_uf</code> e incluem BR 0.</p></div></div>
        <div className="filter-panel">
          <YearSelect id="geography-year" label="Ano" years={asset.data.filters.years} value={year} onChange={setYear} />
          <label className="select-control" htmlFor="geography-uf"><span>UF</span><select id="geography-uf" value={uf} onChange={(event) => changeUf(event.target.value)}><option value="all">Todas as UFs</option>{asset.data.filters.ufs.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          <MultiSelectFilter legend="BR" options={compatibleBrs.map((br) => ({ value: String(br), label: `BR ${br}` }))} selected={brs} onChange={setBrs} />
        </div>
        <p className="integration-note"><strong>{formatInteger(selectedRows.length)}</strong> células geográficas selecionadas. Alterar a UF limpa BRs incompatíveis.</p>
      </section>
      {!summary ? <EmptyState /> : <section className="surface"><div className="cards-grid"><article className="metric-card"><span>Total no recorte</span><strong>{formatInteger(summary.total_occurrences)}</strong></article><article className="metric-card"><span>Graves no recorte</span><strong>{formatInteger(summary.severe_occurrences)}</strong></article><article className="metric-card"><span>Não graves</span><strong>{formatInteger(summary.non_severe_occurrences)}</strong></article><article className="metric-card"><span>Proporção grave</span><strong>{formatPercent(summary.severe_proportion)}</strong></article></div></section>}
      {grouped.length === 0 ? <EmptyState /> : <HorizontalProportionChart id="geography-proportion" title={uf === "all" ? "Comparação descritiva por UF" : `Comparação descritiva por BR em ${uf}`} description="Ordenação apenas geográfica para apresentação; não constitui ranking de perigo." rows={grouped} />}
    </div>
  );
}
