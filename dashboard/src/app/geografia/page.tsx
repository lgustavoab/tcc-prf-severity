import { GeographyFoundation } from "@/components/scientific/geography-foundation";
import { PageHeader } from "@/components/scientific/page-header";
import { ScientificCaveat } from "@/components/scientific/scientific-caveat";

export default function GeographyPage() {
  return <div className="section-stack"><PageHeader title="Geografia" description="Contagens e proporções por ano, UF e BR, sem classificação de perigo." status="EXPLORATORY" /><GeographyFoundation /><ScientificCaveat /></div>;
}
