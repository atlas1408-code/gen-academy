import { IconCheck, IconCircle, IconLoader2 } from "@tabler/icons-react";
import type { Stage } from "../types";
import { STAGE_LABEL } from "../types";
import type { NodeState } from "../lib/useStageMachine";

function StageIcon({ st }: { st: NodeState }) {
  if (st === "done") return <IconCheck size={14} color="#0f8268" />;
  if (st === "active" || st === "progress")
    return <IconLoader2 size={14} color="var(--accent)" className="spin" />;
  return <IconCircle size={13} color="var(--ink-mute)" />;
}

export function PipelineRail({
  stages,
  nodes,
}: {
  stages: Stage[];
  nodes: Record<string, NodeState>;
}) {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {stages.map((s) => {
        const st = nodes[s] ?? "pending";
        const active = st === "active" || st === "progress";
        return (
          <span
            key={s}
            className="glass"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 12,
              padding: "6px 12px",
              borderRadius: 10,
              color: st === "done" ? "#0f8268" : active ? "var(--ink)" : "var(--ink-mute)",
              background: active ? "rgba(255,255,255,.85)" : undefined,
              transition: "0.25s",
            }}
          >
            <StageIcon st={st} />
            {STAGE_LABEL[s] ?? s}
          </span>
        );
      })}
    </div>
  );
}
