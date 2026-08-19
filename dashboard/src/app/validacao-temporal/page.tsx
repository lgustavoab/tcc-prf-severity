import { PageHeader } from "@/components/scientific/page-header";
import { TemporalValidationFoundation } from "@/components/scientific/temporal-validation-foundation";

export default function TemporalValidationPage() {
  return <div className="section-stack"><PageHeader title="Validação Temporal" description="Desempenho publicado nos três folds com janela de treinamento expansiva." status="FROZEN_RESULT" /><TemporalValidationFoundation /></div>;
}
