import { useState } from "react";
import { IconSearch, IconLoader2 } from "@tabler/icons-react";
import { useSSE } from "../lib/useSSE";
import { useStageMachine } from "../lib/useStageMachine";
import { useStatus } from "../lib/useStatus";
import { StageTimeline } from "./StageTimeline";
import { SourcesPanel } from "./SourcesPanel";
import { AnswerCard } from "./AnswerCard";
import { QUERY_STAGES } from "../types";

const SAMPLES = [
  "What is a context window?",
  "What is the refusal path?",
  "What is the best recipe for pizza dough?",
];

export function QueryView() {
  const [q, setQ] = useState("What is a context window?");
  const { start } = useSSE();
  const status = useStatus();
  const { state, feed, reset } = useStageMachine(QUERY_STAGES);
  const [highlight, setHighlight] = useState<number | null>(null);
  const running = state.terminal === "running";
  const { data } = state;

  const run = (question = q) => {
    if (!question.trim() || running) return;
    setQ(question);
    setHighlight(null);
    reset();
    start(`/query?q=${encodeURIComponent(question.trim())}`, feed, () =>
      feed({ stage: "error", status: "error", message: "Connection lost — is the backend running?", elapsed_ms: 0, data: {} })
    );
  };

  return (
    <div>
      {/* input */}
      <div style={{ display: "flex", gap: 8, maxWidth: 760 }}>
        <input
          className="glass"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="Ask a question about the lectures…"
          style={{ flex: 1, height: 44, borderRadius: 12, padding: "0 15px", fontSize: 14, color: "var(--ink)", outline: "none" }}
        />
        <button onClick={() => run()} disabled={running}
          style={{
            display: "flex", alignItems: "center", gap: 6, background: "var(--accent)", color: "#fff", border: "none",
            borderRadius: 12, height: 44, padding: "0 20px", fontSize: 14, fontWeight: 500,
            cursor: running ? "default" : "pointer", opacity: running ? 0.5 : 1, boxShadow: "0 5px 15px rgba(47,107,255,.32)",
          }}>
          {running ? <IconLoader2 size={16} className="spin" /> : <IconSearch size={16} />} ask
        </button>
      </div>
      <div style={{ display: "flex", gap: 7, marginTop: 10, flexWrap: "wrap" }}>
        {SAMPLES.map((s) => (
          <button key={s} onClick={() => run(s)} className="glass"
            style={{ fontSize: 11.5, padding: "5px 11px", borderRadius: 999, color: "var(--ink-soft)", cursor: "pointer", border: "none" }}>
            {s}
          </button>
        ))}
      </div>

      {/* workspace: pipeline is centered while querying, then docks left and
          the results region (answer + sources) fills the right. */}
      {state.terminal !== "idle" && (
        <div className={`workspace${data.retrieved ? " has-results" : ""}`}>
          <div className="pipeline-col">
            <StageTimeline stages={QUERY_STAGES} state={state} status={status} />
          </div>

          {data.retrieved && (
            <div className="results-col">
              {data.answer ? (
                <AnswerCard text={data.answer} chunks={data.retrieved} refused={state.terminal === "refused"} onCite={setHighlight} />
              ) : (
                <div className="glass" style={{ borderRadius: 14, padding: "16px 18px", fontSize: "var(--fs-answer)", color: "var(--ink-mute)" }}>
                  Composing a cited answer…
                </div>
              )}
              <SourcesPanel
                chunks={data.retrieved}
                topScore={data.topScore}
                cutoff={data.cutoff}
                highlight={highlight}
                onSelect={setHighlight}
              />
            </div>
          )}
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
