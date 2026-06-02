import { ChatPanel } from "./components/ChatPanel";
import { ReasoningPanel } from "./components/ReasoningPanel";
import { ReportPanel } from "./components/ReportPanel";
import type { ReportChart } from "./components/ReportCharts";
import { useSession } from "./hooks/useSession";

export default function App() {
  const { session, events, metrics, loading, error, sendMessage, sendAction } = useSession();
  const report = session?.data?.report as { charts?: ReportChart[] } | undefined;
  const charts = report?.charts ?? [];
  return (
    <div className="h-screen flex flex-col">
      <div className="px-4 py-2 border-b border-slate-800 flex items-center justify-between text-sm">
        <span className="font-bold text-lg">AI 运营助手 V4</span>
        <span className="text-slate-400">Agent Runtime · Skill Engine · Hook Engine</span>
        {session && <span className="text-xs font-mono text-slate-500">{session.phase}</span>}
      </div>
      {error && <div className="bg-red-900/50 text-red-200 px-4 py-2 text-sm">{error}</div>}
      <div className="flex-1 grid grid-cols-12 min-h-0">
        <div className="col-span-3 min-h-0"><ChatPanel session={session} metrics={metrics} loading={loading} onSend={sendMessage} onAction={sendAction} /></div>
        <div className="col-span-5 min-h-0"><ReportPanel markdown={session?.markdown_report || ""} charts={charts} /></div>
        <div className="col-span-4 min-h-0"><ReasoningPanel events={events} /></div>
      </div>
    </div>
  );
}
