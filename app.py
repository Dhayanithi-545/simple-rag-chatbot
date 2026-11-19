import html
import os
import time
from datetime import datetime
import streamlit as st
from pypdf import PdfReader
from rag_backend import process_pdf, ask_question

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DocuMind Studio · AI Document Intelligence",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Vector Brand Logos (Bespoke Geometric SVG Emblem)
# -----------------------------------------------------------------------------
LOGO_SVG_SIDEBAR = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M6 3.5C6 2.67157 6.67157 2 7.5 2H14.1716C14.5694 2 14.9509 2.15804 15.2322 2.43934L19.5607 6.76777C19.842 7.04907 20 7.4306 20 7.82843V20.5C20 21.3284 19.3284 22 18.5 22H7.5C6.67157 22 6 21.3284 6 20.5V3.5Z" stroke="white" stroke-width="1.8" stroke-linejoin="round"/>
  <path d="M14 2V6.5C14 7.32843 14.6716 8 15.5 8H20" stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M13 11L13.95 13.55L16.5 14.5L13.95 15.45L13 18L12.05 15.45L9.5 14.5L12.05 13.55L13 11Z" fill="white"/>
</svg>
"""

LOGO_SVG_HERO = """
<svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M6 3.5C6 2.67157 6.67157 2 7.5 2H14.1716C14.5694 2 14.9509 2.15804 15.2322 2.43934L19.5607 6.76777C19.842 7.04907 20 7.4306 20 7.82843V20.5C20 21.3284 19.3284 22 18.5 22H7.5C6.67157 22 6 21.3284 6 20.5V3.5Z" stroke="white" stroke-width="1.7" stroke-linejoin="round"/>
  <path d="M14 2V6.5C14 7.32843 14.6716 8 15.5 8H20" stroke="white" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M13 10.5L14.15 13.35L17 14.5L14.15 15.65L13 18.5L11.85 15.65L9 14.5L11.85 13.35L13 10.5Z" fill="white"/>
</svg>
"""

LOGO_SVG_BADGE = """
<svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="dmGrad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
      <stop stop-color="#4F46E5"/>
      <stop offset="0.5" stop-color="#7C3AED"/>
      <stop offset="1" stop-color="#06B6D4"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="20" height="20" rx="6" fill="url(#dmGrad)"/>
  <path d="M12 6.5L13.35 10.15L17 11.5L13.35 12.85L12 16.5L10.65 12.85L7 11.5L10.65 10.15L12 6.5Z" fill="white"/>
