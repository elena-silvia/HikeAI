from dataclasses import dataclass, asdict
from typing import Dict, Any, List


@dataclass
class AgentCard:
    """
    Standardized Agent Card descriptor defining an agent's identity,
    role, operational capabilities, and I/O contract in an A2A ecosystem.
    """
    agent_id: str
    name: str
    version: str
    role: str
    description: str
    capabilities: List[str]
    inputs: Dict[str, str]
    outputs: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
