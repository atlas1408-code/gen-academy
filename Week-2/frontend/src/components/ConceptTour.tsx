import { useState } from "react";
import { IconArrowRight, IconArrowLeft, IconPlayerPlay } from "@tabler/icons-react";
import type { TourStep } from "../content";
import type { Phase } from "../App";

export function ConceptTour({
  phase, steps, onDone, onSkip,
}: { phase: Phase; steps: TourStep[]; onDone: () => void; onSkip: () => void }) {
  const [i, setI] = useState(0);
  const last = i === steps.length - 1;
  const step = steps[i];

  return (
    <div style={{ animation: "lg-up .4s ease" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 14 }}>
        <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 24, color: "var(--ink)", margin: 0 }}>
          How {phase === "query" ? "a query" : "ingestion"} works
        </h2>
        <button onClick={onSkip}
          style={{ background: "none", border: "none", color: "var(--ink-mute)", fontSize: 12.5, cursor: "pointer" }}>
          skip →
        </button>
      </div>

      {/* step card */}
      <div className="glass" key={step.key} style={{ borderRadius: 16, padding: "22px 22px", minHeight: 150, animation: "lg-up .3s ease" }}>
        <div style={{ fontSize: 13, color: "var(--accent)", fontWeight: 600, marginBottom: 8 }}>{step.title}</div>
        <div style={{ fontSize: 15, color: "var(--ink)", lineHeight: 1.65 }}>{step.body}</div>
      </div>

      {/* progress dots */}
      <div style={{ display: "flex", gap: 7, justifyContent: "center", margin: "18px 0" }}>
        {steps.map((s, idx) => (
          <span key={s.key} onClick={() => setI(idx)}
            style={{
              width: idx === i ? 22 : 8, height: 8, borderRadius: 999, cursor: "pointer", transition: ".25s",
              background: idx === i ? "var(--accent)" : idx < i ? "rgba(47,107,255,.4)" : "rgba(47,107,255,.18)",
            }} />
        ))}
      </div>

      {/* controls */}
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <button onClick={() => setI((n) => Math.max(0, n - 1))} disabled={i === 0} className="glass"
          style={{ display: "flex", alignItems: "center", gap: 6, border: "none", borderRadius: 11, height: 42, padding: "0 16px",
            color: "var(--ink-soft)", cursor: i === 0 ? "default" : "pointer", opacity: i === 0 ? 0.4 : 1, fontSize: 13.5 }}>
          <IconArrowLeft size={15} /> back
        </button>
        {last ? (
          <button onClick={onDone}
            style={{ display: "flex", alignItems: "center", gap: 7, background: "var(--accent)", color: "#fff", border: "none",
              borderRadius: 11, height: 42, padding: "0 22px", fontSize: 14, fontWeight: 500, cursor: "pointer", boxShadow: "0 5px 15px rgba(47,107,255,.32)" }}>
            <IconPlayerPlay size={15} /> try it
          </button>
        ) : (
          <button onClick={() => setI((n) => Math.min(steps.length - 1, n + 1))}
            style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--accent)", color: "#fff", border: "none",
              borderRadius: 11, height: 42, padding: "0 20px", fontSize: 14, fontWeight: 500, cursor: "pointer", boxShadow: "0 5px 15px rgba(47,107,255,.32)" }}>
            next <IconArrowRight size={15} />
          </button>
        )}
      </div>
    </div>
  );
}
