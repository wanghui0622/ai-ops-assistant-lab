from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import yaml

class HookRegistry:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        if config_path.exists():
            self.config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    def lifecycle_hooks(self) -> List[Dict[str, Any]]:
        return list(self.config.get("hooks", {}).get("lifecycle", []))
    def pre_post_hooks(self) -> List[Dict[str, Any]]:
        return list(self.config.get("hooks", {}).get("pre_post", []))
