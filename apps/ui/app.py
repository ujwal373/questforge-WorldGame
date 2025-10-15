import os, json, requests, streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="QuestForge", layout="centered")
st.title("🗺️ QuestForge — AI World")

# --- helpers -----------------------------------------------------------------
def call_command(player_id: str, intent: str, args: dict | None = None):
    payload = {"player_id": player_id, "intent": intent, "args": args or {}}
    r = requests.post(f"{API_URL}/play/command", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def get_world():
    r = requests.get(f"{API_URL}/world", timeout=15)
    r.raise_for_status()
    return r.json()

def parse_choice_to_intent(choice: str):
    # choices are like: "inspect forest", "move forest", "talk blacksmith", "trade rare_ore with blacksmith"
    parts = choice.split()
    verb = parts[0]
    args = {}
    if verb in ("inspect","move","talk") and len(parts) > 1:
        args = {"target": " ".join(parts[1:])}
    elif verb == "trade" and "with" in parts:
        item = parts[1]
        target = parts[-1]
        args = {"target": target, "item": item}
    return verb, args

# --- state -------------------------------------------------------------------
if "player_id" not in st.session_state:
    st.session_state.player_id = "p1"
if "log" not in st.session_state:
    st.session_state.log = []
if "choices" not in st.session_state:
    st.session_state.choices = ["inspect forest", "move forest", "talk blacksmith", "trade rare_ore with blacksmith"]

# --- sidebar: world snapshot --------------------------------------------------
with st.sidebar:
    st.header("🌍 World")
    try:
        w = get_world()
        # show quick facts
        players = w.get("players", {})
        me = players.get(st.session_state.player_id, {"loc":"town_square","inventory":[]})
        st.markdown(f"**You are in:** `{me.get('loc','?')}`")
        st.markdown(f"**Inventory:** `{', '.join(me.get('inventory',[])) or 'empty'}`")
        st.markdown("**Flags:** " + ", ".join([k for k,v in (w.get('flags') or {}).items() if v]) or "none")
        st.markdown("**Regions:** " + ", ".join([r['id'] for r in w.get('regions',[])]))
    except Exception as e:
        st.warning(f"World not reachable: {e}")

# --- main: input form ---------------------------------------------------------
st.subheader("Type a command")
with st.form("action"):
    col1, col2 = st.columns([3, 1])
    cmd_text = col1.text_input("e.g., `inspect forest`, `move forest`, `talk blacksmith`, `trade rare_ore with blacksmith`", "")
    st.session_state.player_id = col2.text_input("Player ID", st.session_state.player_id)
    submitted = st.form_submit_button("Send")

    if submitted and cmd_text.strip():
        verb, args = parse_choice_to_intent(cmd_text.strip())
        try:
            data = call_command(st.session_state.player_id, verb, args)
            st.session_state.log.append(data["story"])
            st.session_state.choices = data.get("choices", st.session_state.choices)
        except Exception as e:
            st.error(f"Command failed: {e}")

# --- suggested choices as buttons --------------------------------------------
st.subheader("Suggested choices")
cols = st.columns(2)
for idx, c in enumerate(st.session_state.choices):
    if cols[idx % 2].button(c):
        verb, args = parse_choice_to_intent(c)
        try:
            data = call_command(st.session_state.player_id, verb, args)
            st.session_state.log.append(data["story"])
            st.session_state.choices = data.get("choices", st.session_state.choices)
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Command failed: {e}")

# --- story log ----------------------------------------------------------------
st.subheader("Story")
if st.session_state.log:
    for s in st.session_state.log[-10:]:
        st.markdown(s)
else:
    st.info("No story yet. Try a command or click a suggested choice.")