</svg>
"""

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "Light"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "indexed_docs" not in st.session_state:
    st.session_state.indexed_docs = {}
    if os.path.exists("data"):
        for fname in sorted(os.listdir("data")):
            if fname.lower().endswith(".pdf"):
                fpath = os.path.join("data", fname)
                try:
                    pages = len(PdfReader(fpath).pages)
                except Exception:
                    pages = "?"
                size_kb = round(os.path.getsize(fpath) / 1024, 1)
                st.session_state.indexed_docs[fname] = {
                    "pages": pages,
                    "size": f"{size_kb} KB" if size_kb < 1024 else f"{round(size_kb/1024, 1)} MB",
                }

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# -----------------------------------------------------------------------------
# Dual-Theme Design Tokens (Light Daylight Editorial vs. Dark Obsidian Aurora)
# -----------------------------------------------------------------------------
is_dark = st.session_state.theme == "Dark"

tokens = (
    {
        "bg_app": "#09090B",
        "aurora_1": "rgba(99, 102, 241, 0.14)",
        "aurora_2": "rgba(16, 185, 129, 0.08)",
        "bg_sidebar": "#111115",
        "bg_card": "#16161B",
        "bg_card_hover": "#1E1E26",
        "bg_glass": "rgba(22, 22, 27, 0.82)",
        "bg_user_bubble": "linear-gradient(135deg, #4F46E5 0%, #6366F1 100%)",
        "text_user_bubble": "#FFFFFF",
        "text_main": "#F8FAFC",
        "text_sub": "#A1A1AA",
        "text_muted": "#71717A",
        "border": "#27272A",
        "border_strong": "#3F3F46",
        "accent": "#6366F1",
        "accent_soft": "rgba(99, 102, 241, 0.16)",
        "accent_text": "#A5B4FC",
        "success_bg": "rgba(16, 185, 129, 0.12)",
        "success_text": "#34D399",
        "success_border": "rgba(16, 185, 129, 0.28)",
        "shadow": "0 8px 30px rgba(0, 0, 0, 0.35)",
        "input_bg": "#16161B",
    }
    if is_dark
    else {
        "bg_app": "#F8FAFC",
        "aurora_1": "rgba(99, 102, 241, 0.09)",
        "aurora_2": "rgba(14, 165, 233, 0.07)",
        "bg_sidebar": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_card_hover": "#F1F5F9",
        "bg_glass": "rgba(255, 255, 255, 0.88)",
        "bg_user_bubble": "linear-gradient(135deg, #4F46E5 0%, #6366F1 100%)",
        "text_user_bubble": "#FFFFFF",
        "text_main": "#0F172A",
        "text_sub": "#475569",
        "text_muted": "#64748B",
        "border": "#E2E8F0",
        "border_strong": "#CBD5E1",
        "accent": "#4F46E5",
        "accent_soft": "rgba(79, 70, 229, 0.08)",
        "accent_text": "#4338CA",
        "success_bg": "rgba(16, 185, 129, 0.10)",
        "success_text": "#059669",
        "success_border": "rgba(16, 185, 129, 0.25)",
        "shadow": "0 4px 20px -2px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.04)",
        "input_bg": "#FFFFFF",
    }
)

# -----------------------------------------------------------------------------
# Inject Master Stylesheet (Fully Resolved for Both Light & Dark Themes)
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {{
        --bg-app: {tokens['bg_app']};
        --bg-sidebar: {tokens['bg_sidebar']};
        --bg-card: {tokens['bg_card']};
        --bg-card-hover: {tokens['bg_card_hover']};
        --bg-glass: {tokens['bg_glass']};
        --text-main: {tokens['text_main']};
        --text-sub: {tokens['text_sub']};
        --text-muted: {tokens['text_muted']};
        --border: {tokens['border']};
        --border-strong: {tokens['border_strong']};
        --accent: {tokens['accent']};
        --accent-soft: {tokens['accent_soft']};
        --accent-text: {tokens['accent_text']};
        --shadow: {tokens['shadow']};
    }}

    html, body, [class*="css"], .stMarkdown, p, span, div, label {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    code, pre {{
        font-family: 'JetBrains Mono', monospace !important;
    }}

    /* Hide default Streamlit footer/decoration while keeping sidebar toggle visible */
    #MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{
        visibility: hidden;
    }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    header[data-testid="stHeader"] button {{
        color: var(--text-main) !important;
    }}

    /* Main Canvas with Ambient Aurora Glow */
    .stApp {{
        background-color: var(--bg-app) !important;
        background-image:
            radial-gradient(at 15% 5%, {tokens['aurora_1']} 0px, transparent 48%),
            radial-gradient(at 85% 12%, {tokens['aurora_2']} 0px, transparent 45%) !important;
        color: var(--text-main) !important;
        transition: background-color 0.25s ease, color 0.25s ease;
    }}

    .block-container {{
        max-width: 880px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 6.5rem !important;
    }}

    /* Sidebar Styling (Scoped safely so native widgets stay readable) */
    section[data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border) !important;
    }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] small {{
        color: var(--text-main);
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1.4rem !important;
    }}

    /* Brand Header */
    .brand-box {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 1rem;
        margin-bottom: 1.1rem;
        border-bottom: 1px solid var(--border);
    }}
    .brand-left {{
        display: flex;
        align-items: center;
        gap: 0.7rem;
    }}
    .brand-logo {{
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #06B6D4 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.25);
        flex-shrink: 0;
    }}
    .brand-name {{
        font-weight: 800;
        font-size: 1.06rem;
        letter-spacing: -0.025em;
        color: var(--text-main) !important;
        line-height: 1.15;
    }}
    .brand-tag {{
        font-size: 0.72rem;
        font-weight: 500;
        color: var(--text-muted) !important;
    }}

    .section-cap {{
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted) !important;
        margin-bottom: 0.55rem;
    }}

    /* File Uploader Dropzone & Native Action Buttons */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: var(--bg-card) !important;
        border: 1.5px dashed var(--border-strong) !important;
        border-radius: 12px !important;
        padding: 0.9rem !important;
        transition: all 0.2s ease;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: var(--accent) !important;
        background-color: var(--accent-soft) !important;
    }}
    [data-testid="stFileUploaderDropzone"] button,
    .stDownloadButton > button {{
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow) !important;
    }}
    [data-testid="stFileUploaderDropzone"] button:hover,
    .stDownloadButton > button:hover {{
        border-color: var(--accent) !important;
        background-color: var(--bg-card-hover) !important;
    }}
    [data-testid="stFileUploaderFile"] {{
        background-color: var(--bg-card-hover) !important;
        border-radius: 8px !important;
        padding: 0.35rem 0.5rem !important;
    }}
    [data-testid="stFileUploaderFile"] * {{
        color: var(--text-main) !important;
    }}

    /* Document Cards in Sidebar */
    .doc-card {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.65rem 0.8rem;
        margin-bottom: 0.5rem;
        border-radius: 10px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .doc-card:hover {{
        border-color: var(--accent);
        transform: translateX(2px);
    }}
    .doc-title {{
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text-main) !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 155px;
    }}
    .doc-meta {{
        font-size: 0.7rem;
        color: var(--text-muted) !important;
        margin-top: 2px;
    }}
    .doc-pill {{
        font-size: 0.68rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 999px;
        background: {tokens['success_bg']};
        color: {tokens['success_text']} !important;
        border: 1px solid {tokens['success_border']};
    }}

    /* Glassmorphic Top Workspace Bar */
    .workspace-bar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 1rem;
        border-radius: 14px;
        background: var(--bg-glass);
        border: 1px solid var(--border);
        backdrop-filter: blur(14px);
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
    }}
    .pulse-dot {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
        margin-right: 8px;
    }}
    .idle-dot {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #94A3B8;
        margin-right: 8px;
    }}

    /* Hero Section */
    @keyframes floatIcon {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-5px); }}
    }}
    .hero-wrap {{
        text-align: center;
        padding: 2.2rem 1rem 1.4rem 1rem;
    }}
    .hero-orb {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 60px;
        height: 60px;
        border-radius: 18px;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #06B6D4 100%);
        margin-bottom: 1.15rem;
        box-shadow: 0 14px 30px rgba(79, 70, 229, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.3);
        animation: floatIcon 3.5s ease-in-out infinite;
    }}
    .hero-heading {{
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: -0.035em;
        line-height: 1.18;
        color: var(--text-main) !important;
        margin-bottom: 0.6rem;
    }}
    .hero-gradient-text {{
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #0EA5E9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .hero-sub {{
        font-size: 0.98rem;
        color: var(--text-sub) !important;
        max-width: 540px;
        margin: 0 auto 1.8rem auto;
        line-height: 1.6;
    }}

    /* 3-Step Workflow Strip */
    .steps-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.85rem;
        margin-bottom: 1.8rem;
        text-align: left;
    }}
    .step-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        box-shadow: var(--shadow);
    }}
    .step-num {{
        font-size: 0.68rem;
        font-weight: 700;
        color: var(--accent-text) !important;
        background: var(--accent-soft);
        padding: 2px 8px;
        border-radius: 999px;
        display: inline-block;
        margin-bottom: 0.45rem;
    }}
    .step-title {{
        font-size: 0.86rem;
        font-weight: 700;
        color: var(--text-main) !important;
        margin-bottom: 0.2rem;
    }}
    .step-desc {{
        font-size: 0.76rem;
        color: var(--text-sub) !important;
        line-height: 1.45;
    }}

    /* Buttons, Segmented Theme Switcher, & Popover Styling */
    .stButton > button {{
        border-radius: 11px !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        border: 1px solid var(--border) !important;
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        box-shadow: var(--shadow) !important;
        transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
        padding: 0.55rem 0.9rem !important;
    }}
    .stButton > button:hover {{
        border-color: var(--accent) !important;
        background-color: var(--bg-card-hover) !important;
        transform: translateY(-2px);
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.32) !important;
    }}
    .stButton > button[kind="primary"] * {{
        color: #FFFFFF !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45) !important;
    }}

    [data-testid="stPopover"] > button,
    [data-baseweb="button-group"] button {{
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
    [data-testid="stPopover"] > button:hover,
    [data-baseweb="button-group"] button:hover {{
        border-color: var(--accent) !important;
        background-color: var(--bg-card-hover) !important;
    }}
    [data-baseweb="button-group"] button[aria-checked="true"] {{
        background-color: var(--accent) !important;
        color: #FFFFFF !important;
        border-color: var(--accent) !important;
    }}
    [data-baseweb="button-group"] button[aria-checked="true"] * {{
        color: #FFFFFF !important;
    }}
    [data-testid="stPopoverBody"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-main) !important;
    }}

    /* Status / Expander Containers in Both Themes */
    [data-testid="stExpander"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow) !important;
    }}
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] p,
    [data-testid="stExpander"] span {{
        color: var(--text-main) !important;
    }}

    /* Bordered Assistant Response Cards */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        box-shadow: var(--shadow) !important;
        padding: 0.35rem 0.45rem !important;
        margin: 0.75rem 0 0.4rem 0 !important;
    }}

    /* User Message Bubbles */
    .user-msg-wrap {{
        display: flex;
        justify-content: flex-end;
        margin: 1rem 0;
    }}
    .user-msg-bubble {{
        background: {tokens['bg_user_bubble']};
        color: {tokens['text_user_bubble']} !important;
        padding: 0.85rem 1.15rem;
        border-radius: 18px 18px 4px 18px;
        max-width: 78%;
        font-size: 0.95rem;
        line-height: 1.55;
        box-shadow: 0 6px 18px rgba(79, 70, 229, 0.22);
    }}
    .user-msg-time {{
        font-size: 0.68rem;
        color: rgba(255, 255, 255, 0.82) !important;
        text-align: right;
        margin-top: 4px;
    }}

    /* Assistant Card Header & Telemetry Footer */
    .assistant-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 0.7rem;
        margin-bottom: 0.8rem;
        border-bottom: 1px solid var(--border);
    }}
    .assistant-badge {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--accent-text) !important;
    }}
    .grounding-tag {{
        font-size: 0.7rem;
        font-family: 'JetBrains Mono', monospace;
        padding: 2px 8px;
        border-radius: 6px;
        background: var(--accent-soft);
        color: var(--accent-text) !important;
    }}
    .assistant-footer {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-top: 0.85rem;
        padding-top: 0.65rem;
        border-top: 1px dashed var(--border);
        font-size: 0.72rem;
        color: var(--text-muted) !important;
        font-family: 'JetBrains Mono', monospace;
    }}

    /* Markdown Typography Across Light & Dark Modes */
    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    .stMarkdown strong,
    .stMarkdown td,
    .stMarkdown th {{
        color: var(--text-main) !important;
        font-size: 0.96rem;
        line-height: 1.7;
    }}
    .stMarkdown code {{
        background-color: var(--accent-soft) !important;
        color: var(--accent-text) !important;
        padding: 0.14rem 0.38rem !important;
        border-radius: 5px !important;
        font-size: 0.85em !important;
    }}
    .stMarkdown pre {{
        background-color: var(--bg-card-hover) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 0.85rem !important;
    }}
    .stMarkdown pre code {{
        background-color: transparent !important;
        color: var(--text-main) !important;
        padding: 0 !important;
    }}

    /* Floating Chat Input & Bottom Dock */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div {{
        background-color: var(--bg-app) !important;
    }}
    [data-testid="stChatInput"] {{
        max-width: 880px !important;
        margin: 0 auto !important;
    }}
    [data-testid="stChatInput"] > div {{
        background-color: {tokens['input_bg']} !important;
        border: 1.5px solid var(--border-strong) !important;
        border-radius: 16px !important;
        box-shadow: var(--shadow) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    [data-testid="stChatInput"] > div:focus-within {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 4px var(--accent-soft), var(--shadow) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        color: var(--text-main) !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: var(--text-muted) !important;
        opacity: 1 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def stream_response(text: str):
    """Smooth word-level streaming for a natural conversational feel."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.014)


