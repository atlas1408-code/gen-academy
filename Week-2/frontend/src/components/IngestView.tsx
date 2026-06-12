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

      {/* pipeline timeline */}
      <div style={{ marginTop: 16 }}>
        <StageTimeline stages={INGEST_STAGES} state={state} status={status} />
      </div>

      {state.terminal === "done" && (
        <div className="glass" style={{ marginTop: 6, padding: "13px 15px", borderRadius: 13, display: "flex", alignItems: "center", gap: 10, animation: "lg-up .45s ease" }}>
          <IconCircleCheck size={20} color="#0f8268" />
          <div style={{ fontSize: 13, color: "var(--ink)" }}>
            Ingested <b>{file?.name}</b>
            {data.chunkCount ? ` — ${data.chunkCount} chunks` : ""}
            {data.embeddingDim ? ` (${data.embeddingDim}-dim)` : ""} now searchable in Query.
          </div>
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
