from __future__ import annotations
import os, json
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Lazy import so lack of key doesn't crash at import-time
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

app = FastAPI(title="Narrator Service (LLM)")

MODEL = os.getenv("MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_client():
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)

class Payload(BaseModel):
    world: Dict[str, Any]
    cmd: Dict[str, Any]

SYSTEM = """You are the Narrator of a living, rules-driven world.
- Output STRICT JSON: {"story": string, "choices": [string, ...]}
- Choices must be short, actionable, and map to intents like:
  "inspect forest", "move forest", "talk blacksmith", "trade rare_ore with blacksmith"
- Do not invent state; rely only on provided JSON.
- Keep story to 2–5 sentences, immersive but clear.
"""

def _summarize_world(w: Dict[str, Any]) -> str:
    regions = ", ".join([r.get("id","?") for r in w.get("regions", [])])
    chars = ", ".join([c.get("id","?") for c in w.get("characters", [])])
    flags = ",".join([k for k, v in (w.get("flags", {}) or {}).items() if v])
    players = list((w.get("players", {}) or {}).keys())
    items = ", ".join([it.get("id","?") for it in w.get("items", [])])
    return (
        f"Regions:[{regions}] Characters:[{chars}] Items:[{items}] "
        f"ActiveFlags:[{flags}] Players:{players or 'none'}"
    )

@app.post("/narrate")
def narrate(p: Payload):
    client = get_client()
    if client is None:
        # Safe fallback if key missing or openai lib not installed
        w = p.world; cmd = p.cmd
        player_id = cmd.get("player_id", "p1")
        player = w.get("players", {}).get(player_id, {"loc": "town_square"})
        story = f"You stand in **{player['loc'].replace('_',' ')}**. (Set OPENAI_API_KEY for rich narration.)"
        return {
            "story": story,
            "choices": [
                "inspect forest",
                "move forest",
                "talk blacksmith",
                "trade rare_ore with blacksmith"
            ],
        }

    world_summary = _summarize_world(p.world)
    user_msg = (
        "World JSON (full):\n" + json.dumps(p.world) +
        "\n\nWorld summary:\n" + world_summary +
        "\n\nLast command:\n" + json.dumps(p.cmd) +
        "\n\nReturn STRICT JSON with keys: story, choices"
    )

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=350,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        story = data.get("story", "")
        choices: List[str] = data.get("choices", [])
        if not choices:
            choices = ["inspect forest", "move forest", "talk blacksmith", "trade rare_ore with blacksmith"]
        return {"story": story, "choices": choices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Narrator error: {e}")