def export_chat_markdown() -> str:
    """Format conversation history as a clean Markdown transcript."""
    lines = ["# DocuMind RAG Session Transcript\n"]
    for m in st.session_state.messages:
        role = "User" if m["role"] == "user" else "DocuMind AI"
        lines.append(f"### {role} ({m.get('time', '')})\n{m['content']}\n")
    return "\n---\n".join(lines)


# -----------------------------------------------------------------------------
# Sidebar: Knowledge Studio
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div class="brand-box">
            <div class="brand-left">
                <div class="brand-logo">{LOGO_SVG_SIDEBAR}</div>
                <div>
                    <div class="brand-name">DocuMind</div>
                    <div class="brand-tag">PDF Vector Studio</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-cap">1 · Add Documents</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Drop PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if st.button(
        "Build Vector Index",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
        icon=":material/bolt:",
    ):
        os.makedirs("data", exist_ok=True)
        with st.status("Indexing PDFs into ChromaDB...", expanded=True) as status:
            for pdf in uploaded_files:
                st.write(f"Chunking & embedding **{pdf.name}**...")
                file_path = os.path.join("data", pdf.name)
                with open(file_path, "wb") as f:
                    f.write(pdf.getbuffer())
                process_pdf(file_path)

                try:
                    pages = len(PdfReader(file_path).pages)
                except Exception:
                    pages = "?"
                size_kb = round(len(pdf.getbuffer()) / 1024, 1)
                st.session_state.indexed_docs[pdf.name] = {
                    "pages": pages,
                    "size": f"{size_kb} KB" if size_kb < 1024 else f"{round(size_kb/1024, 1)} MB",
                }
            status.update(label="Knowledge base ready!", state="complete", expanded=False)
        st.rerun()

    st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-cap">2 · Indexed Library ({len(st.session_state.indexed_docs)})</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.indexed_docs:
        for fname, meta in st.session_state.indexed_docs.items():
            safe_fname = html.escape(fname)
            st.markdown(
                f"""
                <div class="doc-card">
                    <div>
                        <div class="doc-title" title="{safe_fname}">📄 {safe_fname}</div>
                        <div class="doc-meta">{meta['pages']} pages · {meta['size']}</div>
                    </div>
                    <span class="doc-pill">Active</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div style="padding: 0.9rem; border-radius: 10px; border: 1px dashed var(--border);
                        font-size: 0.78rem; color: var(--text-muted); text-align: center;">
                No PDFs indexed yet.<br/>Upload a file above to begin.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.messages:
        st.markdown("<div style='height: 1.4rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-cap">Session Controls</div>', unsafe_allow_html=True)
        st.download_button(
            "Export Transcript (.md)",
            data=export_chat_markdown(),
            file_name="documind_chat.md",
            mime="text/markdown",
            use_container_width=True,
            icon=":material/download:",
        )
        if st.button(
            "Clear Conversation",
            use_container_width=True,
            icon=":material/delete_sweep:",
        ):
            st.session_state.messages = []
            st.rerun()

# -----------------------------------------------------------------------------
# Top Workspace Bar (Live Index Status + Instant Light/Dark Switcher)
# -----------------------------------------------------------------------------
col_status, col_theme = st.columns([3.2, 1.3], vertical_alignment="center")

with col_status:
    doc_count = len(st.session_state.indexed_docs)
    if doc_count > 0:
        status_text = f'<span class="pulse-dot"></span><strong>{doc_count}</strong> PDF{"s" if doc_count > 1 else ""} ready for semantic search'
    else:
        status_text = '<span class="idle-dot"></span>Waiting for PDF upload in sidebar'

    st.markdown(
        f"""
        <div class="workspace-bar" style="margin-bottom: 0;">
            <div style="font-size: 0.82rem; color: var(--text-main);">{status_text}</div>
            <div style="font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; color: var(--text-muted);">
                gemini-2.5-flash
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_theme:
    selected_theme = st.segmented_control(
        "Theme",
        options=["Light", "Dark"],
        default=st.session_state.theme,
        format_func=lambda x: "☀️ Light" if x == "Light" else "🌙 Dark",
        label_visibility="collapsed",
        key="theme_selector",
    )
    if selected_theme and selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Pre-Query Empty State (Hero + Visual Workflow + Bento Starter Cards)
# -----------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div class="hero-orb">{LOGO_SVG_HERO}</div>
            <div class="hero-heading">
                Chat with your documents,<br/>
                <span class="hero-gradient-text">grounded in real context.</span>
            </div>
            <div class="hero-sub">
                Upload PDFs on the left to create a semantic vector index, then ask complex questions, extract figures, or synthesize summaries in seconds.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.indexed_docs:
        st.markdown(
            """
            <div class="steps-grid">
                <div class="step-card">
                    <span class="step-num">STEP 01</span>
                    <div class="step-title">Upload PDFs</div>
                    <div class="step-desc">Drop one or multiple PDF documents into the sidebar uploader.</div>
                </div>
                <div class="step-card">
                    <span class="step-num">STEP 02</span>
                    <div class="step-title">Build Index</div>
                    <div class="step-desc">Text is split into overlapping chunks and embedded into ChromaDB.</div>
                </div>
                <div class="step-card">
                    <span class="step-num">STEP 03</span>
                    <div class="step-title">Ask & Explore</div>
                    <div class="step-desc">Query your files or click any prompt card below to start.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="section-cap" style="margin-bottom: 0.75rem;">Suggested Prompts</div>',
        unsafe_allow_html=True,
    )

    bento_prompts = [
        ("Executive Summary", "Summarize the core thesis and key takeaways in 5 bullet points"),
        ("Metrics & Numbers", "Extract all important dates, statistics, and financial figures"),
        ("Critical Insights", "What are the biggest risks, gaps, or limitations mentioned?"),
        ("Actionable Steps", "Create a structured action plan based on the document's recommendations"),
    ]

    grid_cols = st.columns(2, gap="medium")
    for idx, (category, prompt_text) in enumerate(bento_prompts):
        with grid_cols[idx % 2]:
            if st.button(
                f"{category}  ·  {prompt_text}",
                key=f"bento_{idx}",
                use_container_width=True,
                icon=":material/arrow_outward:",
            ):
                st.session_state.pending_prompt = prompt_text
                st.rerun()

# -----------------------------------------------------------------------------
# Conversation Thread (Structured Cards + Telemetry + Post-Response Actions)
# -----------------------------------------------------------------------------
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        safe_content = html.escape(msg["content"]).replace("\n", "<br/>")
        st.markdown(
            f"""
            <div class="user-msg-wrap">
                <div class="user-msg-bubble">
                    {safe_content}
                    <div class="user-msg-time">{msg.get('time', '')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        latency = msg.get("latency", "—")
        words = len(msg["content"].split())
        docs_used = msg.get("doc_count", len(st.session_state.indexed_docs))

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="assistant-header">
                    <span class="assistant-badge">{LOGO_SVG_BADGE} DocuMind Answer</span>
                    <span class="grounding-tag">Grounded · {docs_used} doc(s)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(msg["content"])
            st.markdown(
                f"""
                <div class="assistant-footer">
                    <span>⚡ {latency}s</span>
                    <span>📝 {words} words</span>
                    <span>🕒 {msg.get('time', '')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Action bar & smart follow-up chips on the latest assistant message
        if idx == len(st.session_state.messages) - 1:
            act_col1, act_col2, act_col3 = st.columns([1.2, 1.4, 3.4])
            with act_col1:
                with st.popover("Copy Text", icon=":material/content_copy:", use_container_width=True):
                    st.code(msg["content"], language="markdown")
            with act_col2:
                if st.button(
                    "Regenerate",
                    key=f"regen_{idx}",
                    icon=":material/refresh:",
                    use_container_width=True,
                ):
                    last_user_q = st.session_state.messages[-2]["content"]
                    st.session_state.messages = st.session_state.messages[:-2]
                    st.session_state.pending_prompt = last_user_q
                    st.rerun()

            st.markdown(
                '<div class="section-cap" style="margin-top: 0.65rem; margin-bottom: 0.4rem;">Follow-up Explorations</div>',
                unsafe_allow_html=True,
            )
            f_cols = st.columns(3, gap="small")
            followups = [
                "Break this down simply",
                "Give specific examples",
                "Compare key points in a table",
            ]
            for f_idx, f_text in enumerate(followups):
                with f_cols[f_idx]:
                    if st.button(
                        f_text,
                        key=f"followup_{idx}_{f_idx}",
                        use_container_width=True,
                        icon=":material/subdirectory_arrow_right:",
                    ):
                        st.session_state.pending_prompt = f_text
                        st.rerun()

# -----------------------------------------------------------------------------
# Query Submission & Multi-Stage RAG Execution
# -----------------------------------------------------------------------------
typed_prompt = st.chat_input("Ask anything about your indexed PDFs...")
active_prompt = typed_prompt or st.session_state.pending_prompt

if active_prompt:
    st.session_state.pending_prompt = None
    now_str = datetime.now().strftime("%I:%M %p")

    # 1. Immediately render optimistic user bubble
    st.session_state.messages.append(
        {"role": "user", "content": active_prompt, "time": now_str}
    )
    safe_prompt = html.escape(active_prompt).replace("\n", "<br/>")
    st.markdown(
        f"""
        <div class="user-msg-wrap">
            <div class="user-msg-bubble">
                {safe_prompt}
                <div class="user-msg-time">{now_str}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Multi-stage retrieval feedback + streamed synthesis
    start_time = time.perf_counter()
    try:
        with st.status("Running RAG retrieval pipeline...", expanded=True) as status:
            st.write("🔹 Encoding query with `gemini-embedding-001`...")
            time.sleep(0.15)
            st.write("🔹 Searching ChromaDB semantic vectors...")
            answer = ask_question(active_prompt)
            status.update(
                label="Context retrieved & synthesized",
                state="complete",
                expanded=False,
            )

        elapsed = round(time.perf_counter() - start_time, 2)
        docs_used = len(st.session_state.indexed_docs)

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="assistant-header">
                    <span class="assistant-badge">{LOGO_SVG_BADGE} DocuMind Answer</span>
                    <span class="grounding-tag">Grounded · {docs_used} doc(s)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write_stream(stream_response(answer))

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "time": datetime.now().strftime("%I:%M %p"),
                "latency": elapsed,
                "doc_count": docs_used,
            }
        )
        st.rerun()
    except Exception as e:
        st.error(f"Could not generate response: {e}")