import { useState } from "react";
import { IconSearch, IconLoader2 } from "@tabler/icons-react";
import { useSSE } from "../lib/useSSE";
import { useStageMachine } from "../lib/useStageMachine";
import { PipelineRail } from "./PipelineRail";
import { Loader } from "./Loader";
import { QUERY_STAGES } from "../types";

const SAMPLES = [
  "What is a context window?",
  "What is fine-tuning and when do you use it?",
  "What is the best recipe for pizza dough?",
];

export function QueryView() {
  const [q, setQ] = useState("What is a context window?");
  const { start } = useSSE();
  const { state, feed, reset } = useStageMachine(QUERY_STAGES);
  const running = state.terminal === "running";
  const { data } = state;

  const run = (question = q) => {
    if (!question.trim() || running) return;
    setQ(question);
    reset();
    start(`/query?q=${encodeURIComponent(question.trim())}`, feed, () =>
      feed({ stage: "error", status: "error", message: "Connection lost — is the backend running?", elapsed_ms: 0, data: {} })
    );
  };

  return (
    <div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          className="glass"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="Ask a question about the lectures…"
          style={{ flex: 1, height: 44, borderRadius: 12, padding: "0 15px", fontSize: 14, color: "var(--ink)", outline: "none" }}
        />
        <button
          onClick={() => run()}
          disabled={running}
          style={{
            display: "flex", alignItems: "center", gap: 6, background: "var(--accent)", color: "#fff",
            border: "none", borderRadius: 12, height: 44, padding: "0 20px", fontSize: 14, fontWeight: 500,
            cursor: running ? "default" : "pointer", opacity: running ? 0.5 : 1, boxShadow: "0 5px 15px rgba(47,107,255,.32)",
          }}
        >
          {running ? <IconLoader2 size={16} className="spin" /> : <IconSearch size={16} />} ask
        </button>
      </div>

      {/* sample chips */}
      <div style={{ display: "flex", gap: 7, marginTop: 10, flexWrap: "wrap" }}>
        {SAMPLES.map((s) => (
          <button key={s} onClick={() => run(s)} className="glass"
            style={{ fontSize: 11.5, padding: "5px 11px", borderRadius: 999, color: "var(--ink-soft)", cursor: "pointer", border: "none" }}>
            {s}
          </button>
        ))}
      </div>

      <div style={{ marginTop: 16 }}>
        <PipelineRail stages={QUERY_STAGES} nodes={state.nodes} />
      </div>

      {state.loaderText && (
        <div style={{ marginTop: 14 }}>
          <Loader text={state.loaderText} since={state.startedAt} />
        </div>
      )}

      {data.embeddingPreview && (
        <div style={{ marginTop: 12, fontSize: 11.5, fontFamily: "monospace", color: "var(--accent-strong)" }}>
          embed [{data.embeddingPreview.map((x) => x.toFixed(3)).join(", ")}, …] · {data.embeddingDim}-dim
        </div>
      )}

      {data.retrieved && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 12, color: "var(--ink-mute)", marginBottom: 6 }}>
            retrieved (top score {data.topScore} · cutoff {data.cutoff})
          </div>
          {data.retrieved.map((r, i) => (
            <div key={i} className="glass" style={{ padding: "9px 12px", borderRadius: 11, marginBottom: 6 }}>
              <div style={{ fontSize: 11, color: "var(--accent-strong)", display: "flex", gap: 8, flexWrap: "wrap" }}>
                <b>{r.score.toFixed(3)}</b>
                <span>{r.title} · {r.timestamp}</span>
                {r.speaker && <span style={{ color: "var(--ink-mute)" }}>· {r.speaker}</span>}
              </div>
              <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                {r.text}
              </div>
            </div>
          ))}
        </div>
      )}

      {(state.terminal === "done" || state.terminal === "refused") && data.answer && (
        <div className="glass" style={{
          marginTop: 14, padding: "14px 16px", borderRadius: 13, fontSize: 13.5, lineHeight: 1.65,
          color: state.terminal === "refused" ? "#9a3b3b" : "var(--ink)", animation: "lg-up .45s ease",
        }}>
          {data.answer}
        </div>
      )}

      {state.terminal === "error" && (
        <div className="glass" style={{ marginTop: 14, padding: "12px 15px", borderRadius: 12, color: "#9a3b3b", fontSize: 13 }}>
          {state.loaderText ?? "Something went wrong."}
        </div>
      )}
    </div>
  );
}
