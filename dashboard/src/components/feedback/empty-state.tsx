export function EmptyState({ message = "Nenhum registro publicado corresponde à seleção." }) {
  return (
    <div className="state-message" role="status">
      {message}
    </div>
  );
}
