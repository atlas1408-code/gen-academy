# Glass-Box RAG — Frontend API Contract

The backend (FastAPI, `backend/app.py`) exposes three endpoints. Two of them
**stream Server-Sent Events (SSE)** — one event per pipeline stage — which the UI
animates. This doc is the contract to design/prototype against.

**Base URL (dev):** `http://127.0.0.1:8000`
**Run backend:** `cd backend && ../.venv/bin/python -m uvicorn app:app --port 8000`

---

## The `StepEvent` (the unit of the stream)

Every frame on `/ingest` and `/query` is one JSON object:

```ts
interface StepEvent {
  stage: "load" | "clean" | "chunk" | "embed" | "upsert"      // ingest stages
       | "retrieve" | "generate"                              // query stages
       | "done" | "refuse" | "error";                         // terminal
  status: "start" | "progress" | "complete" | "error";
  message: string;        // human-readable, safe to show verbatim
  elapsed_ms: number;     // ms since the request started (for timing display)
  data: Record<string, any>;  // stage-specific payload (see below), kept small
}
```

SSE wire format (note the `data: ` prefix and blank-line terminator):

```
data: {"stage":"embed","status":"complete","message":"…","elapsed_ms":602,"data":{…}}

```

Drive the **pipeline diagram** off `stage` (which node lights up) and `status`
(start → pulse, complete → solid). Drive the **side panel** off `data`.

---

## `GET /query?q=<question>`  → SSE

Stages, in order. Terminal is either `done` (answer) or `refuse`.

| stage | status | notable `data` fields |
|---|---|---|
| `embed` | start → complete | `embedding_dim`, `embedding_preview` (first 8 dims) |
| `retrieve` | start → complete | `top_score`, `cutoff`, `retrieved[]` (see below) |
| `generate` | start → complete | — (only if not refused) |
| `done` | complete | `refused:false`, `answer`, `top_score`, `sources[]` |
| `refuse` | complete | `refused:true`, `answer`, `top_score`, `sources[]` |

`retrieved[]` / `sources[]` item shape:

```ts
interface RetrievedChunk {
  score: number;       // hybrid similarity (0..1-ish)
  title: string;       // e.g. "Week1 Session1"
  timestamp: string;   // chunk start, "HH:MM:SS" — the citation anchor
  text: string;        // chunk excerpt (truncated ~200 chars)
}
```

### Sample stream (answerable)
```json
{"stage":"embed","status":"start","message":"Embedding question via Nebius (Qwen/Qwen3-Embedding-8B)…","elapsed_ms":0,"data":{}}
{"stage":"embed","status":"complete","message":"Question embedded (4096-dim)","elapsed_ms":602,"data":{"embedding_dim":4096,"embedding_preview":[0.0328,-0.0098,-0.0099,-0.0133,0.0256,-0.0181,-0.0005,0.0103]}}
{"stage":"retrieve","status":"start","message":"Hybrid search top-8 (α=0.7) in Pinecone…","elapsed_ms":603,"data":{}}
{"stage":"retrieve","status":"complete","message":"Retrieved 8 chunks (top score 0.787)","elapsed_ms":3766,"data":{"top_score":0.787,"cutoff":0.4,"retrieved":[{"score":0.787,"title":"Week1 Session1","timestamp":"00:53:22","text":"…"}]}}
{"stage":"generate","status":"start","message":"Generating cited answer via Nebius (meta-llama/Llama-3.3-70B-Instruct)…","elapsed_ms":3767,"data":{}}
{"stage":"generate","status":"complete","message":"Answer generated","elapsed_ms":8353,"data":{}}
{"stage":"done","status":"complete","message":"Done","elapsed_ms":8354,"data":{"refused":false,"answer":"A context window is… [Week1 Session1 00:53:22] …","top_score":0.787,"sources":[…]}}
```

