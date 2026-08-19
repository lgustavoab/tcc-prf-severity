"use client";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import type { Metadata, MethodologyDesignAsset, MethodologyFeaturesAsset } from "@/types/dashboard";

export function MethodologyFoundation() {
  const meta = useDashboardAsset<Metadata>(DATA_PATHS.meta, { assetId: "META" });
  const design = useDashboardAsset<MethodologyDesignAsset>(DATA_PATHS.methodologyDesign, { assetId: "METHODOLOGY_DESIGN" });
  const features = useDashboardAsset<MethodologyFeaturesAsset>(DATA_PATHS.methodologyFeatures, { assetId: "METHODOLOGY_FEATURES" });
  if (meta.status === "loading" || design.status === "loading" || features.status === "loading") return <LoadingState label="Carregando contratos metodológicos…" />;
  if (meta.status === "error") return <ErrorState message={meta.error} />;
  if (design.status === "error") return <ErrorState message={design.error} />;
  if (features.status === "error") return <ErrorState message={features.error} />;

  return <div className="section-stack"><section className="surface"><div className="cards-grid"><article className="metric-card"><span>Período</span><strong>{meta.data.data_period.start_year}–{meta.data.data_period.end_year}</strong><small>cinco anos</small></article><article className="metric-card"><span>Folds temporais</span><strong>{design.data.data.length}</strong><small>janela expansiva</small></article><article className="metric-card"><span>Representações principais</span><strong>{features.data.data.length}</strong><small>contrato publicado</small></article><article className="metric-card"><span>Preditores físicos</span><strong>{features.data.physical_predictors.length}</strong><small>matriz publicada</small></article></div></section><section className="surface"><h2>Desfecho e fronteira de uso</h2><p><strong>Desfecho:</strong> {meta.data.target_definition}</p><p><strong>População:</strong> {meta.data.source_scope}</p><p>O preprocessing, a política de leakage e as variáveis são apresentados a partir dos contratos publicados, sem reconstrução da matriz analítica.</p></section></div>;
}
