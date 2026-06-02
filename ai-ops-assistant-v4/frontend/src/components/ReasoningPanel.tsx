import { useState } from "react";
import type { HookEvent } from "../types/session";

const TYPE_COLOR: Record<string, string> = {
  skill_start: "border-blue-500", skill_complete: "border-emerald-500", skill_step: "border-cyan-600",
  hitl_pause: "border-amber-500", report_ready: "border-purple-500", user_action: "border-pink-500", error: "border-red-500",
};

export function ReasoningPanel({ events }: { events: HookEvent[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);
  return (
    <div className="flex flex-col h-full">
      <header className="px-4 py-3 border-b border-slate-800 font-semibold">推理过程</header>
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {events.length === 0 && <div className="text-slate-500 text-sm">Hooks 事件将在此实时展示</div>}
        {events.map((ev, i) => (
          <div key={i} className={`border-l-2 pl-3 py-2 ${TYPE_COLOR[ev.type] || "border-slate-600"}`}>
            <div className="flex justify-between gap-2 text-xs text-slate-500">
              <span className="font-mono">{ev.type}</span>
              <span>{ev.timestamp?.slice(11, 19)}</span>
            </div>
            <div className="text-sm mt-1">{ev.summary}</div>
            {ev.skill_name && <div className="text-xs text-indigo-400 mt-0.5">skill: {ev.skill_name}</div>}
            {ev.payload && Object.keys(ev.payload).length > 0 && (
              <button className="text-xs text-slate-400 mt-1 underline" onClick={() => setExpanded(expanded === i ? null : i)}>详情</button>
            )}
            {expanded === i && ev.payload && (
              <pre className="mt-2 text-xs bg-slate-900 p-2 rounded overflow-x-auto max-h-40">{JSON.stringify(ev.payload, null, 2)}</pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
