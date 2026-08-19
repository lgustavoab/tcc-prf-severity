import { ModelsFoundation } from "@/components/scientific/models-foundation";
import { PageHeader } from "@/components/scientific/page-header";

export default function ModelsPage() {
  return <div className="section-stack"><PageHeader title="Modelos" description="Comparação, seleção e avaliação final apresentadas a partir de resultados congelados." status="FROZEN_RESULT" /><ModelsFoundation /></div>;
}
