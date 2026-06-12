import { IconDatabaseImport, IconMessageQuestion, IconArrowRight, IconPointFilled } from "@tabler/icons-react";
import { RAG_INTRO } from "../content";
import type { Phase } from "../App";

function ChoiceCard({
  icon, title, desc, onClick,
}: { icon: React.ReactNode; title: string; desc: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="glass"
      style={{
        flex: 1, textAlign: "left", border: "none", cursor: "pointer", borderRadius: 16, padding: "20px 20px",
        display: "flex", flexDirection: "column", gap: 8, transition: "transform .15s, box-shadow .15s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.transform = "translateY(-3px)")}
      onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0)")}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ display: "grid", placeItems: "center", width: 40, height: 40, borderRadius: 11, background: "rgba(47,107,255,.12)", color: "var(--accent)" }}>
          {icon}
        </span>
        <span style={{ fontSize: 17, fontWeight: 600, color: "var(--ink)" }}>{title}</span>
        <IconArrowRight size={16} color="var(--accent)" style={{ marginLeft: "auto" }} />
      </div>
      <span style={{ fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.55 }}>{desc}</span>
    </button>
  );
}

export function Landing({ onChoose }: { onChoose: (p: Phase) => void }) {
  return (
    <div style={{ animation: "lg-up .5s ease" }}>
      <h1 style={{ fontFamily: "var(--font-serif)", fontSize: 34, color: "var(--ink)", margin: "0 0 6px" }}>
        {RAG_INTRO.title}
      </h1>
      <p style={{ fontSize: 15, color: "var(--ink-soft)", lineHeight: 1.6, margin: "0 0 18px", maxWidth: 620 }}>
        {RAG_INTRO.lead}
      </p>

      <div className="glass" style={{ borderRadius: 16, padding: "16px 18px", marginBottom: 22 }}>
        {RAG_INTRO.points.map((p, i) => (
          <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start", padding: "5px 0", fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.55 }}>
            <IconPointFilled size={14} color="var(--accent)" style={{ flexShrink: 0, marginTop: 3 }} />
            <span>{p}</span>
          </div>
        ))}
      </div>

      <div style={{ fontSize: 12.5, color: "var(--ink-mute)", marginBottom: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>
        Choose a phase to explore
      </div>
      <div style={{ display: "flex", gap: 14 }}>
        <ChoiceCard
          icon={<IconDatabaseImport size={22} />}
          title="Ingest"
          desc="Add a transcript to the knowledge base — watch it get split, cleaned, embedded, and stored."
          onClick={() => onChoose("ingest")}
        />
        <ChoiceCard
          icon={<IconMessageQuestion size={22} />}
          title="Query"
          desc="Ask a question — watch it get embedded, matched against the corpus, and answered with citations."
          onClick={() => onChoose("query")}
        />
      </div>
    </div>
  );
}
