import type { PageStatus } from "@/lib/constants/navigation";

const STATUS_LABELS: Record<PageStatus, string> = {
  MIXED: "Resumo exploratório",
  EXPLORATORY: "Exploratório",
  FROZEN_RESULT: "Resultado congelado",
  DOCUMENTATION: "Documentação",
};

interface PageHeaderProps {
  title: string;
  description: string;
  status: PageStatus;
}

export function PageHeader({ title, description, status }: PageHeaderProps) {
  return (
    <header className="page-header">
      <span className={`status-badge status-${status.toLowerCase()}`}>{STATUS_LABELS[status]}</span>
      <h1>{title}</h1>
      <p>{description}</p>
    </header>
  );
}
