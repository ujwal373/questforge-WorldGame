from __future__ import annotations
from typing import Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Narrator Service")

class Payload(BaseModel):
    world: Dict[str, Any]
    cmd: Dict[str, Any]

@app.post("/narrate")
def narrate(p: Payload):
    w = p.world
    cmd = p.cmd
    player_id = cmd.get("player_id", "p1")
    player = w.get("players", {}).get(player_id, {"loc": "town_square", "inventory": []})

    loc = player["loc"]
    forest = next((r for r in w["regions"] if r["id"] == "forest"), None)
    blacksmith = next((c for c in w["characters"] if c["id"] == "blacksmith"), None)

    lines = []
    lines.append(f"You stand in **{loc.replace('_',' ')}**. The air hums with quiet intent.")
    if loc == "forest" and forest:
        lines.append(f"The forest feels watchful. Danger level: {forest['danger']:.2f}.")
    if blacksmith:
        mood = blacksmith.get("mood", "wary")
        needs = ', '.join(blacksmith.get("needs", [])) or 'none'
        lines.append(f"Blacksmith is {mood}; needs: {needs}.")
    if w.get("flags", {}).get("bandits"):
        lines.append("⚠️ Rumors of bandits spread through the trees.")

    story = "\n".join(lines)
    choices = [
        "inspect forest",
        "move forest",
        "talk blacksmith",
        "trade rare_ore with blacksmith"
    ]
    return {"story": story, "choices": choices}
