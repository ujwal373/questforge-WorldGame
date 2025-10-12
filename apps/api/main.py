from __future__ import annotations
import os
import httpx
from fastapi import FastAPI
from apps.api.utils import Command, WorldResponse

# Robust: fallback if var is unset OR empty
WORLD_URL = os.getenv("WORLD_URL") or "http://world:8010"
NARRATOR_URL = os.getenv("NARRATOR_URL") or "http://narrator:8020"
EVENTMASTER_URL = os.getenv("EVENTMASTER_URL") or "http://eventmaster:8030"
NPC_BLACKSMITH_URL = os.getenv("NPC_BLACKSMITH_URL") or "http://npc_blacksmith:8040"

app = FastAPI(title="QuestForge API")

@app.get("/world")
async def get_world():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{WORLD_URL}/state")
        return r.json()

@app.post("/play/command", response_model=WorldResponse)
async def play(cmd: Command):
    async with httpx.AsyncClient() as client:
        w = await client.post(f"{WORLD_URL}/intent", json=cmd.model_dump())
        world = w.json()
        e = await client.post(f"{EVENTMASTER_URL}/maybe", json={"world": world})
        if e.json().get("changed"):
            world = (await client.get(f"{WORLD_URL}/state")).json()
        n = await client.post(f"{NARRATOR_URL}/narrate",
                              json={"world": world, "cmd": cmd.model_dump()})
        nj = n.json()
        story = nj["story"]
        choices = nj.get("choices", ["inspect forest","talk blacksmith","move town_square"])
    return WorldResponse(story=story, world=world, choices=choices)
