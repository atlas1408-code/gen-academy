import type { RetrievedChunk } from "../types";

/** Find the source a citation like "[Random 00:02:55-00:04:49]" refers to. */
function matchSource(cite: string, chunks: RetrievedChunk[]): number | null {
  const inner = cite.replace(/^\[|\]$/g, "");
  const idx = chunks.findIndex((c) => inner.includes(c.title) && inner.includes(c.timestamp));
  return idx >= 0 ? idx : null;
}

export function AnswerCard({
  text, chunks, refused, onCite,
}: {
  text: string;
  chunks: RetrievedChunk[];
  refused: boolean;
  onCite: (i: number) => void;
}) {
  const parts = text.split(/(\[[^\]]+\])/g);
  return (
    <div
      className="glass"
      style={{
        borderRadius: 14, padding: "16px 18px", fontSize: 14, lineHeight: 1.7,
        color: refused ? "#9a3b3b" : "var(--ink)",
        borderLeft: `3px solid ${refused ? "#cf8a8a" : "var(--accent)"}`,
        animation: "lg-up .45s ease",
      }}
    >
      <div style={{ fontSize: 11, color: "var(--ink-mute)", textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 8 }}>
        {refused ? "No answer" : "Answer"}
      </div>
      {parts.map((p, i) => {
        if (/^\[[^\]]+\]$/.test(p)) {
          const idx = matchSource(p, chunks);
          if (idx == null) return <span key={i} style={{ color: "var(--ink-mute)" }}>{p}</span>;
          return (
            <button
              key={i}
              onClick={() => onCite(idx)}
              style={{
                display: "inline", border: "none", cursor: "pointer", font: "inherit",
                background: "rgba(47,107,255,.13)", color: "var(--accent-strong)",
                borderRadius: 6, padding: "1px 6px", margin: "0 1px",
              }}
            >
              {p}
            </button>
          );
        }
        return <span key={i}>{p}</span>;
      })}
    </div>
  );
}
