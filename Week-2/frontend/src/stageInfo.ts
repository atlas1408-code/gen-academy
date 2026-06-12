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

  switch (stage) {
    case "embed":
      return {
        tool: `Nebius Token Factory · ${embModel}`,
        toolKind: "nebius",
        summary: `The text becomes a ${dim}-dimension vector capturing its meaning — the same embedding model is used for documents and questions, so they share one space.`,
        docs: { label: "Nebius embeddings docs", url: NEBIUS_EMBED_DOCS },
      };
    case "retrieve":
      return {
        tool: `Pinecone · ${metric}`,
        toolKind: "pinecone",
        summary: `Hybrid search blends dense semantic similarity with sparse BM25 keywords (α=${alpha}) and returns the top ${topk}. If the best score is below ${cutoff}, the system refuses instead of guessing.`,
        docs: { label: "Pinecone docs", url: PINECONE_DOCS },
      };
    case "generate":
      return {
        tool: `Nebius Token Factory · ${llm}`,
        toolKind: "nebius",
        summary: `The language model writes the answer using only the retrieved chunks, citing the lecture and timestamp for every claim.`,
        docs: { label: "Nebius docs", url: NEBIUS_DOCS },
      };
    case "load":
      return {
        tool: "local parser",
        toolKind: "local",
        summary: `The transcript is parsed into timestamped speech segments — each passage paired with when it was said.`,
      };
    case "clean":
      return {
        tool: "local glossary",
        toolKind: "local",
        summary: `Speech-to-text jargon is normalized before chunking (e.g. “cloud code” → “Claude Code”) so search matches the right terms.`,
      };
    case "chunk":
      return {
        tool: "tiktoken",
        toolKind: "local",
        summary: `Segments are grouped into ~512-token chunks with overlap — big enough to hold a complete thought, small enough to stay precise. Timestamps are preserved as citation anchors.`,
      };
    case "upsert":
      return {
        tool: `Pinecone · ${metric}`,
        toolKind: "pinecone",
        summary: `Each chunk's dense + sparse vectors, original text, and metadata are stored with a deterministic ID — so re-ingesting the same file overwrites rather than duplicates.`,
        docs: { label: "Pinecone docs", url: PINECONE_DOCS },
      };
    default:
      return { tool: "", toolKind: "local", summary: "" };
  }
}
