"use client";

import { useMemo, useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { VisualizationPlaceholder } from "@/components/feedback/visualization-placeholder";
import { MultiSelectFilter } from "@/components/filters/multi-select-filter";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger } from "@/lib/formatting/numbers";
import type { ExplorationContextualAsset, ExplorationTemporalAsset } from "@/types/dashboard";

const options = (values: Array<string | number>) => values.map((value) => ({ value: String(value), label: String(value) }));
const selectedOrAll = (selected: ReadonlySet<string>, value: string | number) => selected.size === 0 || selected.has(String(value));

export function ExplorationFoundation() {
  const temporal = useDashboardAsset<ExplorationTemporalAsset>(DATA_PATHS.explorationTemporal, {
    assetId: "EXPLORATION",
    partId: "temporal",
  });
  const contextual = useDashboardAsset<ExplorationContextualAsset>(DATA_PATHS.explorationContextual, {
    assetId: "EXPLORATION",
    partId: "contextual",
  });
  const [temporalYears, setTemporalYears] = useState(new Set<string>());
  const [weekdays, setWeekdays] = useState(new Set<string>());
  const [hours, setHours] = useState(new Set<string>());
  const [contextualYears, setContextualYears] = useState(new Set<string>());
  const [roadTypes, setRoadTypes] = useState(new Set<string>());
  const [weather, setWeather] = useState(new Set<string>());
  const [landUse, setLandUse] = useState(new Set<string>());

  const temporalCells = useMemo(() => {
    if (temporal.status !== "success") return 0;
    return temporal.data.data.filter(
      (row) => selectedOrAll(temporalYears, row.source_year) && selectedOrAll(weekdays, row.dia_semana) && selectedOrAll(hours, row.hour),
    ).length;
  }, [hours, temporal, temporalYears, weekdays]);

  const contextualCells = useMemo(() => {
    if (contextual.status !== "success") return 0;
    return contextual.data.data.filter(
      (row) =>
        selectedOrAll(contextualYears, row.source_year) &&
        selectedOrAll(roadTypes, row.tipo_pista) &&
        selectedOrAll(weather, row.condicao_metereologica) &&
        selectedOrAll(landUse, row.uso_solo),
    ).length;
  }, [contextual, contextualYears, landUse, roadTypes, weather]);

  if (temporal.status === "loading" || contextual.status === "loading") return <LoadingState label="Carregando os dois escopos exploratórios…" />;
  if (temporal.status === "error") return <ErrorState message={temporal.error} />;
  if (contextual.status === "error") return <ErrorState message={contextual.error} />;

  return (
    <div className="section-stack">
      <section className="surface">
        <div className="surface-header"><div><h2>Exploração temporal</h2><p>Estado local independente: ano, dia da semana e hora.</p></div></div>
        <div className="filter-panel">
          <MultiSelectFilter legend="Ano" options={options(temporal.data.filters.years)} selected={temporalYears} onChange={setTemporalYears} />
          <MultiSelectFilter legend="Dia da semana" options={options(temporal.data.filters.weekdays)} selected={weekdays} onChange={setWeekdays} />
          <MultiSelectFilter legend="Hora" options={temporal.data.filters.hours.map((hour) => ({ value: String(hour), label: `${hour}h` }))} selected={hours} onChange={setHours} />
        </div>
        <p className="integration-note"><strong>{formatInteger(temporalCells)}</strong> células agregadas selecionadas no asset temporal.</p>
        <VisualizationPlaceholder title="Associações temporais" description="A seleção será conectada a visualizações na 6D sem afetar o escopo contextual." asset="EXPLORATION · temporal.json" />
      </section>

      <section className="surface">
        <div className="surface-header"><div><h2>Exploração contextual</h2><p>Estado local independente: ano, pista, meteorologia e uso do solo.</p></div></div>
        <div className="filter-panel">
          <MultiSelectFilter legend="Ano" options={options(contextual.data.filters.years)} selected={contextualYears} onChange={setContextualYears} />
          <MultiSelectFilter legend="Tipo de pista" options={options(contextual.data.filters.road_types)} selected={roadTypes} onChange={setRoadTypes} />
          <MultiSelectFilter legend="Condição meteorológica" options={options(contextual.data.filters.weather_conditions)} selected={weather} onChange={setWeather} />
          <MultiSelectFilter legend="Uso do solo" options={options(contextual.data.filters.land_use)} selected={landUse} onChange={setLandUse} />
        </div>
        <p className="integration-note"><strong>{formatInteger(contextualCells)}</strong> células agregadas selecionadas no asset contextual.</p>
        <VisualizationPlaceholder title="Associações de via e ambiente" description="A seleção será conectada a visualizações na 6D sem afetar o escopo temporal." asset="EXPLORATION · contextual.json" />
      </section>
    </div>
  );
}
