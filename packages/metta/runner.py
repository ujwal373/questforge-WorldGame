from __future__ import annotations
from pathlib import Path

RULES = Path(__file__).with_name("rules.metta").read_text()

def evaluate(world: dict) -> dict:
    # TODO: parse RULES and apply to world; passthrough for MVP
    return world
