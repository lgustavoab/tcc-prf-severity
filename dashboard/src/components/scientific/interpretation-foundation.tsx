"use client";

import { useState } from "react";

import { PredictorContributionChart } from "@/components/charts/predictor-contribution-chart";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
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

  const rows = view === "source" ? source.data.data : transformed.data.data;

  return <div className="section-stack"><section className="surface"><div className="surface-header"><div><h2>Visões publicadas</h2><p>A alternância muda apenas a apresentação e preserva o ranking original.</p></div><label className="select-control" htmlFor="interpretation-view"><span>Apresentação</span><select id="interpretation-view" value={view} onChange={(event) => setView(event.target.value as View)}><option value="source">Variáveis de origem</option><option value="transformed">Top 15 transformadas</option></select></label></div><p className="integration-note">{rows.length} registros publicados nesta visão.</p></section><PredictorContributionChart view={view} rows={rows} /><aside className="scientific-caveat" aria-label="Limite da interpretação SHAP"><span className="caveat-mark" aria-hidden="true">i</span><div><strong>Interpretação não causal</strong><p>SHAP descreve o comportamento do modelo e não identifica causalidade. Representação, codificação one-hot e cardinalidade influenciam as contribuições; BR possui 125 colunas transformadas no asset publicado.</p></div></aside></div>;
}
