"""Agent 运行时上下文。"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai.memory.manager import MemoryManager


@dataclass
class AgentContext:
    """Agent Loop 共享上下文。"""

    config: Dict[str, Any]
    memory: MemoryManager
    session_id: str = ""
    engine: Any = None
    trajectory: List[Dict[str, Any]] = field(default_factory=list)
    mode: str = "hybrid"

    @property
    def agent_config(self) -> Dict[str, Any]:
        return self.config.get("agent", {})

    @property
    def max_steps(self) -> int:
        return int(self.agent_config.get("max_steps", 20))

    def record_step(self, tool: str, args: Dict, result: Dict) -> None:
        self.trajectory.append({"tool": tool, "args": args, "result": result})
