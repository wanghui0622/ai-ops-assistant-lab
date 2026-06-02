import type { ActionButton } from "../types/session";

const LABELS: Record<string, string> = { confirm_metrics: "继续", edit_metrics: "修改指标", confirm_report: "生成报告", cancel: "取消" };

export function ActionButtons({ actions, onAction, disabled }: { actions: ActionButton[]; onAction: (id: string) => void; disabled?: boolean }) {
  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {actions.map((a) => (
        <button key={a.id} disabled={disabled} onClick={() => onAction(a.id)}
          className="px-3 py-1.5 rounded-lg text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50">
          {a.label || LABELS[a.id] || a.id}
        </button>
      ))}
    </div>
  );
}
