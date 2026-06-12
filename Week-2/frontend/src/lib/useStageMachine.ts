import { useCallback, useRef, useState } from "react";
import type { RetrievedChunk, Stage, StepEvent } from "../types";

export type NodeState = "pending" | "active" | "progress" | "done" | "error";
export type Terminal = "idle" | "running" | "done" | "refused" | "error";

export interface PipelineState {
  nodes: Record<string, NodeState>;
  loaderText: string | null;
  startedAt: number | null; // for the elapsed-time display on slow stages
  terminal: Terminal;
  data: {
    embeddingPreview?: number[];
    embeddingDim?: number;
    retrieved?: RetrievedChunk[];
    topScore?: number;
    cutoff?: number;
    answer?: string;
    refused?: boolean;
    chunkCount?: number;
    glossaryFixes?: number;
    sampleChunk?: string;
    segmentCount?: number;
    upsertDone?: number;
    upsertTotal?: number;
  };
}

// Minimum time a stage stays visibly "active" so fast stages (load=2ms,
// clean=39ms) don't flash. Slow stages (embed, retrieve, upsert) overrun this
// naturally, so no artificial delay is added to them.
const MIN_MS = 1100;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * Consumes raw StepEvents through a paced queue and exposes the *visual* state.
 * Decoupled from event arrival: advancing transitions (start/complete/terminal)
 * are spaced at least MIN_MS apart; `progress` events update live, un-paced.
 */
export function useStageMachine(stages: Stage[]) {
  const blank = useCallback(
    (): PipelineState => ({
      nodes: Object.fromEntries(stages.map((s) => [s, "pending"])) as Record<string, NodeState>,
      loaderText: null,
      startedAt: null,
      terminal: "idle",
      data: {},
    }),
    [stages]
  );

  const [state, setState] = useState<PipelineState>(blank);
  const queue = useRef<StepEvent[]>([]);
  const pumping = useRef(false);
  const lastStepAt = useRef(0);

  const reset = useCallback(() => {
    queue.current = [];
    pumping.current = false;
    lastStepAt.current = 0;
    setState(blank());
  }, [blank]);

  const apply = useCallback(
    (ev: StepEvent) => {
      setState((prev) => {
        const nodes = { ...prev.nodes };
        const data = { ...prev.data };
        let { loaderText, startedAt, terminal } = prev;
        const d = ev.data || {};

        // Capture stage-specific data for the side panel.
        if (d.embedding_preview) data.embeddingPreview = d.embedding_preview;
        if (d.embedding_dim) data.embeddingDim = d.embedding_dim;
        if (d.retrieved) {
          data.retrieved = d.retrieved;
          data.topScore = d.top_score;
          data.cutoff = d.cutoff;
        }
        if (d.chunk_count != null) data.chunkCount = d.chunk_count;
        if (d.glossary_fixes != null) data.glossaryFixes = d.glossary_fixes;
        if (d.sample_chunk) data.sampleChunk = d.sample_chunk;
        if (d.segment_count != null) data.segmentCount = d.segment_count;
        if (d.upserted != null) {
          data.upsertDone = d.upserted;
          data.upsertTotal = d.vector_count;
        }

        if (ev.stage === "done") {
          if (d.answer) data.answer = d.answer;
          if (d.refused != null) data.refused = d.refused;
          terminal = data.refused ? "refused" : "done";
          loaderText = null;
          startedAt = null;
          stages.forEach((s) => {
            if (nodes[s] !== "done") nodes[s] = "done";
          });
        } else if (ev.stage === "refuse") {
          data.refused = true;
          if (d.answer) data.answer = d.answer;
          if (d.top_score != null) data.topScore = d.top_score;
          terminal = "refused";
          loaderText = null;
          startedAt = null;
        } else if (ev.stage === "error") {
          terminal = "error";
          loaderText = ev.message;
          startedAt = null;
        } else if (stages.includes(ev.stage)) {
          if (ev.status === "start") {
            nodes[ev.stage] = "active";
            loaderText = ev.message;
            startedAt = Date.now();
            terminal = "running";
          } else if (ev.status === "progress") {
            nodes[ev.stage] = "progress";
            loaderText = ev.message;
          } else if (ev.status === "complete") {
            nodes[ev.stage] = "done";
            loaderText = null;
            startedAt = null;
          }
        }
        return { nodes, data, loaderText, startedAt, terminal };
      });
    },
    [stages]
  );

  const pump = useCallback(async () => {
    if (pumping.current) return;
    pumping.current = true;
    while (queue.current.length) {
      const ev = queue.current.shift()!;
      const advancing =
        ev.status === "start" ||
        ev.status === "complete" ||
        ev.stage === "done" ||
        ev.stage === "refuse" ||
        ev.stage === "error";
      if (advancing) {
        const wait = Math.max(0, MIN_MS - (Date.now() - lastStepAt.current));
        if (wait) await sleep(wait);
        lastStepAt.current = Date.now();
      }
      apply(ev);
    }
    pumping.current = false;
  }, [apply]);

  const feed = useCallback(
    (ev: StepEvent) => {
      queue.current.push(ev);
      void pump();
    },
    [pump]
  );

  return { state, feed, reset };
}
