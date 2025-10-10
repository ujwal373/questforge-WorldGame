from __future__ import annotations
from pydantic import BaseModel
from typing import Dict, Any, List

class Command(BaseModel):
    player_id: str
    intent: str
    args: Dict[str, Any] | None = None

class WorldResponse(BaseModel):
    story: str
    world: Dict[str, Any]
    choices: List[str]
