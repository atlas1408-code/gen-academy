import { useState } from "react";
import { IconHome, IconChevronRight, IconBook2 } from "@tabler/icons-react";
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

  // Interactive screens get more room for the two-pane results; landing/tour
  // stay a comfortable reading width.
  const maxWidth = screen === "interactive" ? 980 : 820;

  return (
    <div style={{ minHeight: "100%", maxWidth, margin: "0 auto", padding: "26px 22px 60px", transition: "max-width .3s" }}>
      {/* header / breadcrumb */}
      <header style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 26 }}>
        <button onClick={home}
          style={{ display: "flex", alignItems: "center", gap: 7, background: "none", border: "none", cursor: "pointer", padding: 0 }}>
          <span style={{ display: "grid", placeItems: "center", width: 30, height: 30, borderRadius: 9, background: "var(--accent)", color: "#fff" }}>
            <IconBook2 size={17} />
          </span>
          <span style={{ fontFamily: "var(--font-serif)", fontSize: 19, color: "var(--ink)" }}>RAG Simulator</span>
        </button>
        {phase && (
          <>
            <IconChevronRight size={15} color="var(--ink-mute)" />
            <span style={{ fontSize: 14, color: "var(--ink-soft)" }}>{phaseLabel}</span>
            {screen === "interactive" && (
              <>
                <IconChevronRight size={15} color="var(--ink-mute)" />
                <span style={{ fontSize: 14, color: "var(--ink-mute)" }}>Try it</span>
              </>
            )}
          </>
        )}
        {phase && (
          <button onClick={home}
            style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 5, background: "none", border: "none", color: "var(--ink-mute)", fontSize: 12.5, cursor: "pointer" }}>
            <IconHome size={14} /> home
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
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 14 }}>
            <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 24, color: "var(--ink)", margin: 0 }}>
              {phase === "query" ? "Ask the lectures" : "Ingest a transcript"}
            </h2>
            <button onClick={() => setScreen("tour")}
              style={{ background: "none", border: "none", color: "var(--ink-mute)", fontSize: 12.5, cursor: "pointer" }}>
              replay walkthrough
            </button>
          </div>
          {phase === "query" ? <QueryView /> : <IngestView />}
        </div>
      )}
    </div>
  );
}