### Sample stream (refusal — note: no `generate` stage)
```json
{"stage":"retrieve","status":"complete","message":"Retrieved 8 chunks (top score 0.243)","elapsed_ms":4067,"data":{"top_score":0.243,"cutoff":0.4,"retrieved":[…]}}
{"stage":"refuse","status":"complete","message":"Top score 0.243 < cutoff 0.4 — refusing","elapsed_ms":4067,"data":{"refused":true,"answer":"I couldn't find this in the lectures.","top_score":0.243,"sources":[…]}}
```

> Citations in `answer` look like `[Week1 Session1 00:53:22]`. The UI can link
> these to the matching `sources[]` entry by `title`+`timestamp`.

---

## `GET /ingest?force=<bool>`  → SSE

Streams ingestion of the transcript corpus. Stages: `load → clean → chunk →
embed → upsert → done`. If a file is unchanged and `force=false`, it emits a
single `done` with `skipped:true`.

| stage | notable `data` fields |
|---|---|
| `load` | `doc`, `file_size_kb`, then `segment_count` |
| `clean` | `glossary_fixes` (count of ASR jargon corrections) |
| `chunk` | `chunk_count`, `sample_chunk` |
| `embed` | `embedding_dim`, `embedding_preview` |
| `upsert` | `vector_count` |
| `done` | `file`, `chunk_count`, `embedding_dim`, `sample_chunk` (or `skipped`/`reason`) |

### Sample stream
```json
{"stage":"load","status":"complete","message":"Parsed 1033 timestamped segments","elapsed_ms":2,"data":{"doc":"week1-session1.txt","segment_count":1033}}
{"stage":"clean","status":"complete","message":"Applied glossary (30 jargon fixes)","elapsed_ms":39,"data":{"glossary_fixes":30}}
{"stage":"chunk","status":"complete","message":"Chunked into 87 chunks (~512 tok, 80 overlap)","elapsed_ms":56,"data":{"chunk_count":87,"sample_chunk":"Well, happy Saturday…"}}
{"stage":"embed","status":"complete","message":"Embedded 87 chunks (4096-dim)","elapsed_ms":13004,"data":{"embedding_dim":4096,"embedding_preview":[0.0081,0.0175,-0.0043,-0.024,0.0386]}}
{"stage":"upsert","status":"complete","message":"Upserted 87 vectors (dense + sparse)","elapsed_ms":46513,"data":{"vector_count":87}}
{"stage":"done","status":"complete","message":"Ingested week1-session1.txt","elapsed_ms":46515,"data":{"file":"week1-session1.txt","chunk_count":87,"embedding_dim":4096}}
```

---

## `GET /status`  → JSON

Snapshot for a header/status panel. Not a stream.

```json
{
  "models": {"embed": "Qwen/Qwen3-Embedding-8B", "llm": "meta-llama/Llama-3.3-70B-Instruct"},
  "retrieval": {"top_k": 8, "hybrid_alpha": 0.7, "similarity_cutoff": 0.4},
  "index": {"metric": "dotproduct", "dimension": 4096, "vector_count": 87},
  "manifest": {"week1-session1.txt": {"chunk_count": 87, "ingested_at": "…"}}
}
```

---

## Consuming SSE in React (sketch)

`EventSource` only does GET (which is why these endpoints are GET):

```ts
const es = new EventSource(`http://127.0.0.1:8000/query?q=${encodeURIComponent(q)}`);
es.onmessage = (e) => {
  const ev: StepEvent = JSON.parse(e.data);
  // update pipeline node [ev.stage] + side panel from ev.data
  if (ev.stage === "done" || ev.stage === "refuse" || ev.stage === "error") es.close();
};
es.onerror = () => es.close();
```

### Latency expectations (so the UI sets the right tone)
A query is **~6–8s** end to end today: question-embed ~0.6–3.7s, hybrid retrieve
~3s, generation (Llama-3.3-70B) ~4–5s. Design the animation to feel good while
each node is "working" for a couple seconds — this is a glass box, the wait is
the point. (Latency optimization is a later pass.)
```
