"""
app.py — Main Streamlit Application for the FAQ Chatbot

This is the entry point of the application. Run with:
    streamlit run app.py
"""

import time
import streamlit as st
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "query_count" not in st.session_state:
    st.session_state["query_count"] = 0

if "history" not in st.session_state:
    st.session_state["history"] = []

if "last_query" not in st.session_state:
    st.session_state["last_query"] = ""

if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0.25
    
from datetime import datetime

from src.config import CONFIDENCE_THRESHOLD, FAQ_DATA_PATH
from src.data_loader import load_faq_data
from src.matching_engine import FAQMatchingEngine
from src.logger import setup_logger


# ---------------------------------------------------------------------------
# Logger Setup
# ---------------------------------------------------------------------------
logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# Page Configuration
# Must be the FIRST Streamlit command called in the script.
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FAQ Chatbot | AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Modern, Dark Glassmorphism UI
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Reset & Font */
    * { font-family: 'Inter', sans-serif; }

    /* Dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    /* Hide default Streamlit header/footer */
    #MainMenu, footer, header { visibility: hidden; }

    /* Main content block */
    .block-container {
        padding: 2rem 2rem 2rem 2rem !important;
        max-width: 900px;
    }

    /* ---- Hero Header ---- */
    .hero-header {
        text-align: center;
        padding: 2rem 1rem 1rem 1rem;
        margin-bottom: 1rem;
    }
    .hero-header h1 {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .hero-header p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.5rem;
    }

    /* ---- Chat Messages ---- */
    .chat-wrapper {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem 0;
    }

    /* User message bubble */
    .user-msg {
        display: flex;
        justify-content: flex-end;
        animation: slideInRight 0.3s ease;
    }
    .user-bubble {
        background: linear-gradient(135deg, #6d28d9, #4f46e5);
        color: #fff;
        padding: 0.85rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        font-size: 0.95rem;
        line-height: 1.5;
        box-shadow: 0 4px 15px rgba(109, 40, 217, 0.4);
    }

    /* Bot message bubble */
    .bot-msg {
        display: flex;
        justify-content: flex-start;
        animation: slideInLeft 0.3s ease;
    }
    .bot-bubble {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #e2e8f0;
        padding: 0.85rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        max-width: 75%;
        font-size: 0.95rem;
        line-height: 1.6;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    /* Timestamp */
    .msg-time {
        font-size: 0.7rem;
        color: #64748b;
        margin-top: 4px;
        text-align: right;
    }

    /* ---- Confidence Badge ---- */
    .conf-badge {
        display: inline-block;
        margin-top: 0.5rem;
        padding: 2px 10px;
        border-radius: 99px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    .conf-high   { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid #34d399; }
    .conf-medium { background: rgba(251,191,36,0.15);  color: #fbbf24; border: 1px solid #fbbf24; }
    .conf-low    { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid #f87171; }

    /* ---- Matched Question Tag ---- */
    .matched-q {
        font-size: 0.75rem;
        color: #a78bfa;
        margin-top: 0.4rem;
        font-style: italic;
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] * { color: #cbd5e1 !important; }

    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #a78bfa !important;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 0.5rem;
    }

    .history-item {
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.4rem;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        font-size: 0.82rem;
        border-left: 3px solid #6d28d9;
        color: #94a3b8 !important;
        word-break: break-word;
    }

    /* ---- Stats Cards ---- */
    .stat-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 2px;
    }

    /* ---- Input Area ---- */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(167,139,250,0.4) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 0 3px rgba(167,139,250,0.2) !important;
    }
    .stTextInput > div > div > input::placeholder { color: #64748b !important; }

    /* ---- Buttons ---- */
    .stButton > button {
        background: linear-gradient(135deg, #6d28d9, #4f46e5) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(109,40,217,0.5) !important;
    }

    /* ---- Divider ---- */
    hr { border-color: rgba(255,255,255,0.08) !important; }

    /* ---- Animations ---- */
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to   { opacity: 1; transform: translateX(0); }
    }

    /* ---- Typing indicator ---- */
    .typing-indicator {
        display: flex;
        gap: 5px;
        padding: 10px 16px;
        background: rgba(255,255,255,0.07);
        border-radius: 18px;
        width: fit-content;
    }
    .dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #a78bfa;
        animation: bounce 1.2s infinite ease-in-out;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
        40%            { transform: scale(1.1); opacity: 1;   }
    }

    /* Scrollable chat area */
    .chat-scroll { max-height: 62vh; overflow-y: auto; padding-right: 4px; }

    /* Suggestion chips */
    .chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 1rem; }
    .chip {
        background: rgba(167,139,250,0.12);
        border: 1px solid rgba(167,139,250,0.3);
        color: #a78bfa;
        padding: 5px 14px;
        border-radius: 99px;
        font-size: 0.8rem;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached Resource Loading
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_engine() -> FAQMatchingEngine:
    """
    Loads the FAQ data and fits the matching engine.

    @st.cache_resource ensures this expensive operation runs ONLY ONCE per
    Streamlit session and is cached across reruns, making the app fast.

    Returns:
        FAQMatchingEngine: A fitted engine ready for query processing.
    """
    logger.info("Initializing FAQ Matching Engine (first load)...")
    faq_df = load_faq_data()
    engine = FAQMatchingEngine()
    engine.fit(faq_df)
    return engine


def get_confidence_badge(score: float) -> str:
    """Returns an HTML confidence badge based on the score value."""
    if score >= 0.70:
        return f'<span class="conf-badge conf-high">✓ High Confidence: {score:.0%}</span>'
    elif score >= CONFIDENCE_THRESHOLD:
        return f'<span class="conf-badge conf-medium">~ Medium Confidence: {score:.0%}</span>'
    else:
        return f'<span class="conf-badge conf-low">✗ Low Confidence: {score:.0%}</span>'


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
def init_session_state():
    """
    Initializes Streamlit session state variables.
    Session state persists data across reruns triggered by user interaction.
    """
    if "messages" not in st.session_state:
        # Start with a welcome message from the bot
        st.session_state.messages = [
            {
                "role": "bot",
                "content": "👋 Hello! I'm your AI FAQ assistant. Ask me anything — I'll find the best answer from our knowledge base!",
                "confidence": None,
                "matched_q": None,
                "time": datetime.now().strftime("%H:%M"),
            }
        ]
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    if "answered_count" not in st.session_state:
        st.session_state.answered_count = 0
    if "active_threshold" not in st.session_state:
        st.session_state.active_threshold = float(CONFIDENCE_THRESHOLD)


def render_message(msg: dict):
    """Renders a single chat message bubble (user or bot) as HTML."""
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="user-msg">
            <div>
                <div class="user-bubble">{msg['content']}</div>
                <div class="msg-time">{msg.get('time', '')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        badge = get_confidence_badge(msg["confidence"]) if msg["confidence"] is not None else ""
        matched = f'<div class="matched-q">📌 Matched: {msg["matched_q"]}</div>' if msg.get("matched_q") else ""
        st.markdown(f"""
        <div class="bot-msg">
            <div>
                <div class="bot-bubble">
                    {msg['content']}
                    {badge}
                    {matched}
                </div>
                <div class="msg-time">{msg.get('time', '')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add Feedback Buttons for Bot Messages (Hackathon feature)
        if msg.get("role") == "bot" and msg.get("confidence") is not None:
            # We use columns to put small feedback buttons
            col1, col2, col3 = st.columns([0.1, 0.1, 0.8])
            msg_id = msg.get("time", "") + str(hash(msg['content']))
            with col1:
                if st.button("👍", key=f"up_{msg_id}", help="Good response"):
                    st.success("Thanks for your feedback!")
            with col2:
                if st.button("👎", key=f"down_{msg_id}", help="Bad response"):
                    st.errorfaq_chatbot("We'll improve our answers. Thanks!")


def process_query(engine: FAQMatchingEngine, user_input: str):
    """
    Processes the user's query through the matching engine and updates chat state.

    Args:
        engine (FAQMatchingEngine): The fitted matching engine instance.
        user_input (str): Raw text typed by the user.
    """
    user_input = user_input.strip()
    if not user_input:
        return

    now = datetime.now().strftime("%H:%M")

    # Append the user's message to the history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "confidence": None,
        "matched_q": None,
        "time": now,
    })
    st.session_state.query_count += 1

    # Query the matching engine
    try:
        matched_q, answer, confidence = engine.get_response(
            user_input, 
            threshold=st.session_state.active_threshold
        )
        if confidence >= st.session_state.active_threshold:
            st.session_state.answered_count += 1

        # Append the bot's response to the history
        st.session_state.messages.append({
            "role": "bot",
            "content": answer,
            "confidence": confidence,
            "matched_q": matched_q if confidence >= st.session_state.active_threshold else None,
            "time": now,
        })
        logger.info(f"Responded to: '{user_input}' | Conf: {confidence:.4f}")

    except Exception as e:
        logger.error(f"Error processing query '{user_input}': {e}")
        st.session_state.messages.append({
            "role": "bot",
            "content": "⚠️ An unexpected error occurred while processing your query. Please try again.",
            "confidence": 0.0,
            "matched_q": None,
            "time": now,
        })


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
def render_sidebar(engine: FAQMatchingEngine):
    """Renders the sidebar with stats, query history, and quick actions."""
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🤖 FAQ Chatbot</div>', unsafe_allow_html=True)
        st.markdown("Powered by **TF-IDF** + **Cosine Similarity**")
        st.divider()

        # --- Stats Cards ---
        total = st.session_state.query_count
        answered = st.session_state.answered_count
        rate = f"{(answered/total*100):.0f}%" if total > 0 else "—"

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">Queries</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{rate}</div>
                <div class="stat-label">Answer Rate</div>
            </div>""", unsafe_allow_html=True)

        st.divider()

        # --- Query History ---
        st.markdown('<div class="sidebar-title">📋 Query History</div>', unsafe_allow_html=True)
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        if user_msgs:
            for msg in reversed(user_msgs[-10:]):
                st.markdown(
                    f'<div class="history-item">🗨 {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown('<span style="color:#4b5563;font-size:0.85rem">No queries yet.</span>', unsafe_allow_html=True)

        st.divider()

        # --- Settings Panel ---
        st.markdown('<div class="sidebar-title">⚙️ Settings</div>', unsafe_allow_html=True)
        new_threshold = st.slider(
            "Confidence Threshold", 
            min_value=0.0, max_value=1.0, 
            value=st.session_state.active_threshold, 
            step=0.05,
            help="Higher values require stricter matches. Lower values may allow fuzzy matches to pass."
        )
        if new_threshold != st.session_state.active_threshold:
            st.session_state.active_threshold = new_threshold
            st.experimental_rerun()

        # --- Dataset Info ---
        st.markdown('<div class="sidebar-title">📚 Knowledge Base</div>', unsafe_allow_html=True)
        faq_count = len(engine.faq_df) if engine.faq_df is not None else 0
        st.markdown(f'<span style="color:#64748b;font-size:0.85rem">{faq_count} FAQ entries loaded</span>', unsafe_allow_html=True)
        st.markdown(f'<span style="color:#64748b;font-size:0.85rem">Active Threshold: {st.session_state.active_threshold:.0%}</span>', unsafe_allow_html=True)

        st.divider()

        # --- Clear Chat Button ---
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [st.session_state.messages[0]]  # Keep welcome msg
            st.session_state.query_count = 0
            st.session_state.answered_count = 0
            st.experimental_rerun()


# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------
def main():
    """Main function that assembles and renders the entire Streamlit application."""
    init_session_state()

    # Load engine (cached — only runs once)
    with st.spinner("🔄 Loading AI engine..."):
        engine = load_engine()

    # ---- Hero Header ----
    st.markdown("""
    <div class="hero-header">
        <h1>🤖 FAQ AI Assistant</h1>
        <p>Instant answers powered by Natural Language Processing</p>
    </div>
    """, unsafe_allow_html=True)

    # ---- Sidebar ----
    render_sidebar(engine)

    # ---- Chat Message History ----
    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        render_message(msg)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ---- Suggestion Chips ----
    st.markdown("**💡 Try asking:**", unsafe_allow_html=True)
    suggestions = [
        "What is your return policy?",
        "How do I track my order?",
        "What payment methods do you accept?",
        "How do I reset my password?",
        "Do you ship internationally?",
    ]
    cols = st.columns(len(suggestions))
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, key=f"chip_{i}", use_container_width=True):
                process_query(engine, suggestion)
                st.experimental_rerun()

    st.markdown("---")

    # ---- Chat Input ----
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                label="Your question",
                placeholder="Type your question here and press Send...",
                label_visibility="collapsed",
                key="user_input_field",
            )
        with col2:
            submitted = st.form_submit_button("Send 🚀", use_container_width=True)

    if submitted and user_input:
        process_query(engine, user_input)
        st.experimental_rerun()


if __name__ == "__main__":
    main()
