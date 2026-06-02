import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ReportCharts, type ReportChart } from "./ReportCharts";

export function ReportPanel({ markdown, charts = [] }: { markdown: string; charts?: ReportChart[] }) {
  return (
    <div className="flex flex-col h-full border-r border-slate-800">
      <header className="px-4 py-3 border-b border-slate-800 font-semibold">分析报告</header>
      <div className="flex-1 overflow-y-auto p-6 prose prose-invert prose-sm max-w-none">
        {markdown ? (
          <>
            <ReportCharts charts={charts} />
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
          </>
        ) : (
          <div className="text-slate-500 text-center mt-20">报告将在您确认生成后显示于此</div>
        )}
      </div>
    </div>
  );
}
