export interface ChartSeriesPoint {
  date: string;
  value: number;
}

export interface ReportChart {
  title: string;
  metric_id: string;
  metric_label: string;
  unit: string;
  series: ChartSeriesPoint[];
}

function fmt(value: number, unit: string): string {
  if (unit === "%") return `${value.toFixed(1)}%`;
  if (unit === "元" && value >= 10000) return `${(value / 10000).toFixed(1)}万`;
  if (value >= 10000) return `${(value / 1000).toFixed(0)}k`;
  return value.toLocaleString("zh-CN");
}

export function ReportCharts({ charts }: { charts: ReportChart[] }) {
  if (!charts.length) return null;
  return (
    <div className="space-y-6 not-prose my-6">
      {charts.map((chart) => {
        const max = Math.max(...chart.series.map((p) => p.value), 1);
        return (
          <div key={chart.metric_id} className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
            <div className="text-sm font-semibold text-slate-200 mb-1">{chart.title}</div>
            <div className="text-xs text-slate-400 mb-4">{chart.metric_label}</div>
            <div className="flex items-end gap-1 h-36">
              {chart.series.map((pt) => (
                <div key={pt.date} className="flex-1 flex flex-col items-center gap-1 min-w-0">
                  <div
                    className="w-full max-w-[48px] rounded-t bg-indigo-500/80 hover:bg-indigo-400 transition-colors"
                    style={{ height: `${Math.max(8, (pt.value / max) * 100)}%` }}
                    title={`${pt.date}: ${fmt(pt.value, chart.unit)}`}
                  />
                  <span className="text-[10px] text-slate-500 truncate w-full text-center">{pt.date.slice(5)}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 flex justify-between text-xs text-slate-400">
              <span>期初 {fmt(chart.series[0]?.value ?? 0, chart.unit)}</span>
              <span>期末 {fmt(chart.series[chart.series.length - 1]?.value ?? 0, chart.unit)}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
