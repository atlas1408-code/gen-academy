import { useEffect, useState } from "react";

export interface Status {
  models: { embed: string; llm: string };
  retrieval: { top_k: number; hybrid_alpha: number; similarity_cutoff: number };
  index: { metric: string; dimension: number; vector_count: number };
  manifest: Record<string, unknown>;
}

/** Fetch the backend's live config once, so stage cards show truthful numbers. */
export function useStatus() {
  const [status, setStatus] = useState<Status | null>(null);
  useEffect(() => {
    fetch("/status")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);
  return status;
}
