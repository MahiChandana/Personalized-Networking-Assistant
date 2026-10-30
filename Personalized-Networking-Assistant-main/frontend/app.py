import streamlit as st
import httpx

# FastAPI backend entry point
BACKEND_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="Personalized Networking Assistant", layout="wide", page_icon="💼")

# ----------------------------------------------------------------------------
# THEME
# Palette: navy (structure/headings), warm gold (primary accent),
# coral (secondary accent / feedback), soft slate background.
# Type: Fraunces (display) + Inter (body/UI) + JetBrains Mono (labels/tags).
# ----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --navy: #1B2A4A;
    --navy-soft: #2E3F63;
    --gold: #D9A441;
    --coral: #EE6C4D;
    --bg: #F3F5F8;
    --slate: #5C6B7A;
    --card-bg: #FFFFFF;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: var(--bg);
}

.block-container {
    max-width: 1100px;
    margin: 0 auto;
    padding-top: 1.5rem;
}

/* Hide default Streamlit chrome bits that clutter the centered layout */
#MainMenu, footer {visibility: hidden;}

/* ---------- HERO ---------- */
.hero-wrap {
    text-align: center;
    padding: 2.5rem 0 1rem 0;
}
.hero-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--gold);
    background: rgba(217, 164, 65, 0.12);
    border: 1px solid rgba(217, 164, 65, 0.35);
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Fraunces', serif;
    font-weight: 700;
    font-size: 4.2rem;
    line-height: 1.1;
    margin: 0;
    background: linear-gradient(100deg, var(--navy) 0%, var(--gold) 55%, var(--coral) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.01em;
}
.hero-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--navy-soft);
    max-width: 620px;
    width: 100%;
    margin: 1.1rem auto 0 auto;
    text-align: center;
    line-height: 1.6;
    display: block;
}
.hero-subtitle .accent {
    color: var(--coral);
    font-weight: 600;
}

/* ---------- FORM CARD ---------- */
.form-card-marker { display: none; }
div[data-testid="stForm"] {
    background: var(--card-bg);
    border-radius: 16px;
    padding: 2rem 2.25rem 1.25rem 2.25rem;
    border-top: 4px solid var(--gold);
    box-shadow: 0 8px 24px rgba(27, 42, 74, 0.07);
}

label[data-testid="stWidgetLabel"] p {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--navy-soft);
}

/* Primary button — gold */
.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
    background: var(--gold);
    color: var(--navy);
    border: none;
    border-radius: 10px;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button[kind="primary"]:hover, div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 14px rgba(217, 164, 65, 0.35);
    color: var(--navy);
}

/* ---------- SECTION HEADERS ---------- */
.section-heading {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 1.5rem;
    color: var(--navy);
    margin: 2.5rem 0 0.25rem 0;
    text-align: center;
}
.section-subheading {
    text-align: center;
    color: var(--slate);
    font-size: 0.92rem;
    margin-bottom: 1.5rem;
}

/* ---------- THEME TAGS ---------- */
.theme-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--navy);
    background: rgba(27, 42, 74, 0.06);
    border: 1px solid rgba(27, 42, 74, 0.15);
    padding: 0.2rem 0.65rem;
    border-radius: 6px;
    margin: 0 0.25rem 0.4rem 0;
}

/* ---------- CONVERSATION CARD (signature element) ---------- */
.convo-card {
    position: relative;
    background: var(--card-bg);
    border-radius: 12px;
    padding: 1.1rem 1.4rem 1.1rem 1.6rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 4px 14px rgba(27, 42, 74, 0.06);
    border-left: 5px solid var(--gold);
}
.convo-card:nth-of-type(2n) { border-left-color: var(--coral); }
.convo-card:nth-of-type(3n) { border-left-color: var(--navy-soft); }
.convo-text {
    font-size: 1.02rem;
    color: var(--navy);
    line-height: 1.5;
}
.convo-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--slate);
    margin-bottom: 0.3rem;
}

