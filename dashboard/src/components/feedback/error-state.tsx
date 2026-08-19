export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state-message state-message-error" role="alert">
      <strong>Não foi possível carregar este conteúdo.</strong>
      <span>{message}</span>
    </div>
  );
}
