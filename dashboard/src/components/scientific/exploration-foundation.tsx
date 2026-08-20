"use client";

import { useMemo, useState } from "react";

import { HorizontalProportionChart } from "@/components/charts/horizontal-proportion-chart";
import { HourlyProportionChart } from "@/components/charts/hourly-proportion-chart";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { MultiSelectFilter } from "@/components/filters/multi-select-filter";
import { DATA_PATHS } from "@/lib/data/paths";
import { groupExploratoryRows, selectedOrAll } from "@/lib/data/exploration";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger } from "@/lib/formatting/numbers";
import type { ExplorationContextualAsset, ExplorationTemporalAsset } from "@/types/dashboard";

const options = (values: Array<string | number>) => values.map((value) => ({ value: String(value), label: String(value) }));

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

  const temporalRows = useMemo(() => {
    if (temporal.status !== "success") return [];
    return temporal.data.data.filter(
      (row) => selectedOrAll(temporalYears, row.source_year) && selectedOrAll(weekdays, row.dia_semana) && selectedOrAll(hours, row.hour),
    );
  }, [hours, temporal, temporalYears, weekdays]);

  const contextualRows = useMemo(() => {
    if (contextual.status !== "success") return [];
    return contextual.data.data.filter(
      (row) =>
        selectedOrAll(contextualYears, row.source_year) &&
        selectedOrAll(roadTypes, row.tipo_pista) &&
        selectedOrAll(weather, row.condicao_metereologica) &&
        selectedOrAll(landUse, row.uso_solo),
    );
  }, [contextual, contextualYears, landUse, roadTypes, weather]);

  if (temporal.status === "loading" || contextual.status === "loading") return <LoadingState label="Carregando os dois escopos exploratórios…" />;
  if (temporal.status === "error") return <ErrorState message={temporal.error} />;
  if (contextual.status === "error") return <ErrorState message={contextual.error} />;

  const byHour = groupExploratoryRows(temporalRows, (row) => `${row.hour}h`, (a, b) => Number.parseInt(a.label) - Number.parseInt(b.label));
  const weekdayOrder = new Map(temporal.data.filters.weekdays.map((weekday, index) => [weekday, index]));
  const byWeekday = groupExploratoryRows(temporalRows, (row) => row.dia_semana, (a, b) => (weekdayOrder.get(a.label) ?? 0) - (weekdayOrder.get(b.label) ?? 0));
  const byRoadType = groupExploratoryRows(contextualRows, (row) => row.tipo_pista);
  const byWeather = groupExploratoryRows(contextualRows, (row) => row.condicao_metereologica);
  const byLandUse = groupExploratoryRows(contextualRows, (row) => row.uso_solo);

  return (
    <div className="section-stack">
      <section className="surface">
        <div className="surface-header"><div><h2>Exploração temporal</h2><p>Estado local independente: ano, dia da semana e hora.</p></div></div>
        <div className="filter-panel">
          <MultiSelectFilter legend="Ano" options={options(temporal.data.filters.years)} selected={temporalYears} onChange={setTemporalYears} />
          <MultiSelectFilter legend="Dia da semana" options={options(temporal.data.filters.weekdays)} selected={weekdays} onChange={setWeekdays} />
          <MultiSelectFilter legend="Hora" options={temporal.data.filters.hours.map((hour) => ({ value: String(hour), label: `${hour}h` }))} selected={hours} onChange={setHours} />
        </div>
        <p className="integration-note"><strong>{formatInteger(temporalRows.length)}</strong> células agregadas selecionadas. As visualizações somam apenas contagens aditivas e calculam graves/total.</p>
        {temporalRows.length === 0 ? <EmptyState /> : <div className="chart-grid chart-grid-two"><HourlyProportionChart rows={byHour} /><HorizontalProportionChart id="weekday-proportion" title="Dia da semana" description="Proporção grave por dia da semana nas células temporais selecionadas." rows={byWeekday} /></div>}
      </section>

      <section className="surface">
        <div className="surface-header"><div><h2>Exploração contextual</h2><p>Estado local independente: ano, pista, meteorologia e uso do solo.</p></div></div>
        <div className="filter-panel">
          <MultiSelectFilter legend="Ano" options={options(contextual.data.filters.years)} selected={contextualYears} onChange={setContextualYears} />
          <MultiSelectFilter legend="Tipo de pista" options={options(contextual.data.filters.road_types)} selected={roadTypes} onChange={setRoadTypes} />
          <MultiSelectFilter legend="Condição meteorológica" options={options(contextual.data.filters.weather_conditions)} selected={weather} onChange={setWeather} />
          <MultiSelectFilter legend="Uso do solo" options={options(contextual.data.filters.land_use)} selected={landUse} onChange={setLandUse} />
        </div>
        <p className="integration-note"><strong>{formatInteger(contextualRows.length)}</strong> células agregadas selecionadas. Este estado não altera a exploração temporal.</p>
        {contextualRows.length === 0 ? <EmptyState /> : <div className="chart-grid"><HorizontalProportionChart id="road-type-proportion" title="Tipo de pista" description="Proporção grave por configuração de pista entre ocorrências registradas." rows={byRoadType} /><HorizontalProportionChart id="weather-proportion" title="Condição meteorológica" description="Todas as categorias publicadas são preservadas, inclusive informação ausente." rows={byWeather} missingCategory="Ignorado" /><HorizontalProportionChart id="land-use-proportion" title="Uso do solo" description="Categorias publicadas sem reclassificação automática como urbano ou rural." rows={byLandUse} /></div>}
      </section>
    </div>
  );
}
