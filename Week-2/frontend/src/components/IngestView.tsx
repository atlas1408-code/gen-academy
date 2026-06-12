import { useRef, useState } from "react";
import { IconUpload, IconFileText, IconLoader2, IconCircleCheck } from "@tabler/icons-react";
import { useSSE } from "../lib/useSSE";
import { useStageMachine } from "../lib/useStageMachine";
import { useStatus } from "../lib/useStatus";
import { StageTimeline } from "./StageTimeline";
import { INGEST_STAGES } from "../types";

export function IngestView() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadErr, setUploadErr] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { start } = useSSE();
  const status = useStatus();
  const { state, feed, reset } = useStageMachine(INGEST_STAGES);
  const running = state.terminal === "running";
  const { data } = state;

  const run = async () => {
    if (!file || running) return;
    setUploadErr(null);
    reset();
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/upload", { method: "POST", body: fd });
      if (!res.ok) {
        setUploadErr((await res.json().catch(() => ({}))).detail ?? "Upload failed.");
        return;
      }
      const { filename } = await res.json();
      start(`/ingest?file=${encodeURIComponent(filename)}`, feed, () =>
        feed({ stage: "error", status: "error", message: "Connection lost — is the backend running?", elapsed_ms: 0, data: {} })
      );
    } catch {
      setUploadErr("Upload failed — is the backend running?");
    }
  };

  return (
    <div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <button onClick={() => inputRef.current?.click()} className="glass"
          style={{ display: "flex", alignItems: "center", gap: 7, height: 44, padding: "0 16px", borderRadius: 12, color: "var(--ink-soft)", cursor: "pointer", border: "none", fontSize: 13.5 }}>
          <IconUpload size={16} /> choose .txt transcript
        </button>
        <input ref={inputRef} type="file" accept=".txt" style={{ display: "none" }}
          onChange={(e) => { setFile(e.target.files?.[0] ?? null); setUploadErr(null); }} />
        {file && (
          <span className="glass" style={{ display: "flex", alignItems: "center", gap: 6, height: 44, padding: "0 14px", borderRadius: 12, fontSize: 12.5, color: "var(--ink)" }}>
            <IconFileText size={15} color="var(--accent)" /> {file.name}
            <span style={{ color: "var(--ink-mute)" }}>· {(file.size / 1024).toFixed(0)} KB</span>
          </span>
        )}
        <button onClick={run} disabled={!file || running}
          style={{
            marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, background: "var(--accent)", color: "#fff",
            border: "none", borderRadius: 12, height: 44, padding: "0 20px", fontSize: 14, fontWeight: 500,
            cursor: !file || running ? "default" : "pointer", opacity: !file || running ? 0.45 : 1, boxShadow: "0 5px 15px rgba(47,107,255,.32)",
          }}>
          {running ? <IconLoader2 size={16} className="spin" /> : <IconUpload size={16} />} ingest
        </button>
      </div>

      <p style={{ fontSize: 11.5, color: "var(--ink-mute)", marginTop: 8 }}>
        Upload any lecture transcript as a <b>.txt</b> file. Files already ingested are skipped automatically. (Slide decks coming soon.)
      </p>

      {/* pipeline — horizontal flow (linear ingest pipeline) */}
      {state.terminal !== "idle" && (
        <div style={{ marginTop: 18 }}>
          <StageTimeline stages={INGEST_STAGES} state={state} status={status} orientation="horizontal" />
        </div>
      )}

      {state.terminal === "done" && (
        <div className="glass" style={{ marginTop: 16, padding: "14px 16px", borderRadius: 13, animation: "lg-up .45s ease" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <IconCircleCheck size={20} color="#0f8268" />
            <div style={{ fontSize: 13.5, color: "var(--ink)" }}>
              Ingested <b>{file?.name}</b>
              {data.segmentCount ? ` — ${data.segmentCount} segments → ` : " — "}
              {data.chunkCount ? `${data.chunkCount} chunks` : ""}
              {data.embeddingDim ? ` (${data.embeddingDim}-dim)` : ""} · now searchable in Query.
            </div>
          </div>
          {data.sampleChunk && (
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid rgba(255,255,255,.6)" }}>
              <div style={{ fontSize: 11, color: "var(--ink-mute)", marginBottom: 4 }}>sample chunk</div>
              <div style={{ fontSize: "var(--fs-read)", color: "var(--ink-soft)", fontStyle: "italic", lineHeight: 1.5,
                display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                “{data.sampleChunk}”
              </div>
            </div>
          )}
        </div>
      )}

      {(uploadErr || state.terminal === "error") && (
        <div className="glass" style={{ marginTop: 14, padding: "12px 15px", borderRadius: 12, color: "#9a3b3b", fontSize: 13 }}>
          {uploadErr ?? state.loaderText ?? "Something went wrong."}
        </div>
      )}
    </div>
  );
}
