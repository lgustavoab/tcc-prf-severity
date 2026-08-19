interface AssetExpectation {
  assetId?: string;
  partId?: string;
  rootSchema?: boolean;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertIntegration(payload: unknown, expectation: AssetExpectation): void {
  if (!isRecord(payload)) {
    throw new Error("O asset não possui um objeto JSON válido.");
  }

  if (expectation.rootSchema) {
    if (payload.schema_version !== "1") {
      throw new Error("Versão de schema incompatível no manifesto.");
    }
    return;
  }

  if (!isRecord(payload.metadata) || payload.metadata.schema_version !== "1") {
    throw new Error("Metadados ausentes ou versão de schema incompatível.");
  }
  if (expectation.assetId && payload.metadata.asset_id !== expectation.assetId) {
    throw new Error(`Asset inesperado: esperado ${expectation.assetId}.`);
  }
  if (expectation.partId && payload.metadata.part_id !== expectation.partId) {
    throw new Error(`Parte inesperada: esperada ${expectation.partId}.`);
  }
}

export async function fetchJson<T>(
  path: string,
  expectation: AssetExpectation,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(path, { signal });
  if (!response.ok) {
    throw new Error(`Não foi possível carregar ${path} (${response.status}).`);
  }

  const payload: unknown = await response.json();
  assertIntegration(payload, expectation);
  return payload as T;
}
