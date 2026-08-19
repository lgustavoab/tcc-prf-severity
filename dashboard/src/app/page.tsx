import { OverviewFoundation } from "@/components/scientific/overview-foundation";
import { PageHeader } from "@/components/scientific/page-header";
import { ScientificCaveat } from "@/components/scientific/scientific-caveat";

export default function OverviewPage() {
  return <div className="section-stack"><PageHeader title="Visão Geral" description="Panorama dos acidentes registrados e porta de entrada para os resultados do estudo." status="MIXED" /><OverviewFoundation /><ScientificCaveat /></div>;
}
