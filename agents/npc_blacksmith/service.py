from __future__ import annotations
from fastapi import FastAPI

app = FastAPI(title="NPC Blacksmith Service")

@app.get("/")
def status():
    return {"npc": "blacksmith", "status": "idle"}
