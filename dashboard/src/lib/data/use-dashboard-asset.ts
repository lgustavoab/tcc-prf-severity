"use client";

import { useEffect, useState } from "react";

import { fetchJson } from "@/lib/data/fetch-json";

interface AssetExpectation {
  assetId?: string;
  partId?: string;
  rootSchema?: boolean;
}

type LoadState<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export function useDashboardAsset<T>(path: string, expectation: AssetExpectation): LoadState<T> {
  const [state, setState] = useState<LoadState<T>>({
    status: "loading",
    data: null,
    error: null,
  });
  const assetId = expectation.assetId;
  const partId = expectation.partId;
  const rootSchema = expectation.rootSchema;

  useEffect(() => {
    const controller = new AbortController();

    fetchJson<T>(path, { assetId, partId, rootSchema }, controller.signal)
      .then((data) => setState({ status: "success", data, error: null }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message = error instanceof Error ? error.message : "Falha desconhecida ao carregar dados.";
        setState({ status: "error", data: null, error: message });
      });

    return () => controller.abort();
  }, [assetId, partId, path, rootSchema]);

  return state;
}
