# Touch grass project HF26
#Run Command= 
import html
import io
import json
import os
import re

import ollama
import streamlit as st
from PIL import Image

MODEL = "gemma3:4b"  # local open-weight multimodal model (Ollama)
GEMMA4_API = "gemma-4-26b-a4b-it"  # Gemma 4 through the Gemini API
BACKENDS = ["Gemma 4 (Gemini API)", "Local: Gemma 3 via Ollama"]
PLACES = ["Park", "College campus", "Garden or lawn", "Street or neighbourhood", "Lake or riverside"]

FALLBACK = [
    {"title": "Find a leaf with jagged or serrated edges", "hint": "Check low bushes and small trees."},
    {"title": "Photograph something bright red", "hint": "A flower, a berry, a sign, anything outdoors."},
    {"title": "Spot a bird, insect or butterfly", "hint": "Stand still for a minute and watch."},
    {"title": "Find the oldest-looking tree and photograph its bark", "hint": "Rough, cracked bark is a good sign."},
    {"title": "Capture the sky through tree branches", "hint": "Look straight up from under a tree."},
]

QUEST_PROMPT = """You are a cheerful outdoor guide creating a scavenger hunt.
Create exactly 5 short quests for a person visiting: <PLACE>. Difficulty: <LEVEL>.
Rules: every quest must be photographable with a phone, safe, doable within 10 minutes, and must not
involve trespassing, touching wild animals or picking plants. Mix: a leaf or plant, a colour, a texture,
tiny wildlife or a bird, and the sky or light.
Return ONLY valid JSON in exactly this format:
{"quests": [{"title": "Find a leaf with jagged edges", "hint": "Look at low bushes and small trees."}]}"""

CHECK_PROMPT = """The person was given this outdoor quest: "<QUEST>"
Look at the photo and decide whether it clearly satisfies the quest. Be fair, but do not accept
unrelated photos.
Return ONLY valid JSON in exactly this format:
{"match": true, "what_i_see": "One short sentence describing the main subject of the photo.",
"fun_fact": "One short, interesting and accurate fact about what is in the photo, or an empty string.",
"feedback": "One friendly sentence. If it does not match, say what to look for instead."}"""

JOURNAL_PROMPT = """Write a short, warm nature-journal entry (80 to 100 words) in the first person about an
outdoor walk at: <PLACE>. Mention the highlights below naturally and end with one sentence encouraging the
reader to keep their phone in their pocket and enjoy the outdoors.
Highlights:
<HIGHLIGHTS>"""


