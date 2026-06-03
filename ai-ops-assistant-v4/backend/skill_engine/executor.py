"""
Skill 执行器：按 workflow.yaml 的步骤动态加载 scripts/run.py。

【学习】Python importlib.util.spec_from_file_location：
  不把 Skill 安装成 pip 包，也能按路径加载模块并调用指定函数（如 run）。

【学习】步骤输出 step_outputs 逐步 merge 到 ctx.data，供后续步骤与 Runtime 使用。
"""

from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from skill_engine.loader import SkillDefinition
from skill_engine.types import SkillContext, SkillResult

class SkillExecutor:
    def __init__(self, hook_dispatcher=None) -> None:
        self.hook_dispatcher = hook_dispatcher
    async def execute(self, skill: SkillDefinition, ctx: SkillContext) -> SkillResult:
        """执行单个 Skill：遍历 workflow.steps，每步调用 script 中的 fn(ctx, inp)。"""
        from hook_engine.events import HookEvent
        if self.hook_dispatcher:
            await self.hook_dispatcher.emit(HookEvent(type="skill_start", session_id=ctx.session_id, skill_name=skill.name, summary=f"开始执行 Skill: {skill.name}"))
        steps = skill.workflow.get("steps") or []
        step_outputs: Dict[str, Any] = {}
        try:
            for step in steps:
                sid = step["id"]
                if self.hook_dispatcher:
                    await self.hook_dispatcher.emit(HookEvent(type="skill_step", session_id=ctx.session_id, skill_name=skill.name, step_id=sid, summary=f"执行步骤: {sid}"))
                fn = self._load_fn(skill.skill_dir, step["script"], step["fn"])
                inp = {**ctx.data, **step_outputs}
                out = fn(ctx, inp)
                step_outputs[sid] = out
                ctx.data.update(out if isinstance(out, dict) else {})
            outputs = self._collect_outputs(skill.workflow, step_outputs, ctx.data)
            result = SkillResult(ok=True, outputs=outputs)
        except Exception as e:
            if self.hook_dispatcher:
                await self.hook_dispatcher.emit(HookEvent(type="skill_error", session_id=ctx.session_id, skill_name=skill.name, summary=str(e), payload={"error": str(e)}))
            return SkillResult(ok=False, error=str(e))
        if self.hook_dispatcher:
            await self.hook_dispatcher.emit(HookEvent(type="skill_complete", session_id=ctx.session_id, skill_name=skill.name, summary=f"Skill 完成: {skill.name}", payload=result.outputs))
        return result
    def _collect_outputs(self, workflow, step_outputs, ctx_data):
        keys = workflow.get("outputs") or list(step_outputs.keys())
        out = {}
        for k in keys:
            if k in ctx_data: out[k] = ctx_data[k]
            else:
                for v in step_outputs.values():
                    if isinstance(v, dict) and k in v: out[k] = v[k]
        return out
    def _load_fn(self, skill_dir: Path, script_rel: str, fn_name: str) -> Callable:
        """从 Skill 目录加载 Python 脚本并返回可调用函数（约定签名 fn(ctx, inp) -> dict）。"""
        script_path = skill_dir / script_rel
        mod_name = f"skill_{skill_dir.name}_{fn_name}"
        spec = importlib.util.spec_from_file_location(mod_name, script_path)
        if spec is None or spec.loader is None: raise ImportError(f"无法加载 {script_path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
        fn = getattr(mod, fn_name, None)
        if fn is None: raise AttributeError(f"{script_path} 缺少 {fn_name}")
        return fn
