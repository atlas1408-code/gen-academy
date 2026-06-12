import { useEffect, useRef, useState } from "react";
import type { RetrievedChunk } from "../types";

function SourceRow({
  c, index, highlighted, onSelect,
}: { c: RetrievedChunk; index: number; highlighted: boolean; onSelect: (i: number | null) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (highlighted) {
      setOpen(true);
      ref.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [highlighted]);

  const pct = Math.round(c.score * 100);
  return (
    <div
      ref={ref}
      onClick={() => { setOpen((o) => !o); onSelect(highlighted ? null : index); }}
      style={{
        padding: "8px 10px", borderRadius: 10, cursor: "pointer", marginBottom: 6,
        background: highlighted ? "rgba(47,107,255,.12)" : "rgba(255,255,255,.45)",
        border: highlighted ? "1px solid rgba(47,107,255,.5)" : "1px solid rgba(255,255,255,.6)",
        transition: "background .25s, border-color .25s",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}>
        <b style={{ color: "var(--accent-strong)", minWidth: 34 }}>{c.score.toFixed(3)}</b>
        <span style={{ flex: 1, height: 5, borderRadius: 3, background: "rgba(47,107,255,.15)", overflow: "hidden" }}>
          <span style={{ display: "block", height: "100%", width: `${pct}%`, background: "var(--accent)", borderRadius: 3 }} />
        </span>
      </div>
      <div style={{ fontSize: 11, color: "var(--ink-soft)", marginTop: 5 }}>
        {c.title} · {c.timestamp}{c.speaker ? ` · ${c.speaker}` : ""}
      </div>
      <div style={{
        fontSize: "var(--fs-read)", color: "var(--ink-soft)", marginTop: 4, lineHeight: 1.5,
        display: "-webkit-box", WebkitLineClamp: open ? 99 : 2, WebkitBoxOrient: "vertical", overflow: "hidden",
      }}>
        {c.text}
      </div>
    </div>
  );
}

export function SourcesPanel({
  chunks, topScore, cutoff, highlight, onSelect,
}: {
  chunks: RetrievedChunk[];
  topScore?: number;
  cutoff?: number;
  highlight: number | null;
  onSelect: (i: number | null) => void;
}) {
  return (
    <div className="glass" style={{ borderRadius: 13, padding: 12, minWidth: 0 }}>
      <div style={{ fontSize: 11, color: "var(--ink-mute)", textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 8, display: "flex", justifyContent: "space-between" }}>
        <span>Sources · {chunks.length}</span>
        {topScore != null && <span>top {topScore} · cutoff {cutoff}</span>}
      </div>
      {chunks.map((c, i) => (
        <SourceRow key={i} c={c} index={i} highlighted={highlight === i} onSelect={onSelect} />
      ))}
    </div>
  );
}
