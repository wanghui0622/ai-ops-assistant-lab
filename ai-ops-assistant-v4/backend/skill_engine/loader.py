from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

@dataclass
class SkillDefinition:
    name: str
    description: str
    skill_dir: Path
    workflow: Dict[str, Any]
    skill_md: str

class SkillLoader:
    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
    def discover(self) -> List[SkillDefinition]:
        out = []
        if not self.skills_dir.exists(): return out
        for d in sorted(self.skills_dir.iterdir()):
            if not d.is_dir(): continue
            skill_md = d / "SKILL.md"
            workflow_yaml = d / "workflow.yaml"
            if not skill_md.exists() or not workflow_yaml.exists(): continue
            wf = yaml.safe_load(workflow_yaml.read_text(encoding="utf-8")) or {}
            meta = self._parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            out.append(SkillDefinition(name=meta.get("name", d.name), description=meta.get("description", ""), skill_dir=d, workflow=wf, skill_md=skill_md.read_text(encoding="utf-8")))
        return out
    def load(self, name: str) -> Optional[SkillDefinition]:
        for s in self.discover():
            if s.name == name or s.skill_dir.name == name: return s
        return None
    def _parse_frontmatter(self, text: str) -> Dict[str, Any]:
        if not text.startswith("---"): return {}
        parts = text.split("---", 2)
        if len(parts) < 3: return {}
        return yaml.safe_load(parts[1]) or {}
