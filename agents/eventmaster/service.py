from __future__ import annotations
from typing import Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="EventMaster Service")

class World(BaseModel):
    world: Dict[str, Any]

@app.post("/maybe")
def maybe_fire(w: World):
    changed = False
    world = w.world
    forest = next((r for r in world["regions"] if r["id"] == "forest"), None)
    if forest and forest["danger"] > 0.7 and not world["flags"].get("festival_active", False):
        world["flags"]["bandits"] = True
        changed = True
    return {"changed": changed}
