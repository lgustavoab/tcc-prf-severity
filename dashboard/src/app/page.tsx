import { AboutStudyFoundation } from "@/components/scientific/about-study-foundation";
import { PageHeader } from "@/components/scientific/page-header";

export default function AboutStudyPage() {
  return <div className="section-stack"><PageHeader title="Entenda o estudo" description="Análise dos fatores associados à gravidade de acidentes em rodovias federais brasileiras e avaliação de modelos de aprendizado de máquina." status="DOCUMENTATION" badgeLabel="TCC · Ciência de dados" /><AboutStudyFoundation /></div>;
}
