"use client";

import { useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { VisualizationPlaceholder } from "@/components/feedback/visualization-placeholder";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import type { InterpretationSourceAsset, InterpretationTransformedAsset } from "@/types/dashboard";

type View = "source" | "transformed";

export function InterpretationFoundation() {
  const [view, setView] = useState<View>("source");
  const source = useDashboardAsset<InterpretationSourceAsset>(DATA_PATHS.interpretationSource, { assetId: "INTERPRETATION", partId: "source_predictors" });
  const transformed = useDashboardAsset<InterpretationTransformedAsset>(DATA_PATHS.interpretationTransformed, { assetId: "INTERPRETATION", partId: "transformed_top15" });
  if (source.status === "loading" || transformed.status === "loading") return <LoadingState />;
  if (source.status === "error") return <ErrorState message={source.error} />;
  if (transformed.status === "error") return <ErrorState message={transformed.error} />;

  const rows = view === "source" ? source.data.data.map((row) => ({ rank: row.rank, name: row.source_predictor, group: row.predictor_group })) : transformed.data.data.map((row) => ({ rank: row.rank, name: row.transformed_feature, group: row.predictor_group }));

  return <div className="section-stack"><section className="surface"><div className="surface-header"><div><h2>Visões publicadas</h2><p>A alternância muda apenas a apresentação e preserva a ordem original.</p></div><label className="select-control" htmlFor="interpretation-view"><span>Apresentação</span><select id="interpretation-view" value={view} onChange={(event) => setView(event.target.value as View)}><option value="source">Variáveis de origem</option><option value="transformed">Top 15 transformadas</option></select></label></div><div className="data-table-wrap"><table><thead><tr><th>Posição publicada</th><th>Variável</th><th>Grupo</th></tr></thead><tbody>{rows.slice(0, 5).map((row) => <tr key={`${view}-${row.rank}`}><td>{row.rank}</td><td>{row.name}</td><td>{row.group}</td></tr>)}</tbody></table></div><p className="integration-note">Prévia estrutural de 5 linhas; o asset contém {rows.length} registros na ordem publicada.</p></section><VisualizationPlaceholder title="Contribuições do modelo" description="Área reservada para as contribuições Tree SHAP já publicadas, sem cálculo ou nova ordenação." asset={view === "source" ? "INTERPRETATION · source_predictors.json" : "INTERPRETATION · transformed_top15.json"} /></div>;
}
