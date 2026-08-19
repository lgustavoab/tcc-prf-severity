const REQUIRED_MESSAGE =
  "Os percentuais representam a proporção de ocorrências graves entre acidentes registrados pela PRF. Sem denominador de exposição ao tráfego, esses valores não representam risco de ocorrência de acidente.";

export function ScientificCaveat({ detail }: { detail?: string }) {
  return (
    <aside className="scientific-caveat" aria-label="Cautela científica">
      <span className="caveat-mark" aria-hidden="true">i</span>
      <div>
        <strong>Cautela de interpretação</strong>
        <p>{REQUIRED_MESSAGE}</p>
        {detail ? <p className="caveat-detail">{detail}</p> : null}
      </div>
    </aside>
  );
}
