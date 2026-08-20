import type { ReactNode } from "react";

interface ChartCardProps {
  title: string;
  description: string;
  children: ReactNode;
  id?: string;
  className?: string;
  headingLevel?: "h2" | "h3";
}

export function ChartCard({
  title,
  description,
  children,
  id,
  className = "",
  headingLevel = "h3",
}: ChartCardProps) {
  const titleId = id ? `${id}-title` : undefined;
  const descriptionId = id ? `${id}-description` : undefined;
  const Heading = headingLevel;

  return (
    <section className={`chart-card ${className}`.trim()} aria-labelledby={titleId} aria-describedby={descriptionId}>
      <header className="chart-card-header">
        <Heading id={titleId}>{title}</Heading>
        <p id={descriptionId}>{description}</p>
      </header>
      {children}
    </section>
  );
}
