from pydantic import BaseModel
from typing import Literal, List, Optional

class ChimeraObservation(BaseModel):
    system_architecture: str
    target_code_snippet: str
    fuzzing_feedback: Optional[str] = None
    progress_percentage: float
    current_state_id: str

class ChimeraAction(BaseModel):
    action_type: Literal["analyze", "probe", "exploit"]
    payload_sequence: List[str]

class ChimeraReward(BaseModel):
    score: float
    is_done: bool
    explanation: str

class StepResponse(BaseModel):
    observation: ChimeraObservation
    reward: float
    done: bool
    info: dict
