from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from config import get_settings
from skill_engine.loader import SkillDefinition, SkillLoader

class SkillRegistry:
    def __init__(self, skills_dir: Optional[Path] = None) -> None:
        self.loader = SkillLoader(skills_dir or get_settings().skills_dir)
        self._cache: Dict[str, SkillDefinition] = {}
        self.refresh()
    def refresh(self) -> None:
        self._cache = {s.name: s for s in self.loader.discover()}
    def list_skills(self) -> List[Dict[str, str]]:
        return [{"name": s.name, "description": s.description} for s in self._cache.values()]
    def get(self, name: str) -> Optional[SkillDefinition]:
        return self._cache.get(name) or self.loader.load(name)
