import { useCallback, useEffect, useRef } from "react";
import type { StepEvent } from "../types";

/**
 * Low-level SSE connection. `start(url, onEvent, onError)` opens an EventSource,
 * parses each frame into a StepEvent, and auto-closes on a terminal stage
 * (done | refuse | error) or on connection error.
 */
export function useSSE() {
  const esRef = useRef<EventSource | null>(null);

  const stop = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
  }, []);

  const start = useCallback(
    (url: string, onEvent: (e: StepEvent) => void, onError?: () => void) => {
      stop();
      const es = new EventSource(url);
      esRef.current = es;
      es.onmessage = (m) => {
        let ev: StepEvent;
        try {
          ev = JSON.parse(m.data);
        } catch {
          return;
        }
        onEvent(ev);
        if (ev.stage === "done" || ev.stage === "refuse" || ev.stage === "error") {
          stop();
        }
      };
      es.onerror = () => {
        onError?.();
        stop();
      };
    },
    [stop]
  );

  useEffect(() => stop, [stop]); // clean up on unmount
  return { start, stop };
}
