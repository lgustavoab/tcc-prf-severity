"use client";

import { useMemo, useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { VisualizationPlaceholder } from "@/components/feedback/visualization-placeholder";
import { MultiSelectFilter } from "@/components/filters/multi-select-filter";
import { YearSelect } from "@/components/filters/year-select";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger } from "@/lib/formatting/numbers";
import type { GeographyAsset } from "@/types/dashboard";

export function GeographyFoundation() {
  const asset = useDashboardAsset<GeographyAsset>(DATA_PATHS.geography, { assetId: "GEOGRAPHY" });
  const [year, setYear] = useState<number | "all">("all");
  const [uf, setUf] = useState("all");
  const [brs, setBrs] = useState(new Set<string>());

  const compatibleBrs = asset.status === "success" ? (uf === "all" ? asset.data.filters.brs : asset.data.filters.br_by_uf[uf] ?? []) : [];
  const selectedCells = useMemo(() => {
    if (asset.status !== "success") return 0;
    return asset.data.data.filter(
      (row) =>
        (year === "all" || row.source_year === year) &&
        (uf === "all" || row.uf === uf) &&
        (brs.size === 0 || brs.has(String(row.br))),
    ).length;
  }, [asset, brs, uf, year]);

  if (asset.status === "loading") return <LoadingState />;
  if (asset.status === "error") return <ErrorState message={asset.error} />;

  const changeUf = (nextUf: string) => {
    setUf(nextUf);
    setBrs(new Set());
  };

  return (
    <div className="section-stack">
      <section className="surface">
        <div className="surface-header"><div><h2>Recorte geográfico</h2><p>As opções de BR são lidas de <code>br_by_uf</code> e incluem BR 0.</p></div></div>
        <div className="filter-panel">
          <YearSelect id="geography-year" label="Ano" years={asset.data.filters.years} value={year} onChange={setYear} />
          <label className="select-control" htmlFor="geography-uf"><span>UF</span><select id="geography-uf" value={uf} onChange={(event) => changeUf(event.target.value)}><option value="all">Todas as UFs</option>{asset.data.filters.ufs.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          <MultiSelectFilter legend="BR" options={compatibleBrs.map((br) => ({ value: String(br), label: `BR ${br}` }))} selected={brs} onChange={setBrs} />
        </div>
        <p className="integration-note"><strong>{formatInteger(selectedCells)}</strong> células geográficas selecionadas. Alterar a UF limpa BRs incompatíveis.</p>
      </section>
      <VisualizationPlaceholder title="Visão geográfica descritiva" description="Área reservada para tabelas e barras acessíveis; nenhum mapa ou ranking é criado nesta fase." asset="GEOGRAPHY · geography.json" />
    </div>
  );
}
