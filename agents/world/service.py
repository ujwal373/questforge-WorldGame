from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

STATE_PATH = Path(__file__).with_name("state_seed.json")
app = FastAPI(title="World Service")
_state: Dict[str, Any] = json.loads(STATE_PATH.read_text())

class Intent(BaseModel):
    player_id: str
    intent: str
    args: Dict[str, Any] | None = None

@app.get("/state")
def get_state():
    return _state

@app.post("/intent")
def apply_intent(i: Intent):
    _state.setdefault("players", {}).setdefault(
        i.player_id, {"loc": "town_square", "inventory": []})
    player = _state["players"][i.player_id]
    args = i.args or {}

    if i.intent == "move":
        dest = args.get("target") or "town_square"
        player["loc"] = dest
    elif i.intent == "inspect":
        pass
    elif i.intent == "talk":
        target = args.get("target")
        if target == "blacksmith":
            for c in _state["characters"]:
                if c["id"] == "blacksmith":
                    c["mood"] = "neutral" if c["mood"] == "wary" else c["mood"]
    elif i.intent == "trade":
        target = args.get("target")
        item = args.get("item")
        if target == "blacksmith" and item == "rare_ore":
            inv = player["inventory"]
            if "rare_ore" in inv:
                inv.remove("rare_ore")
                inv.append("sword")
                for c in _state["characters"]:
                    if c["id"] == "blacksmith":
                        c["needs"] = [n for n in c["needs"] if n != "ore"]
                        c["trust"][i.player_id] = c["trust"].get(i.player_id, 0.0) + 0.2
            else:
                inv.append("rare_ore")

    for r in _state["regions"]:
        if r["id"] == "forest":
            r["danger"] = max(0.0, min(1.0, r["danger"] + 0.05))
    return _state
