import type { Status } from "./lib/useStatus";

export type ToolKind = "nebius" | "pinecone" | "local";

export interface StageMeta {
  tool: string;
  toolKind: ToolKind;
  summary: string;
  docs?: { label: string; url: string };
}

const NEBIUS_EMBED_DOCS = "https://docs.tokenfactory.nebius.com/api-reference/examples/create-embeddings";
const NEBIUS_DOCS = "https://docs.tokenfactory.nebius.com/";
const PINECONE_DOCS = "https://docs.pinecone.io/";

/** Descriptive + docs metadata per pipeline stage, enriched with live config. */
export function stageMeta(stage: string, st: Status | null): StageMeta {
  const dim = st?.index.dimension ?? 4096;
  const embModel = st?.models.embed ?? "Qwen/Qwen3-Embedding-8B";
  const llm = st?.models.llm ?? "meta-llama/Llama-3.3-70B-Instruct";
  const topk = st?.retrieval.top_k ?? 8;
  const alpha = st?.retrieval.hybrid_alpha ?? 0.7;
  const cutoff = st?.retrieval.similarity_cutoff ?? 0.4;
  const metric = st?.index.metric ?? "dotproduct";

  // Summaries are intentionally terse here (the Concept Tour carries the full
  // explanation) so the timeline cards stay compact and scannable.
  switch (stage) {
    case "embed":
      return {
        tool: `Nebius · ${embModel}`,
        toolKind: "nebius",
        summary: `Text → a ${dim}-dim vector (same model as the documents).`,
        docs: { label: "Nebius docs", url: NEBIUS_EMBED_DOCS },
      };
    case "retrieve":
      return {
        tool: `Pinecone · ${metric}`,
        toolKind: "pinecone",
        summary: `Hybrid dense + BM25 (α=${alpha}), top ${topk}; refuses below ${cutoff}.`,
        docs: { label: "Pinecone docs", url: PINECONE_DOCS },
      };
    case "generate":
      return {
        tool: `Nebius · ${llm}`,
        toolKind: "nebius",
        summary: `Answers only from the retrieved chunks, with citations.`,
        docs: { label: "Nebius docs", url: NEBIUS_DOCS },
      };
    case "load":
      return {
        tool: "local parser",
        toolKind: "local",
        summary: `Parsed into timestamped speech segments.`,
      };
    case "clean":
      return {
        tool: "local glossary",
        toolKind: "local",
        summary: `Fixes ASR jargon (e.g. “cloud code” → “Claude Code”).`,
      };
    case "chunk":
      return {
        tool: "tiktoken",
        toolKind: "local",
        summary: `~512-token chunks with overlap; timestamps preserved.`,
      };
    case "upsert":
      return {
        tool: `Pinecone · ${metric}`,
        toolKind: "pinecone",
        summary: `Dense + sparse + text stored; deterministic IDs (idempotent).`,
        docs: { label: "Pinecone docs", url: PINECONE_DOCS },
      };
    default:
      return { tool: "", toolKind: "local", summary: "" };
  }
}
