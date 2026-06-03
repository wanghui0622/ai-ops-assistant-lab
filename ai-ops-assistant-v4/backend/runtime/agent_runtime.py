"""
Agent Runtime：会话、Workflow YAML 驱动、Skill 链与 HITL 闸门。

【学习】对应 LEARNING.md 阶段 5。V4 用 Skill 替代 V1 的 Camel ChatAgent 流水线：
  - workflow YAML 的 skill_sequence 定义阶段顺序
  - hitl_gates 在指定 Skill 后暂停，等待用户 confirm_metrics / edit_metrics 等
  - HookDispatcher 向 SSE 推送 pre_skill / post_skill 事件（右侧时间线）

【学习】async/await：FastAPI 路由 await runtime.handle_message，避免阻塞事件循环。
【学习】阅读顺序：runtime/ops-analysis.yaml → skill_engine/skills/*/workflow.yaml → 本文件
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import yaml
from config import Settings, get_settings
from hook_engine.dispatcher import HookDispatcher
from hook_engine.events import HookEvent
from model_adapter.adapter import ModelAdapter
from runtime.session_manager import SessionManager
from runtime.session_state import ChatMessage, PendingAction, SessionPhase, SessionState
from skill_engine.executor import SkillExecutor
from skill_engine.registry import SkillRegistry
from skill_engine.types import SkillContext

class AgentRuntime:
    """编排核心：SessionManager 存状态，SkillExecutor 跑脚本，ModelAdapter 调 LLM。"""

    def __init__(self, settings: Optional[Settings] = None, hook_dispatcher: Optional[HookDispatcher] = None, session_manager: Optional[SessionManager] = None) -> None:
        self.settings = settings or get_settings()
        self.hooks = hook_dispatcher or HookDispatcher()
        self.sessions = session_manager or SessionManager()
        self.skills = SkillRegistry(self.settings.skills_dir)
        self.executor = SkillExecutor(self.hooks)
        self.model = ModelAdapter(self.settings)
    async def create_session(self) -> SessionState:
        s = self.sessions.create()
        await self.hooks.emit(HookEvent(type="session_start", session_id=s.session_id, summary="会话已创建"))
        return s
    async def handle_message(self, session_id: str, text: str) -> SessionState:
        """用户发送自然语言问题：按 workflow 顺序执行 Skill，遇 HITL 闸门则暂停。"""
        session = self._require(session_id)
        # 【学习】HITL 等待确认时，普通聊天不会推进流程，引导用户点 UI 按钮
        if session.phase in (SessionPhase.AWAITING_METRIC_REVIEW, SessionPhase.AWAITING_REPORT_CONFIRM):
            session.messages.append(ChatMessage(role="user", content=text))
            session.messages.append(ChatMessage(role="assistant", content="请先使用下方按钮确认或修改，再继续对话。"))
            return session
        session.user_question = text.strip()
        session.phase = SessionPhase.RUNNING
        session.skill_index = 0
        session.data = {"user_question": session.user_question}
        session.messages.append(ChatMessage(role="user", content=text))
        await self.hooks.emit(HookEvent(type="session_message", session_id=session_id, summary=f"用户: {text[:80]}", payload={"text": text}))
        wf = self.sessions.load_workflow(session.workflow_name, self.settings.workflows_dir)
        skills: List[str] = list(wf.get("skill_sequence") or [])
        for i, skill_name in enumerate(skills):
            session.skill_index = i
            await self._run_skill(session, skill_name)
            # 【学习】_gate_after 读 workflow YAML 的 hitl_gates.after_skill
            gate = self._gate_after(wf, skill_name)
            if gate:
                return await self._pause_hitl(session, gate)
        session.phase = SessionPhase.COMPLETED
        return session
    async def handle_action(self, session_id: str, action: str, payload: Optional[Dict[str, Any]] = None) -> SessionState:
        session = self._require(session_id)
        payload = payload or {}
        await self.hooks.emit(HookEvent(type="user_action", session_id=session_id, summary=f"用户操作: {action}", payload={"action": action, **payload}))
        wf = self.sessions.load_workflow(session.workflow_name, self.settings.workflows_dir)
        if action == "cancel":
            session.phase = SessionPhase.CANCELLED
            session.pending_action = None
            session.messages.append(ChatMessage(role="assistant", content="已取消当前分析流程。"))
            return session
        if action == "edit_metrics" and session.phase == SessionPhase.AWAITING_METRIC_REVIEW:
            mids = payload.get("metric_ids")
            if mids:
                mb = dict(session.data.get("metric_bundle") or {})
                mb["metric_ids"] = mids
                session.data["metric_bundle"] = mb
            session.pending_action = None
            session.phase = SessionPhase.RUNNING
            await self._run_skill(session, "compile-and-query")
            gate = self._gate_after(wf, "compile-and-query")
            if gate: return await self._pause_hitl(session, gate)
            return session
        if action == "confirm_metrics" and session.phase == SessionPhase.AWAITING_METRIC_REVIEW:
            session.pending_action = None
            session.phase = SessionPhase.RUNNING
            await self._run_skill(session, "analyze-insight")
            gate = self._gate_before(wf, "generate-report")
            if gate:
                return await self._pause_hitl(session, gate)
            await self._run_skill(session, "generate-report")
            session.phase = SessionPhase.COMPLETED
            await self.hooks.emit(HookEvent(type="report_ready", session_id=session_id, summary="报告已生成", payload={"markdown": session.markdown_report}))
            session.messages.append(ChatMessage(role="assistant", content="报告已生成，请查看中间面板。"))
            return session
        if action == "confirm_report" and session.phase == SessionPhase.AWAITING_REPORT_CONFIRM:
            session.pending_action = None
            session.phase = SessionPhase.RUNNING
            await self._run_skill(session, "generate-report")
            session.phase = SessionPhase.COMPLETED
            await self.hooks.emit(HookEvent(type="report_ready", session_id=session_id, summary="报告已生成", payload={"markdown": session.markdown_report}))
            session.messages.append(ChatMessage(role="assistant", content="报告已生成，请查看中间面板。"))
            return session
        session.messages.append(ChatMessage(role="assistant", content=f"未知或当前阶段不支持的操作: {action}"))
        return session
    async def _run_skill(self, session: SessionState, skill_name: str) -> None:
        skill = self.skills.get(skill_name)
        if not skill:
            raise ValueError(f"Skill 不存在: {skill_name}")
        ctx = SkillContext(session_id=session.session_id, user_question=session.user_question, data=dict(session.data), model_adapter=self.model, settings=self.settings)
        await self.hooks.emit(HookEvent(type="pre_skill_execute", session_id=session.session_id, skill_name=skill_name, summary=f"准备执行 {skill_name}"))
        result = await self.executor.execute(skill, ctx)
        await self.hooks.emit(HookEvent(type="post_skill_execute", session_id=session.session_id, skill_name=skill_name, summary=f"完成 {skill_name}", payload=result.outputs))
        if not result.ok:
            session.phase = SessionPhase.ERROR
            session.error = result.error
            raise RuntimeError(result.error or "skill failed")
        session.data.update(result.outputs)
        if skill_name == "understand-intent":
            session.data["understanding"] = session.data.get("understanding") or session.data.get("intent")
        if result.outputs.get("markdown_report"):
            session.markdown_report = result.outputs["markdown_report"]
        assistant_msg = self._skill_summary(skill_name, result.outputs)
        session.messages.append(ChatMessage(role="assistant", content=assistant_msg))
    def _skill_summary(self, skill_name: str, outputs: Dict[str, Any]) -> str:
        if skill_name == "understand-intent":
            u = outputs.get("understanding") or {}
            return f"已理解意图：**{u.get('intent_label', '—')}**，时间范围 {u.get('time_range_days', 7)} 天。"
        if skill_name == "select-metrics":
            mb = outputs.get("metric_bundle") or {}
            return f"已选择指标：`{mb.get('metric_ids', [])}`。"
        if skill_name == "compile-and-query":
            mb = outputs.get("metric_bundle") or {}
            qe = outputs.get("query_execution") or {}
            mids = mb.get("metric_ids") or []
            return f"已拉取 **{qe.get('row_count', 0)}** 天数据，指标：{', '.join(mids)}。请确认是否继续，或修改指标后重新查询。"
        if skill_name == "analyze-insight":
            ins = outputs.get("insight") or {}
            return f"分析完成：{ins.get('summary','')}"
        if skill_name == "generate-report":
            return "Markdown 报告已生成。"
        return f"Skill `{skill_name}` 执行完成。"
    async def _pause_hitl(self, session: SessionState, gate: dict) -> SessionState:
        phase = SessionPhase(gate.get("phase", "awaiting_metric_review"))
        session.phase = phase
        actions = list(gate.get("actions") or [])
        prompt = gate.get("prompt", "请确认是否继续")
        payload = {}
        if phase == SessionPhase.AWAITING_METRIC_REVIEW:
            payload = {"metric_bundle": session.data.get("metric_bundle"), "sql_compiler": session.data.get("sql_compiler")}
        session.pending_action = PendingAction(action_type=phase.value, prompt=prompt, actions=actions, payload=payload)
        session.messages.append(ChatMessage(role="assistant", content=prompt, actions=[{"id": a, "label": self._action_label(a)} for a in actions]))
        await self.hooks.emit(HookEvent(type="hitl_pause", session_id=session.session_id, summary=prompt, payload={"phase": phase.value, "actions": actions}))
        return session
    def _action_label(self, action: str) -> str:
        return {"confirm_metrics": "继续", "edit_metrics": "修改指标", "confirm_report": "生成报告", "cancel": "取消"}.get(action, action)
    def _gate_after(self, wf: dict, skill_name: str):
        for g in wf.get("hitl_gates") or []:
            if g.get("after_skill") == skill_name: return g
        return None
    def _gate_before(self, wf: dict, skill_name: str):
        for g in wf.get("hitl_gates") or []:
            if g.get("before_skill") == skill_name: return g
        return None
    def _require(self, session_id: str) -> SessionState:
        s = self.sessions.get(session_id)
        if not s: raise KeyError(f"session not found: {session_id}")
        return s
