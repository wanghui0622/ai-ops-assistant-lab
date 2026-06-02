import { useState } from "react";
import { ActionButtons } from "./ActionButtons";
import { MetricEditor } from "./MetricEditor";
import type { MetricItem, SessionState } from "../types/session";

export function ChatPanel({ session, metrics, loading, onSend, onAction }: {
  session: SessionState | null; metrics: MetricItem[]; loading: boolean;
  onSend: (t: string) => void; onAction: (a: string, p?: Record<string, unknown>) => void;
}) {
  const [input, setInput] = useState("");
  const [showEditor, setShowEditor] = useState(false);
  const pending = session?.pending_action;
  const mb = (pending?.payload?.metric_bundle || session?.data?.metric_bundle) as { metric_ids?: string[] } | undefined;
  const selected = mb?.metric_ids || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col h-full border-r border-slate-800">
      <header className="px-4 py-3 border-b border-slate-800 font-semibold">智能对话</header>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {(session?.messages || []).map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div className={`inline-block max-w-[90%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap ${m.role === "user" ? "bg-indigo-700" : "bg-slate-800"}`}>{m.content}</div>
            {m.actions && <ActionButtons actions={m.actions} onAction={(id) => id === "edit_metrics" ? setShowEditor(true) : onAction(id)} disabled={loading} />}
          </div>
        ))}
        {showEditor && pending?.action_type === "awaiting_metric_review" && (
          <MetricEditor metrics={metrics} selected={selected}
            onSave={(ids) => { onAction("edit_metrics", { metric_ids: ids }); setShowEditor(false); }}
            onCancel={() => setShowEditor(false)} disabled={loading} />
        )}
      </div>
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="例如：最近七天活跃度怎么样？" className="flex-1 rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm" disabled={loading} />
        <button type="submit" disabled={loading || !input.trim()} className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-sm">发送</button>
      </form>
    </div>
  );
}
