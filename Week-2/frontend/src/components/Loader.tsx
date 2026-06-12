import { useEffect, useState } from "react";
import { IconLoader2 } from "@tabler/icons-react";

/** Live elapsed-seconds ticker for slow stages. */
export function Elapsed({ since }: { since: number | null }) {
  const [, force] = useState(0);
  useEffect(() => {
    if (since == null) return;
    const id = setInterval(() => force((n) => n + 1), 250);
    return () => clearInterval(id);
  }, [since]);
  if (since == null) return null;
  return <span style={{ opacity: 0.65 }}>{((Date.now() - since) / 1000).toFixed(1)}s</span>;
}

export function Loader({
  text,
  since,
  progress,
}: {
  text: string;
  since: number | null;
  progress?: { done: number; total: number };
}) {
  const pct = progress && progress.total ? Math.round((progress.done / progress.total) * 100) : null;
  return (
    <div
      className="glass"
      style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 12 }}
    >
      <IconLoader2 size={15} className="spin" color="var(--accent)" />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12.5, color: "var(--ink-soft)", display: "flex", justifyContent: "space-between", gap: 8 }}>
          <span>{text}</span>
          <span style={{ display: "flex", gap: 8 }}>
            {pct != null && <span style={{ color: "var(--accent-strong)" }}>{pct}%</span>}
            <Elapsed since={since} />
          </span>
        </div>
        {pct != null ? (
          <div style={{ height: 4, borderRadius: 2, background: "rgba(47,107,255,.16)", marginTop: 6, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${pct}%`, background: "var(--accent)", borderRadius: 2, transition: "width .3s" }} />
          </div>
        ) : (
          <div className="shim" style={{ marginTop: 6 }} />
        )}
      </div>
    </div>
  );
}
