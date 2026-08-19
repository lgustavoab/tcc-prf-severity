import { InterpretationFoundation } from "@/components/scientific/interpretation-foundation";
import { PageHeader } from "@/components/scientific/page-header";

export default function InterpretationPage() {
  return <div className="section-stack"><PageHeader title="Interpretação" description="Contribuições Tree SHAP publicadas para descrever o modelo, sem interpretação causal." status="FROZEN_RESULT" /><InterpretationFoundation /></div>;
}
