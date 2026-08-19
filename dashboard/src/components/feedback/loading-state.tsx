export function LoadingState({ label = "Carregando dados publicados…" }: { label?: string }) {
  return (
    <div className="state-message" role="status" aria-live="polite">
      <span className="state-dot" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
