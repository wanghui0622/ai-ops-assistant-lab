import { useState } from "react";
import type { MetricItem } from "../types/session";

export function MetricEditor({ metrics, selected, onSave, onCancel, disabled }: {
  metrics: MetricItem[]; selected: string[]; onSave: (ids: string[]) => void; onCancel: () => void; disabled?: boolean;
}) {
  const [ids, setIds] = useState<string[]>(selected);
  const toggle = (id: string) => setIds((p) => p.includes(id) ? p.filter((x) => x !== id) : [...p, id]);
  return (
    <div className="mt-3 p-3 rounded-lg border border-slate-700 bg-slate-900/80">
      <div className="text-sm font-medium mb-2">选择指标（registry 白名单）</div>
      <div className="space-y-1 max-h-40 overflow-y-auto">
        {metrics.map((m) => (
          <label key={m.id} className="flex items-start gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={ids.includes(m.id)} onChange={() => toggle(m.id)} className="mt-1" />
            <span><span className="font-mono text-indigo-300">{m.id}</span> — {m.description}</span>
          </label>
        ))}
      </div>
      <div className="flex gap-2 mt-3">
        <button disabled={disabled || ids.length === 0} onClick={() => onSave(ids)} className="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-sm disabled:opacity-50">应用并重新查询</button>
        <button onClick={onCancel} className="px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-sm">取消</button>
      </div>
    </div>
  );
}
