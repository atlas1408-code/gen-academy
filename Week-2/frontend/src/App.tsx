import { useState } from "react";
import { IconHome, IconChevronRight, IconSchema, IconRefresh } from "@tabler/icons-react";
import { Landing } from "./components/Landing";
import { ConceptTour } from "./components/ConceptTour";
import { QueryView } from "./components/QueryView";
import { IngestView } from "./components/IngestView";
import { QUERY_TOUR, INGEST_TOUR } from "./content";

export type Phase = "ingest" | "query";
type Screen = "landing" | "tour" | "interactive";

const seenKey = (p: Phase) => `tourSeen_${p}`;

export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [phase, setPhase] = useState<Phase | null>(null);

  const choose = (p: Phase) => {
    setPhase(p);
    setScreen(localStorage.getItem(seenKey(p)) ? "interactive" : "tour");
  };
  const finishTour = () => {
    if (phase) localStorage.setItem(seenKey(phase), "1");
    setScreen("interactive");
  };
  const home = () => { setScreen("landing"); setPhase(null); };
  const phaseLabel = phase === "query" ? "Query" : "Ingest";

  // Interactive screens get a wide workspace (pipeline docks left, results
  // fill the right); landing/tour stay a comfortable reading width.
  const maxWidth = screen === "interactive" ? 1400 : 820;

  return (
    <div style={{ minHeight: "100%", maxWidth, margin: "0 auto", padding: "26px 22px 24px", transition: "max-width .3s" }}>
      {/* header / breadcrumb */}
      <header style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 22 }}>
        <button onClick={home}
          style={{ display: "flex", alignItems: "center", gap: 9, background: "none", border: "none", cursor: "pointer", padding: 0 }}>
          <span style={{ display: "grid", placeItems: "center", width: 32, height: 32, borderRadius: 10, background: "var(--accent)", color: "#fff", boxShadow: "0 4px 12px rgba(47,107,255,.3)" }}>
            <IconSchema size={18} />
          </span>
          <span style={{ fontFamily: "var(--font-serif)", fontSize: 19, color: "var(--ink)", letterSpacing: 0.2 }}>RAG Simulator</span>
        </button>
        {phase && (
          <>
            <IconChevronRight size={15} color="var(--ink-mute)" style={{ flexShrink: 0 }} />
            <span style={{ fontSize: 14, color: "var(--ink-soft)", fontWeight: 500 }}>{phaseLabel}</span>
          </>
        )}
        {phase && (
          <button onClick={home}
            style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 5, background: "none", border: "none", color: "var(--ink-mute)", fontSize: 13, cursor: "pointer" }}>
            <IconHome size={15} /> Home
          </button>
        )}
      </header>

      {screen === "landing" && <Landing onChoose={choose} />}

      {screen === "tour" && phase && (
        <ConceptTour
          phase={phase}
          steps={phase === "query" ? QUERY_TOUR : INGEST_TOUR}
          onDone={finishTour}
          onSkip={finishTour}
        />
      )}

      {screen === "interactive" && phase && (
        <div style={{ animation: "lg-up .4s ease" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 16 }}>
            <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 25, color: "var(--ink)", margin: 0, lineHeight: 1.1 }}>
              {phase === "query" ? "Ask the lectures" : "Ingest a transcript"}
            </h2>
            <button onClick={() => setScreen("tour")} className="glass"
              style={{ display: "flex", alignItems: "center", gap: 6, border: "none", borderRadius: 999, padding: "7px 14px", color: "var(--ink-soft)", fontSize: 12.5, cursor: "pointer", flexShrink: 0 }}>
              <IconRefresh size={14} /> Replay walkthrough
            </button>
          </div>
          {phase === "query" ? <QueryView /> : <IngestView />}
        </div>
      )}
    </div>
  );
}
