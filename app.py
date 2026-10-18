import os
import time
import uuid
import sqlite3
import base64
import random
from datetime import datetime, date, timedelta
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "phucs.db"
LOGO_PATH = APP_DIR / "assets" / "phucs_logo.png"

# Load integrations once at startup. If the helper file was omitted from GitHub,
# or a dependency failed to install, keep the whole app alive and show a useful
# error only when an integration is used (instead of crashing the entire page).
def _integration_unavailable(*args, **kwargs):
    detail = repr(INTEGRATION_IMPORT_ERROR) if INTEGRATION_IMPORT_ERROR else "không rõ nguyên nhân"
    raise RuntimeError(
        "Không tải được phucs_integrations.py hoặc thư viện phụ thuộc. "
        "Hãy bảo đảm file phucs_integrations.py nằm cùng thư mục với app.py, "
        "requirements.txt đã được cài và redeploy ứng dụng. Chi tiết: " + detail
    )

def _setting_fallback(name, default=""):
    try:
        value = st.secrets.get(name, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()

INTEGRATION_IMPORT_ERROR = None
try:
    from phucs_integrations import (
        setting, ai_client, chat_completion, test_ai_connection, tavily_search, analyze_image, transcribe_audio, generate_image,
        replicate_create, supabase_client, create_checkout_url, upload_supabase_file,
        group_messages, send_group_message,
    )
except Exception as _exc:
    INTEGRATION_IMPORT_ERROR = _exc
    setting = _setting_fallback
    ai_client = chat_completion = test_ai_connection = _integration_unavailable
    tavily_search = analyze_image = transcribe_audio = generate_image = _integration_unavailable
    replicate_create = supabase_client = create_checkout_url = upload_supabase_file = _integration_unavailable
    group_messages = send_group_message = _integration_unavailable

st.set_page_config(
    page_title="P.H.U.C.S AI — Learn together",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual identity ----------
PINK = "#D94F83"
PALE = "#FFF4F8"
DARK_PINK = "#A82F62"

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=Nunito:wght@400;600;700;800;900&display=swap');
    :root { --phucs-pink:#ec4899; --phucs-hot:#d92f87; --phucs-deep:#8f2854; --phucs-pale:#fff3f8; --phucs-line:#f7c9df; }
    html, body, [class*="css"] { font-family:'Be Vietnam Pro',sans-serif; }
    .stApp { background:radial-gradient(ellipse at 12% 5%,rgba(255,211,231,.62),transparent 33%),radial-gradient(ellipse at 92% 18%,rgba(255,226,240,.72),transparent 28%),linear-gradient(135deg,#fff9fc 0%,#fff0f7 48%,#fffafd 100%); color:#52253e; }
    [data-testid="stHeader"] { background:rgba(255,248,252,.76); }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#ffe5f1 0%,#fff3f8 55%,#fffafd 100%); border-right:1px solid #f5c4da; }
    [data-testid="stSidebar"] > div:first-child { padding-top:1.1rem; }
    [data-testid="stSidebar"] [data-testid="stImage"] img { border-radius:22px; }
    h1,h2,h3 { color:var(--phucs-deep); font-family:'Nunito','Be Vietnam Pro',sans-serif; font-weight:850; }
    h1 { letter-spacing:-.035em; }
    .hero { position:relative; overflow:hidden; padding:1.6rem 1.8rem; border:1px solid rgba(244,174,205,.8); border-radius:28px;
      background:linear-gradient(112deg,rgba(255,255,255,.94),rgba(255,226,240,.86)),radial-gradient(circle at 88% 15%,#ffd2e7,transparent 35%);
      box-shadow:0 14px 38px rgba(177,56,106,.10); }
    .welcome-hero { position:relative; overflow:hidden; padding:1.7rem 1.8rem; margin:.3rem 0 1.1rem; border:1px solid #f4bfd7; border-radius:28px;
      background:linear-gradient(110deg,rgba(255,255,255,.97) 0%,rgba(255,240,247,.94) 52%,rgba(255,219,237,.84) 100%);
      box-shadow:0 12px 32px rgba(177,56,106,.09); }
    .welcome-hero:after { content:'♡'; position:absolute; right:5%; top:-35px; font-size:170px; line-height:1; color:rgba(236,72,153,.09); transform:rotate(15deg); pointer-events:none; }
    .brand { font-family:'Nunito',sans-serif; font-weight:900; letter-spacing:.035em; font-size:clamp(2rem,5vw,3.5rem); color:#d93687; line-height:1.05; }
    .slogan { color:#8f2854; font-weight:700; font-size:1rem; }
    .small-muted { color:#986d83; font-size:.9rem; }
    div.stButton > button, .stLinkButton a { border-radius:16px; border:1px solid #f1b6d0; font-weight:700; transition:all .18s ease; }
    div.stButton > button:hover, .stLinkButton a:hover { border-color:#e879ae; color:#a82f62; box-shadow:0 5px 16px rgba(217,47,135,.12); transform:translateY(-1px); }
    div.stButton > button[kind="primary"] { background:linear-gradient(135deg,#f472b6,#df2f8b); color:white; border:0; box-shadow:0 6px 18px rgba(217,47,135,.18); }
    [data-testid="stMetric"] { background:rgba(255,255,255,.86); padding:1rem; border:1px solid #f4d0df; border-radius:20px; box-shadow:0 5px 18px rgba(177,56,106,.045); }
    [data-testid="stExpander"] { border:1px solid #f5c9dc; border-radius:16px; background:rgba(255,255,255,.72); }
    [data-testid="stChatMessage"] { background:rgba(255,255,255,.78); border:1px solid #f7d6e5; border-radius:18px; padding:.85rem 1rem; }
    [data-testid="stChatInput"] textarea { border-radius:22px!important; border-color:#f1b6d0!important; background:rgba(255,255,255,.92)!important; }
    .stTabs [data-baseweb="tab-list"] { gap:7px; padding:7px; border:1px solid #f6c8dc; border-radius:19px; background:rgba(255,255,255,.72); flex-wrap:wrap; }
    .stTabs [data-baseweb="tab"] { background:#fff0f7; border:1px solid #f8d5e5; border-radius:14px; padding:9px 14px; color:#8f2854; }
