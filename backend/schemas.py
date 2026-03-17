from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

class RuleBase(BaseModel):
    condition: str
    priority: int = 0
    next_step_id: Optional[int] = None

class RuleCreate(RuleBase):
    pass

class Rule(RuleBase):
    id: int
    step_id: int

    model_config = ConfigDict(from_attributes=True)

class StepBase(BaseModel):
    name: str
    step_type: str = "action"

class StepCreate(StepBase):
    pass

class Step(StepBase):
    id: int
    workflow_id: int
    rules: List[Rule] = []

    model_config = ConfigDict(from_attributes=True)

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkflowCreate(WorkflowBase):
    pass

class Workflow(WorkflowBase):
    id: int
    steps: List[Step] = []

    model_config = ConfigDict(from_attributes=True)

class ExecutionLogBase(BaseModel):
    step_name: str
    evaluated_rules: List[Dict[str, Any]]
    next_step: Optional[str] = None
    status: str

class ExecutionLog(ExecutionLogBase):
    id: int
    execution_id: int

    model_config = ConfigDict(from_attributes=True)

class ExecutionBase(BaseModel):
    status: str

class Execution(ExecutionBase):
    id: int
    workflow_id: int
    logs: List[ExecutionLog] = []

    model_config = ConfigDict(from_attributes=True)

class ExecuteRequest(BaseModel):
    start_step_id: int
    data: Dict[str, Any]
