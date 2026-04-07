from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Observation(BaseModel):
    html_content: str = Field(..., description="Current state of the HTML/DOM")
    accessibility_score: float = Field(..., description="Current accessibility percentage (0.0 to 1.0)")
    identified_issues: List[str] = Field(..., description="List of detected A11y violations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context info")

class Action(BaseModel):
    # Support for batching multiple commands in one step for speed
    commands: List[str] = Field(..., description="List of commands to modify the DOM in one step")

class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]

class ResetResponse(BaseModel):
    observation: Observation
    info: Dict[str, Any]

class StateResponse(BaseModel):
    observation: Observation
    info: Dict[str, Any]
