import { MethodologyFoundation } from "@/components/scientific/methodology-foundation";
import { PageHeader } from "@/components/scientific/page-header";

export default function MethodologyPage() {
  return <div className="section-stack"><PageHeader title="Metodologia" description="Síntese documental do desfecho, desenho temporal, variáveis, preprocessing e fronteiras científicas." status="DOCUMENTATION" /><MethodologyFoundation /></div>;
}
