interface VisualizationPlaceholderProps {
  title: string;
  description: string;
  asset: string;
}

export function VisualizationPlaceholder({ title, description, asset }: VisualizationPlaceholderProps) {
  return (
    <section className="visualization-placeholder" aria-label={title}>
      <div>
        <span className="eyebrow">Integração prevista na Fase 6D</span>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <code>{asset}</code>
    </section>
  );
}
