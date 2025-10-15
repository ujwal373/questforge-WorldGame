from __future__ import annotations
from typing import Dict, Any

"""
Minimal rule evaluator (MeTTa-inspired) that returns a DIFF you can
apply to the world state. We keep rules in Python for now for speed.
"""

def evaluate(world: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inspect current world + last intent and return a partial DIFF:

    Example DIFF:
    {
      "flags": {"bandits": True},
      "players": {"p1": {"inventory": ["sword"]}},
      "characters": {
         "blacksmith": {"needs": [], "trust": {"p1": 0.2}}
      }
    }
    """
    diff: Dict[str, Any] = {}

    _rule_spawn_bandits(world, diff)
    _rule_trade_weapon(world, intent, diff)

    return diff


def _rule_spawn_bandits(world: Dict[str, Any], diff: Dict[str, Any]) -> None:
    # (and (> (danger forest) 0.7) (not festival_active)) -> (spawn bandits)
    forest = next((r for r in world.get("regions", []) if r.get("id") == "forest"), None)
    festival = bool(world.get("flags", {}).get("festival_active", False))
    if forest and forest.get("danger", 0.0) > 0.7 and not festival:
        diff.setdefault("flags", {})["bandits"] = True


def _rule_trade_weapon(world: Dict[str, Any], intent: Dict[str, Any], diff: Dict[str, Any]) -> None:
    # (:rule trade-weapon
    #   (and (has player rare_ore) (needs blacksmith ore))
    #   (do (give blacksmith player sword)
    #       (set (needs blacksmith ore) false)
    #       (inc (trust blacksmith player) 0.2)))

    if intent.get("intent") != "trade":
        return
    args = intent.get("args") or {}
    if not (args.get("target") == "blacksmith" and args.get("item") == "rare_ore"):
        return

    player_id = intent.get("player_id", "p1")
    player = world.get("players", {}).get(player_id, {"inventory": []})
    inv = list(player.get("inventory", []))

    # Does blacksmith still need ore?
    blacksmith = next((c for c in world.get("characters", []) if c.get("id") == "blacksmith"), None)
    needs_ore = False
    if blacksmith:
        needs_ore = "ore" in (blacksmith.get("needs") or [])

    # Demo affordance: if player doesn't have the ore, allow picking it once
    if "rare_ore" not in inv:
        inv.append("rare_ore")

    if needs_ore and "rare_ore" in inv:
        # Remove ore, grant sword, increase trust, clear need
        inv.remove("rare_ore")
        if "sword" not in inv:  # avoid duplicates on retries
            inv.append("sword")

        # write DIFF
        diff.setdefault("players", {}).setdefault(player_id, {})["inventory"] = inv

        # blacksmith updates
        cdiff = diff.setdefault("characters", {}).setdefault("blacksmith", {})
        # clear ore need
        cdiff["needs"] = [n for n in (blacksmith.get("needs") or []) if n != "ore"]

        # trust +0.2
        trust = dict(blacksmith.get("trust") or {})
        trust[player_id] = round(trust.get(player_id, 0.0) + 0.2, 2)
        cdiff["trust"] = trust
