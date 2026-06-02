export interface ActionButton { id: string; label: string }
export interface ChatMessage { role: string; content: string; actions?: ActionButton[] }
export interface PendingAction { action_type: string; prompt: string; actions: string[]; payload?: Record<string, unknown> }
export interface SessionState {
  session_id: string; phase: string; user_question: string; messages: ChatMessage[];
  pending_action?: PendingAction | null; markdown_report: string; data: Record<string, unknown>; error?: string | null;
}
export interface HookEvent { type: string; session_id: string; summary: string; skill_name?: string; step_id?: string; payload?: Record<string, unknown>; timestamp: string }
export interface MetricItem { id: string; name: string; description: string; source_table: string }