def prepare(raw):
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail((896, 896))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def call_model(prompt, backend, api_key, img_bytes=None, want_json=True):
    if backend == BACKENDS[0]:
        if not api_key:
            raise ValueError("Please enter your Gemini API key in the sidebar.")
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        contents = [prompt]
        if img_bytes:
            contents = [types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"), prompt]
        return client.models.generate_content(model=GEMMA4_API, contents=contents).text or ""
    msg = {"role": "user", "content": prompt}
    if img_bytes:
        msg["images"] = [img_bytes]
    kwargs = {"format": "json"} if want_json else {}
    reply = ollama.chat(model=MODEL, messages=[msg], options={"temperature": 0.4}, **kwargs)
    return reply["message"]["content"]


def parse_json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def yes(v):
    return v is True or str(v).strip().lower() in ("true", "yes")


def esc(v):
    return html.escape(str(v or ""))


def make_quests(place, level, backend, api_key):
    prompt = QUEST_PROMPT.replace("<PLACE>", place).replace("<LEVEL>", level)
    data = parse_json(call_model(prompt, backend, api_key))
    items = data.get("quests", []) if isinstance(data, dict) else []
    quests = [{"title": str(q["title"]), "hint": str(q.get("hint", ""))}
              for q in items if isinstance(q, dict) and q.get("title")]
    return quests[:5]


def check_photo(quest, img_bytes, backend, api_key):
    prompt = CHECK_PROMPT.replace("<QUEST>", quest["title"])
    data = parse_json(call_model(prompt, backend, api_key, img_bytes=img_bytes))
    return {
        "match": yes(data.get("match")),
        "what_i_see": str(data.get("what_i_see", "")),
        "fun_fact": str(data.get("fun_fact", "")),
        "feedback": str(data.get("feedback", "")),
    }


def write_journal(place, quests, results, backend, api_key):
    lines = []
    for i, q in enumerate(quests):
        r = results.get(i)
        if r and r["match"]:
            lines.append(f"- {q['title']}: {r['what_i_see']}")
    prompt = JOURNAL_PROMPT.replace("<PLACE>", place).replace("<HIGHLIGHTS>", "\n".join(lines))
    return call_model(prompt, backend, api_key, want_json=False).strip()


st.set_page_config(page_title="Touch Grass Quest", page_icon="🌿", layout="wide")
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #F0FDF4 0%, #FEFCE8 100%); }
.stApp, .stApp p, .stApp label, .stApp li, .stApp span, .stApp h1, .stApp h2, .stApp h3,
[data-testid="stWidgetLabel"] p { color: #111111 !important; }
header[data-testid="stHeader"] { background: transparent; }
.hero { background: linear-gradient(120deg, #16A34A, #65A30D 55%, #FACC15); padding: 26px 32px;
  border-radius: 18px; margin-bottom: 18px; box-shadow: 0 8px 22px rgba(0,0,0,0.15); }
.hero h1 { margin: 0; color: #111111 !important; font-size: 2.2rem; font-weight: 800; }
.hero p { margin: 6px 0 0 0; color: #111111 !important; font-size: 1.05rem; }
.stat { background: #FFFFFF; border-radius: 14px; padding: 14px 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.stat .l { font-size: 0.78rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
.stat .v { font-size: 1.8rem; font-weight: 800; }
.quest { border-radius: 14px; padding: 14px 20px; margin: 14px 0 6px 0; box-shadow: 0 4px 14px rgba(0,0,0,0.12); color: #111111; }
.quest .t { font-size: 1.15rem; font-weight: 800; }
.quest .h { font-size: 0.92rem; opacity: 0.85; }
.result { background: #FFFFFF; border-left: 8px solid #16A34A; border-radius: 12px; padding: 12px 18px; color: #111111; margin-bottom: 8px; }
.result.bad { border-left-color: #D93025; }
.journal { background: #FFF8CC; border-left: 10px solid #F5B301; border-radius: 16px; padding: 22px 28px;
  color: #111111; font-size: 1.05rem; line-height: 1.7; box-shadow: 0 8px 20px rgba(245,179,1,0.35); }
.stButton > button { background: #FACC15; color: #111111 !important; border: 1px solid #CA8A04;
  border-radius: 10px; font-weight: 700; padding: 0.55rem 1.4rem; }
</style>
<div class="hero">
  <h1>🌿 Touch Grass Quest</h1>
  <p>An AI-powered outdoor scavenger hunt. Get 5 quests, go outside, snap what you find, and let an open-weight Gemma model check your photos. The screen is only for the first and last minute.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("AI engine")
    backend = st.radio("Model", BACKENDS)
    api_key = ""
    if backend == BACKENDS[0]:
        api_key = st.text_input("Gemini API key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))
        st.caption("Gemma 4 is an open-weight model served through the Gemini API.")
    else:
        st.caption("Runs fully on this device through Ollama. Your photos never leave it.")

ss = st.session_state
ss.setdefault("quests", [])
ss.setdefault("results", {})
ss.setdefault("gen", 0)
ss.setdefault("place", PLACES[0])
ss.setdefault("journal", "")

done = sum(1 for r in ss.results.values() if r["match"])
total = len(ss.quests)
points = done * 10 + (20 if total and done == total else 0)

c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="stat"><div class="l">Quests completed</div><div class="v">{done} / {total}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="stat"><div class="l">Points</div><div class="v">{points}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="stat"><div class="l">AI engine</div><div class="v">{"Gemma 4" if backend == BACKENDS[0] else "Gemma 3 (local)"}</div></div>', unsafe_allow_html=True)
st.write("")

st.subheader("1. Plan your outing")
a, b, c = st.columns([1.2, 1, 1])
place = a.selectbox("Where are you going?", PLACES)
level = b.radio("Difficulty", ["Easy", "Medium", "Hard"], horizontal=True)
if c.button("Generate my 5 quests 🌱"):
    with st.spinner("Creating your quests..."):
        try:
            quests = make_quests(place, level, backend, api_key)
        except Exception as err:
            quests = []
            st.error(f"Could not reach the AI: {err}")
    if len(quests) < 3:
        st.warning("The AI did not return enough quests, so a default set is used.")
        quests = FALLBACK
    ss.quests, ss.results, ss.journal, ss.place = quests, {}, "", place
    ss.gen += 1
    st.rerun()

if ss.quests:
    st.subheader("2. Go outside and complete your quests")
    st.caption("Take the photos with your phone camera. You can upload them here from your phone or your laptop.")
    for i, q in enumerate(ss.quests):
        res = ss.results.get(i)
        bg = "#DCFCE7" if (res and res["match"]) else ("#FEE2E2" if res else "#FEF9C3")
        mark = "✅ " if (res and res["match"]) else ("❌ " if res else f"{i + 1}. ")
        st.markdown(f'<div class="quest" style="background:{bg}"><div class="t">{mark}{esc(q["title"])}</div>'
                    f'<div class="h">Hint: {esc(q["hint"])}</div></div>', unsafe_allow_html=True)
        up = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png", "webp"], key=f"up_{ss.gen}_{i}")
        if up is not None and st.button("Check my photo 🔍", key=f"chk_{ss.gen}_{i}"):
            with st.spinner("Gemma is looking at your photo..."):
                try:
                    ss.results[i] = check_photo(q, prepare(up.getvalue()), backend, api_key)
                    st.rerun()
                except Exception as err:
                    st.error(f"Something went wrong: {err}")
        if res:
            cls = "result" if res["match"] else "result bad"
            fact = f"<br><b>Fun fact:</b> {esc(res['fun_fact'])}" if res["fun_fact"] else ""
            st.markdown(f'<div class="{cls}"><b>{esc(res["feedback"])}</b><br>I see: {esc(res["what_i_see"])}{fact}</div>',
                        unsafe_allow_html=True)

    st.subheader("3. Your nature journal")
    if done and st.button("Write my nature journal 📓"):
        with st.spinner("Writing your journal entry..."):
            try:
                ss.journal = write_journal(ss.place, ss.quests, ss.results, backend, api_key)
            except Exception as err:
                st.error(f"Something went wrong: {err}")
    if ss.journal:
        st.markdown(f'<div class="journal">{esc(ss.journal).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        st.success(f"You earned {points} points. Now put the phone away and enjoy the outdoors. 🌿")
else:
    st.info("Pick a place and generate your quests to begin.")
    
    
    
    