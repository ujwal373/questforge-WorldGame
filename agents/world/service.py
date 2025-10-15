from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel
from packages.metta.runner import evaluate

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
    # ensure player exists
    _state.setdefault("players", {}).setdefault(i.player_id, {"loc": "town_square", "inventory": []})
    player = _state["players"][i.player_id]
    args = i.args or {}

    # === Minimal core actions ===
    if i.intent == "move":
        dest = args.get("target") or "town_square"
        player["loc"] = dest

    elif i.intent == "inspect":
        pass  # no-op; narrator will describe based on state

    elif i.intent == "talk":
        target = args.get("target")
        if target == "blacksmith":
            for c in _state["characters"]:
                if c["id"] == "blacksmith":
                    c["mood"] = "neutral" if c["mood"] == "wary" else c["mood"]

    elif i.intent == "trade":
        # Trading is handled by rules (runner); we only pass context down
        pass

    # === Deterministic rules apply here ===
    diff = evaluate(_state, i.model_dump())
    _apply_diff(_state, diff)

    return _state


@app.post("/tick")
def tick():
    """
    Advance world time: drift danger, clear transient flags (optionally).
    """
    # drift forest danger a bit
    for r in _state["regions"]:
        if r["id"] == "forest":
            r["danger"] = max(0.0, min(1.0, r.get("danger", 0.0) + 0.03))
    return _state


# ------------------------
# Utilities
# ------------------------
def _apply_diff(state: Dict[str, Any], diff: Dict[str, Any]) -> None:
    if not diff:
        return

    # Flags
    if "flags" in diff:
        state.setdefault("flags", {})
        state["flags"].update(diff["flags"])

    # Players (partial merge)
    for pid, pd in (diff.get("players") or {}).items():
        state.setdefault("players", {}).setdefault(pid, {})
        state["players"][pid].update(pd)

    # Characters (match by id)
    if "characters" in diff:
        char_map = {c["id"]: c for c in state.get("characters", [])}
        for cid, cd in diff["characters"].items():
            if cid in char_map:
                char_map[cid].update(cd)
            else:
                # if not present, create
                state.setdefault("characters", []).append({"id": cid, **cd})
