from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Phase(str, Enum):
    CLARIFY = "clarify"
    PLAN = "plan"
    EXECUTE = "executed"
    HITL_APPROVAl = "hitl_approval"
    DONE = "done"
    FAILED = "failed"

class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class TaskNode(BaseModel):
    id: str
    description: str
    tool: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    approved: bool = False
    status: NodeStatus = NodeStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None

class SystemState():
    query: str
    phase: Phase = Phase.CLARIFY
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    clarification_answer: Optional[str] = None
    dag: Dict[str, TaskNode] = Field(default_factory=dict)
    iteration_count: int = 0
    error: Optional[str] = None