import type { ReactNode } from "react";

interface ChartCardProps {
  title: string;
  description: string;
  children: ReactNode;
  id?: string;
  className?: string;
}

export function ChartCard({ title, description, children, id, className = "" }: ChartCardProps) {
  const titleId = id ? `${id}-title` : undefined;
  const descriptionId = id ? `${id}-description` : undefined;

  return (
    <section className={`chart-card ${className}`.trim()} aria-labelledby={titleId} aria-describedby={descriptionId}>
      <header className="chart-card-header">
        <h3 id={titleId}>{title}</h3>
        <p id={descriptionId}>{description}</p>
      </header>
      {children}
    </section>
  );
}
