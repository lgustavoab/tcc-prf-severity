import { ExplorationFoundation } from "@/components/scientific/exploration-foundation";
import { PageHeader } from "@/components/scientific/page-header";
import { ScientificCaveat } from "@/components/scientific/scientific-caveat";

export default function ExplorationPage() {
  return <div className="section-stack"><PageHeader title="Exploração" description="Agregações descritivas em dois escopos independentes: temporal e contextual." status="EXPLORATORY" /><ExplorationFoundation /><ScientificCaveat detail="Os controles de uma seção não recortam os dados da outra." /></div>;
}