/* Feedback badge in history */
.fb-yes { color: #2E7D32; font-weight: 600; }
.fb-no { color: var(--coral); font-weight: 600; }
.fb-none { color: var(--slate); }

hr { border-color: rgba(27, 42, 74, 0.08); }
</style>
""", unsafe_allow_html=True)

# Persistent Session State management initialization
if "starters" not in st.session_state:
    st.session_state.starters = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "themes" not in st.session_state:
    st.session_state.themes = []

# ----------------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------------
st.markdown("""
<div class="hero-wrap">
    <h1 class="hero-title">Personalized Networking Assistant</h1>
    <p class="hero-subtitle">Generate smart conversation prompts and perform instant contextual validations — so you always know <span class="accent">how to start the conversation.</span></p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🚀 Starter Engine", "🔍 Fact Verification", "📜 Past Strategies"])

# --- TAB 1: GENERATION ENGINE ---
with tab1:
    # Centered form using a 3-column layout, form lives in the middle column
    left_pad, center, right_pad = st.columns([1, 2, 1])

    with center:
        with st.form("generate_form"):
            user_bio = st.text_area(
                "Your Professional Bio / Interests",
                placeholder="Software Engineer interested in urban planning and climate change mitigation.",
                height=110
            )
            event_desc = st.text_area(
                "Event Description",
                placeholder="AI for Sustainable Cities Panel Discussion and Networking mixer.",
                height=110
            )
            submitted = st.form_submit_button("Generate Starters", type="primary", use_container_width=True)

        if submitted:
            if not user_bio or not event_desc:
                st.warning("Please complete both parameters to proceed.")
            else:
                with st.spinner("Analyzing themes and crafting prompts..."):
                    try:
                        st.session_state.starters = []
                        st.session_state.themes = []
                        st.session_state.session_id = None

                        payload = {"bio": user_bio, "event_description": event_desc}
                        res = httpx.post(f"{BACKEND_URL}/generate", json=payload, timeout=45.0)

                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.starters = data.get("starters", [])
                            st.session_state.session_id = data.get("session_id", None)
                            st.session_state.themes = data.get("themes", [])
                            st.toast("Blueprints generated successfully!")
                        else:
                            st.error(f"Failed to interface with backend engine pipeline. Status: {res.status_code}")
                    except Exception as e:
                        st.error(f"Connection Error during generation: {e}")

    # ---- Generated Strategies: full width, below the form ----
    if st.session_state.starters:
        st.markdown('<div class="section-heading">Generated Strategies</div>', unsafe_allow_html=True)

        if st.session_state.themes:
            tags_html = "".join([f'<span class="theme-tag">{t}</span>' for t in st.session_state.themes])
            st.markdown(f'<div style="text-align:center; margin-bottom:1.5rem;">{tags_html}</div>', unsafe_allow_html=True)

        card_left, card_center, card_right = st.columns([1, 2, 1])
        with card_center:
            for idx, starter in enumerate(st.session_state.starters):
                st.markdown(f"""
                <div class="convo-card">
                    <div class="convo-label">Starter {idx + 1}</div>
                    <div class="convo-text">{starter}</div>
                </div>
                """, unsafe_allow_html=True)

                fb_col1, fb_col2, _ = st.columns([0.15, 0.15, 0.7])
                if fb_col1.button("👍", key=f"up_{idx}"):
                    try:
                        httpx.post(f"{BACKEND_URL}/feedback", json={
                            "session_id": st.session_state.session_id,
                            "starter": starter,
                            "feedback": "useful"
                        })
                        st.toast("Feedback registered!")
                    except Exception:
                        st.toast("Could not save feedback metrics.")

                if fb_col2.button("👎", key=f"down_{idx}"):
                    try:
                        httpx.post(f"{BACKEND_URL}/feedback", json={
                            "session_id": st.session_state.session_id,
                            "starter": starter,
                            "feedback": "not useful"
                        })
                        st.toast("Feedback registered!")
                    except Exception:
                        st.toast("Could not save feedback metrics.")
    else:
        st.markdown(
            '<p style="text-align:center; color:#5C6B7A; margin-top:2rem;">Fill out your profiles above to review custom conversational blueprints.</p>',
            unsafe_allow_html=True
        )

# --- TAB 2: QUICK FACT CHECK ---
with tab2:
    left_pad, center, right_pad = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="section-heading">Contextual Fact Search System</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="section-subheading">Cross-examine a concept or trend before you bring it up in conversation.</p>',
            unsafe_allow_html=True
        )

        with st.form("verify_form"):
            query = st.text_input(
                "Topic to verify",
                placeholder="e.g., Blockchain in healthcare"
            )
            verify_submitted = st.form_submit_button("Run Fact Verification", type="primary", use_container_width=True)

        if verify_submitted:
            if query:
                with st.spinner("Querying reliable sources..."):
                    try:
                        res = httpx.post(f"{BACKEND_URL}/verify", json={"query": query})
                        if res.status_code == 200:
                            result = res.json()
                            if result.get("status") == "Verified":
                                st.markdown(f"""
                                <div class="convo-card">
                                    <div class="convo-label">{result.get('title')}</div>
                                    <div class="convo-text">{result.get('summary')}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.caption(f"[View Wikipedia Reference]({result.get('url')})")
                            else:
                                st.error(result.get("summary", "Verification failed."))
                        else:
                            st.error(f"Backend validation failed with status code: {res.status_code}")
                    except Exception as e:
                        st.error(f"Verification pipeline connection error: {e}")
            else:
                st.warning("Please enter a topic to verify.")

# --- TAB 3: STRATEGY LOGS & HISTORY ---
with tab3:
    left_pad, center, right_pad = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="section-heading">Historical Log Tracker</div>', unsafe_allow_html=True)
        if st.button("Refresh Log Repositories", use_container_width=True):
            st.rerun()

        try:
            res = httpx.get(f"{BACKEND_URL}/history")
            if res.status_code == 200:
                history_records = res.json()

                if history_records:
                    for item in reversed(history_records):
                        event_title = item.get('event') or item.get('event_description') or "Unknown Event"
                        timestamp = item.get('timestamp', '2026-01-01')[:10]

                        with st.expander(f"📅 Event: {event_title[:60]}... ({timestamp})"):
                            st.markdown(f"**Your Profile Bio:** {item.get('bio', 'N/A')}")
                            themes = item.get('themes', [])
                            if themes:
                                tags_html = "".join([f'<span class="theme-tag">{t}</span>' for t in themes])
                                st.markdown(tags_html, unsafe_allow_html=True)
                            st.markdown("**Suggested Starters Given:**")

                            starters_with_feedback = item.get('starters_with_feedback')
                            if starters_with_feedback:
                                for entry in starters_with_feedback:
                                    fb = entry.get("feedback")
                                    if fb == "useful":
                                        badge_html = '<span class="fb-yes">👍 useful</span>'
                                    elif fb == "not useful":
                                        badge_html = '<span class="fb-no">👎 not useful</span>'
                                    else:
                                        badge_html = '<span class="fb-none">— not rated</span>'
                                    st.markdown(f"- {entry.get('text')}  {badge_html}", unsafe_allow_html=True)
                            else:
                                for s in item.get('starters', []):
                                    st.write(f"- {s}")
                else:
                    st.info("No entries saved yet. Generate starter configurations to update local tracking history.")
            else:
                st.error(f"Could not load log data. Backend status code: {res.status_code}")
        except Exception as e:
            st.error(f"Could not reach database history tracker: {e}")