// Mirrors backend/rag/events.py StepEvent (see frontend/API.md).
export type Stage =
  | "load" | "clean" | "chunk" | "embed" | "upsert"   // ingest
  | "retrieve" | "rerank" | "generate"                 // query
  | "done" | "refuse" | "error";                       // terminal

export type Status = "start" | "progress" | "complete" | "error";

export interface StepEvent {
  stage: Stage;
  status: Status;
  message: string;
  elapsed_ms: number;
  data: Record<string, any>;
}

export interface RetrievedChunk {
  score: number;
  title: string;
  timestamp: string;
  timestamp_end?: string;
  speaker?: string;
  text: string;
}

// Visible pipeline nodes per phase (terminal stages aren't nodes).
export const QUERY_STAGES: Stage[] = ["embed", "retrieve", "rerank", "generate"];
export const INGEST_STAGES: Stage[] = ["load", "clean", "chunk", "embed", "upsert"];

export const STAGE_LABEL: Record<string, string> = {
  load: "load", clean: "clean", chunk: "chunk", embed: "embed", upsert: "store",
  retrieve: "retrieve", rerank: "rerank", generate: "generate",
};
