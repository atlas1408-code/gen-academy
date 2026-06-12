import { IconCheck, IconLoader2, IconExternalLink, IconChevronDown, IconChevronUp } from "@tabler/icons-react";
import type { Stage } from "../types";
import { STAGE_LABEL } from "../types";
import type { NodeState, PipelineState } from "../lib/useStageMachine";
import type { Status } from "../lib/useStatus";
import { stageMeta, type ToolKind } from "../stageInfo";
import { Elapsed } from "./Loader";

const TOOL_COLOR: Record<ToolKind, { bg: string; fg: string }> = {
  nebius: { bg: "rgba(47,107,255,.12)", fg: "var(--accent-strong)" },
  pinecone: { bg: "rgba(15,130,104,.12)", fg: "#0f8268" },
  local: { bg: "rgba(111,128,164,.14)", fg: "var(--ink-mute)" },
};

function Dot({ node }: { node: NodeState }) {
  const active = node === "active" || node === "progress";
  return (
    <div
      className="glass"
      style={{
        width: 28, height: 28, borderRadius: "50%", display: "grid", placeItems: "center",
        flexShrink: 0, zIndex: 1,
        border: active ? "1px solid rgba(47,107,255,.5)" : node === "done" ? "1px solid rgba(15,130,104,.4)" : undefined,
      }}
    >
      {node === "done" ? (
        <IconCheck size={15} color="#0f8268" />
      ) : active ? (
        <IconLoader2 size={14} color="var(--accent)" className="spin" />
      ) : (
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--ink-mute)", opacity: 0.5 }} />
      )}
    </div>
  );
}

/** Live data line(s) for a given stage. */
function StageData({ stage, data }: { stage: Stage; data: PipelineState["data"] }) {
  const mono: React.CSSProperties = { fontSize: 11.5, fontFamily: "monospace", color: "var(--accent-strong)", marginTop: 7, wordBreak: "break-word" };
  const meta: React.CSSProperties = { fontSize: 11.5, color: "var(--ink-mute)", marginTop: 7 };

  if (stage === "embed" && data.embeddingPreview)
    return <div style={mono}>[{data.embeddingPreview.map((x) => x.toFixed(3)).join(", ")}, …] · {data.embeddingDim}-dim</div>;

  if (stage === "retrieve" && data.topScore != null)
    return <div style={meta}>retrieved {data.retrieved?.length ?? 0} chunks · top score <b style={{ color: "var(--accent-strong)" }}>{data.topScore}</b> · cutoff {data.cutoff}</div>;

  if (stage === "load" && data.segmentCount != null)
    return <div style={meta}>{data.segmentCount} timestamped segments</div>;

  if (stage === "clean" && data.glossaryFixes != null)
    return <div style={meta}>{data.glossaryFixes} jargon fix{data.glossaryFixes === 1 ? "" : "es"} applied</div>;

  if (stage === "chunk" && data.chunkCount != null)
    return (
      <div style={{ marginTop: 7 }}>
        <div style={meta}>{data.chunkCount} chunks</div>
        {data.sampleChunk && (
          <div style={{ fontSize: 11.5, color: "var(--ink-soft)", marginTop: 4, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden", fontStyle: "italic" }}>
            “{data.sampleChunk}”
          </div>
        )}
      </div>
    );

  if (stage === "upsert" && data.upsertTotal != null) {
    const pct = Math.round(((data.upsertDone ?? 0) / data.upsertTotal) * 100);
    return (
      <div style={{ marginTop: 8 }}>
        <div style={meta}>{data.upsertDone ?? 0} / {data.upsertTotal} vectors</div>
        <div style={{ height: 4, borderRadius: 2, background: "rgba(47,107,255,.16)", marginTop: 4, overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${pct}%`, background: "var(--accent)", borderRadius: 2, transition: "width .3s" }} />
        </div>
      </div>
    );
  }
  return null;
}

export function StageTimeline({
  stages, state, status, collapsed, onToggleCollapse,
}: {
  stages: Stage[];
  state: PipelineState;
  status: Status | null;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}) {
  // Collapsed summary: a slim bar of done stages + total time (shown after a run).
  if (collapsed) {
    return (
      <button
        onClick={onToggleCollapse}
        className="glass"
        style={{
          display: "flex", alignItems: "center", gap: 10, width: "100%", textAlign: "left",
          border: "none", cursor: "pointer", borderRadius: 12, padding: "10px 14px",
        }}
      >
        <IconCheck size={15} color="#0f8268" />
        <span style={{ display: "flex", gap: 6, flexWrap: "wrap", flex: 1 }}>
          {stages.map((s, i) => (
            <span key={s} style={{ fontSize: 12, color: "var(--ink-soft)" }}>
              {STAGE_LABEL[s] ?? s}{i < stages.length - 1 ? " ·" : ""}
            </span>
          ))}
        </span>
        <span style={{ fontSize: 11.5, color: "var(--ink-mute)" }}>
          {(state.elapsedMs / 1000).toFixed(1)}s
        </span>
        <IconChevronDown size={15} color="var(--ink-mute)" />
      </button>
    );
  }

  return (
    <div style={{ marginTop: 6 }}>
      {onToggleCollapse && (
        <button onClick={onToggleCollapse}
          style={{ display: "flex", alignItems: "center", gap: 4, marginLeft: "auto", marginBottom: 8, background: "none", border: "none", color: "var(--ink-mute)", fontSize: 11.5, cursor: "pointer" }}>
          hide steps <IconChevronUp size={13} />
        </button>
      )}
      <div style={{ position: "relative" }}>
      {/* spine */}
      <div style={{ position: "absolute", left: 13, top: 16, bottom: 16, width: 2, background: "rgba(47,107,255,.15)" }} />
      {stages.map((s) => {
        const node = state.nodes[s] ?? "pending";
        const meta = stageMeta(s, status);
        const active = node === "active" || node === "progress";
        const tc = TOOL_COLOR[meta.toolKind];
        return (
          <div key={s} style={{ position: "relative", display: "flex", gap: 12, marginBottom: 16 }}>
            <Dot node={node} />
            <div
              className="glass"
              style={{
                flex: 1, padding: "13px 15px", borderRadius: 13,
                opacity: node === "pending" ? 0.62 : 1,
                border: active ? "1px solid rgba(47,107,255,.45)" : undefined,
                transition: "opacity .35s, border-color .35s",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span style={{ fontSize: 13.5, fontWeight: 600, color: "var(--ink)", textTransform: "capitalize" }}>
                  {STAGE_LABEL[s] ?? s}
                </span>
                <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 999, background: tc.bg, color: tc.fg, fontWeight: 500 }}>
                  {meta.tool}
                </span>
                {active && (
                  <span style={{ marginLeft: "auto", fontSize: 11.5, color: "var(--ink-mute)" }}>
                    <Elapsed since={state.startedAt} />
                  </span>
                )}
              </div>

              <div style={{ fontSize: 12.5, color: "var(--ink-soft)", lineHeight: 1.55, marginTop: 6 }}>
                {meta.summary}
              </div>

              <StageData stage={s} data={state.data} />

              {active && <div className="shim" style={{ marginTop: 9 }} />}

              {meta.docs && (
                <a
                  href={meta.docs.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: "inline-flex", alignItems: "center", gap: 4, marginTop: 9, fontSize: 11.5, color: "var(--accent)", textDecoration: "none" }}
                >
                  <IconExternalLink size={12} /> {meta.docs.label}
                </a>
              )}
            </div>
          </div>
        );
      })}
      </div>
    </div>
  );
}
