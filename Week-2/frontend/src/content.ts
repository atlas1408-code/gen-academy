// Educational copy — focused on RAG concepts (not frontend/backend architecture).

export const RAG_INTRO = {
  title: "Retrieval-Augmented Generation",
  lead:
    "RAG lets a language model answer questions from your documents instead of only its training data — so answers are grounded, current, and citable.",
  points: [
    "Ingest: prepare your documents — split, clean, embed, and store them so they're searchable by meaning.",
    "Query: ask a question — the system retrieves the most relevant pieces and the model answers using only those, with citations.",
    "If nothing relevant is found, it says so instead of making something up.",
  ],
};

export interface TourStep {
  key: string;
  title: string;
  body: string;
}

export const QUERY_TOUR: TourStep[] = [
  {
    key: "embed",
    title: "1 · Embed the question",
    body:
      "Your question is turned into a vector — a list of numbers that captures its meaning — using the same embedding model that was used on the documents. That shared space is what makes meaning-based search possible.",
  },
  {
    key: "retrieve",
    title: "2 · Hybrid search",
    body:
      "We find the most relevant chunks two ways at once: dense search (semantic meaning) and sparse search (exact keywords), then blend the scores. The closest chunks come back with a similarity score each.",
  },
  {
    key: "threshold",
    title: "3 · The threshold (refusal)",
    body:
      "If the best match isn't similar enough — below the cutoff — the system refuses with \"I couldn't find this in the lectures\" rather than guessing. Designing this refusal is what keeps a RAG system honest.",
  },
  {
    key: "generate",
    title: "4 · Cited generation",
    body:
      "The surviving chunks are handed to the language model with strict instructions: answer only from this context, and cite the lecture and timestamp for every claim.",
  },
];

export const INGEST_TOUR: TourStep[] = [
  {
    key: "load",
    title: "1 · Load",
    body:
      "The transcript is read and split into timestamped segments — each piece of speech paired with when it was said. Those timestamps become the citation anchors later.",
  },
  {
    key: "clean",
    title: "2 · Clean",
    body:
      "Speech-to-text mangles jargon. A glossary fixes it (e.g. \"cloud code\" → \"Claude Code\") so search matches the right terms instead of the transcription's mistakes.",
  },
  {
    key: "chunk",
    title: "3 · Chunk",
    body:
      "Segments are grouped into ~512-token chunks with a little overlap — big enough to carry a complete thought, small enough to stay precise. Each chunk keeps its timestamp range.",
  },
  {
    key: "embed",
    title: "4 · Embed",
    body:
      "Every chunk is turned into a vector that captures its meaning — the same kind of vector a question becomes at query time, so the two can be compared.",
  },
  {
    key: "store",
    title: "5 · Store",
    body:
      "Vectors, the original chunk text, and metadata are stored in a vector database (Pinecone). Re-ingesting the same file overwrites rather than duplicates, so it stays clean.",
  },
];
