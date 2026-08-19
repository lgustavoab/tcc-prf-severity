"use client";

import { useState } from "react";

import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { VisualizationPlaceholder } from "@/components/feedback/visualization-placeholder";
import { YearSelect } from "@/components/filters/year-select";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger, formatPercent } from "@/lib/formatting/numbers";
import type { OverviewAsset } from "@/types/dashboard";

export function OverviewFoundation() {
  const [year, setYear] = useState<number | "all">("all");
  const asset = useDashboardAsset<OverviewAsset>(DATA_PATHS.overview, { assetId: "OVERVIEW" });

  if (asset.status === "loading") return <LoadingState />;
  if (asset.status === "error") return <ErrorState message={asset.error} />;

  const row = year === "all" ? asset.data.summary : asset.data.data.find((item) => item.source_year === year);
  if (!row) return <EmptyState />;

  return (
    <div className="section-stack">
      <section className="surface">
        <div className="surface-header">
          <div>
            <h2>Panorama publicado</h2>
            <p>O filtro de ano é local a esta página e seleciona linhas já publicadas.</p>
          </div>
          <YearSelect id="overview-year" label="Período" years={asset.data.filters.years} value={year} onChange={setYear} />
        </div>
        <div className="cards-grid">
          <article className="metric-card"><span>Ocorrências registradas</span><strong>{formatInteger(row.total_occurrences)}</strong></article>
          <article className="metric-card"><span>Ocorrências graves</span><strong>{formatInteger(row.severe_occurrences)}</strong></article>
          <article className="metric-card"><span>Ocorrências não graves</span><strong>{formatInteger(row.non_severe_occurrences)}</strong></article>
          <article className="metric-card"><span>Proporção grave</span><strong>{formatPercent(row.severe_proportion)}</strong></article>
          <article className="metric-card"><span>Período apresentado</span><strong>{year === "all" ? "2021–2025" : year}</strong></article>
        </div>
      </section>
      <VisualizationPlaceholder
        title="Evolução e composição do período"
        description="Área reservada para os gráficos acessíveis da visão geral, sem antecipar a integração científica da Fase 6D."
        asset="OVERVIEW · overview/summary.json"
      />
    </div>
  );
}
