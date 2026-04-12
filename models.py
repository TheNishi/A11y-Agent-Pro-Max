from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Observation(BaseModel):
    html_content: str = Field(..., description="Current state of the HTML/DOM")
    accessibility_score: float = Field(..., description="Current accessibility percentage (0.0 to 1.0)")
    identified_issues: List[str] = Field(..., description="List of detected A11y violations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context info")

class State(BaseModel):
    html_content: str = Field(..., description="Current state of the HTML/DOM")
    accessibility_score: float = Field(..., description="Current accessibility percentage (0.0 to 1.0)")
    identified_issues: List[str] = Field(..., description="List of detected A11y violations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context info")
    steps_taken: int = Field(..., description="Number of steps taken in current episode")

class Action(BaseModel):
    # Support for batching multiple commands in one step for speed
    commands: List[str] = Field(..., description="List of commands to modify the DOM in one step")
    
    class Config:
        allow_population_by_field_name = True
        fields = {
            'commands': {'alias': 'action'} # Some use 'action'
        }

class StepResponse(BaseModel):
    observation: Observation
    reward: float = Field(..., description="The reward for the last step")
    score: float = Field(..., description="Current task score (0.01 to 0.99) for the grader")
    done: bool = Field(..., description="Whether the task is finished")
    info: Dict[str, Any]

class ResetResponse(BaseModel):
    observation: Observation
    info: Dict[str, Any]

class StateResponse(BaseModel):
    observation: Observation
    info: Dict[str, Any]

class GradeResponse(BaseModel):
    task_id: str
    score: float
    solved: bool
    feedback: List[str]

    # COMPLIANCE: Absolute naming safety for different SDK versions
    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        d['grade'] = d['score']
        d['is_solved'] = d['solved']
        d['task'] = d['task_id']
        return d
