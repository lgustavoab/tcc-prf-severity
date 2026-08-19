import { PageHeader } from "@/components/scientific/page-header";
import { ThresholdFoundation } from "@/components/scientific/threshold-foundation";

export default function ThresholdPage() {
  return <div className="section-stack"><PageHeader title="Limiar de Decisão" description="Ponto de operação selecionado antes de 2025 e avaliação final somente leitura." status="FROZEN_RESULT" /><ThresholdFoundation /></div>;
}
