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
    page_title="P.H.U.C.S AI — Đồng hành cùng bạn",
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
    .stTabs [aria-selected="true"] { background:linear-gradient(135deg,#f472b6,#df2f8b)!important; color:white!important; border-color:#df2f8b!important; }
    [data-testid="stFileUploader"] section { background:rgba(255,255,255,.68); border:1px dashed #e9a9c7; border-radius:16px; }
    input, textarea, [data-baseweb="select"] > div { border-radius:13px!important; }
    hr { border-color:#f3c8db!important; }
    /* High contrast: keep all text readable over translucent/animated backgrounds. */
    [data-testid="stAppViewContainer"] { color:#3f2634; }
    [data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] label, [data-testid="stAppViewContainer"] .stMarkdown,
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] { color:#49313f; }
    [data-testid="stChatMessage"] { background:#ffffff!important; border:1px solid #e6a9c5!important; box-shadow:0 5px 18px rgba(80,32,57,.08); color:#30202a!important; }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li, [data-testid="stChatMessage"] span { color:#30202a!important; }
    [data-testid="stChatInput"] textarea, [data-testid="stChatInput"] textarea:focus { background:#ffffff!important; color:#30202a!important; -webkit-text-fill-color:#30202a!important; border:1.5px solid #cc6d9b!important; }
    [data-testid="stChatInput"] textarea::placeholder { color:#765969!important; opacity:1!important; }
    [data-testid="stExpander"], [data-testid="stMetric"], [data-testid="stFileUploader"] section { background:rgba(255,255,255,.96)!important; color:#30202a!important; }
    [data-baseweb="select"] *, input, textarea { color:#30202a; }
    .stTabs [data-baseweb="tab"] { color:#702449!important; font-weight:700; }
    .stTabs [aria-selected="true"] { color:#fff!important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown { color:#48263a; }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms!important; animation-iteration-count:1!important; scroll-behavior:auto!important; } }
    @media (max-width: 760px) { .welcome-hero {padding:1.2rem;} .hero {padding:1.2rem;} .stTabs [data-baseweb="tab"] {padding:7px 9px;} }
    </style>
    """, unsafe_allow_html=True)

inject_css()

# ---------- Database ----------
def db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, provider TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chats (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
          title TEXT NOT NULL, messages TEXT NOT NULL DEFAULT '[]',
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS todos (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
          task TEXT NOT NULL, due_date TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
          title TEXT NOT NULL, category TEXT NOT NULL, event_date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
          title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS study_sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
          subject TEXT NOT NULL, seconds INTEGER NOT NULL, saved_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS local_group_messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT, group_id TEXT NOT NULL,
          user_id TEXT NOT NULL, display_name TEXT NOT NULL, content TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """)
init_db()

def current_user():
    return st.session_state.get("user")

def create_user(name, provider="guest"):
    uid = str(uuid.uuid4())[:8].upper()
    user = {"user_id": uid, "display_name": name.strip() or "Học viên", "provider": provider}
    with db() as con:
        con.execute("INSERT INTO users VALUES (?,?,?,?)",
                    (uid, user["display_name"], provider, datetime.now().isoformat(timespec="seconds")))
    st.session_state.user = user
    st.session_state.active_chat = None
    st.session_state.messages = []
    st.rerun()

# ---------- Login ----------
def login_screen():
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.1, 1], gap="large", vertical_alignment="center")
    with left:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        st.markdown("""
        <div class="hero" style="text-align:center;padding:2.1rem 1.2rem">
          <div class="brand">P.H.U.C.S</div>
          <div style="font-size:1.1rem;font-weight:800;color:#a82f62;margin:.35rem 0">
            Personal Highly Useful Computer System
          </div>
          <p class="slogan">Đồng hành cùng P.H.U.C.S, vững bước thành công</p>
          <p class="small-muted">Không gian học tập thông minh — sáng tạo — truyền cảm hứng.</p>
        </div>
        """, unsafe_allow_html=True)
        logo = st.file_uploader("Tải logo riêng (PNG/JPG, tùy chọn)", type=["png", "jpg", "jpeg"], key="login_logo")
        if logo:
            st.image(logo, width=220)
    with right:
        st.markdown("### Chào mừng bạn đến với P.H.U.C.S")
        st.write("Đăng nhập để bắt đầu hành trình chinh phục tri thức.")
        name = st.text_input("Tên hiển thị", placeholder="Ví dụ: Minh Anh")
        if st.button("✨ Tiếp tục với tài khoản khách", type="primary", use_container_width=True):
            create_user(name or "Học viên", "guest")
        st.divider()
        st.markdown("**Đăng nhập bằng tài khoản bên ngoài**")
        st.caption("Cần cấu hình OAuth và callback URL trong môi trường triển khai để xác minh tài khoản thật.")
        # Real social OAuth is delegated to Supabase Auth. Provider credentials and redirect URLs
        # must first be configured in the Supabase dashboard.
        try:
            from phucs_integrations import setting, supabase_client
            supabase_ready = bool(setting("SUPABASE_URL") and setting("SUPABASE_ANON_KEY"))
        except Exception:
            supabase_ready = False
        cols = st.columns(3)
        for col, label, provider in zip(cols, ["Google", "Facebook", "Apple / iCloud"], ["google", "facebook", "apple"]):
            with col:
                if supabase_ready:
                    if st.button(label, use_container_width=True, key=f"oauth_{provider}"):
                        try:
                            from urllib.parse import urlparse
                            client = supabase_client()
                            st.session_state["supabase_oauth_client"] = client
                            redirect_to = setting("APP_BASE_URL", "http://localhost:8501")
                            result = client.auth.sign_in_with_oauth({"provider": provider, "options": {"redirect_to": redirect_to}})
                            oauth_url = getattr(result, "url", None) or (result.get("url") if isinstance(result, dict) else None)
                            if oauth_url:
                                st.session_state["oauth_link"] = oauth_url
                            else:
                                st.error("Không nhận được URL OAuth từ Supabase.")
                        except Exception as exc:
                            st.error(f"Không tạo được liên kết đăng nhập: {exc}")
                else:
                    st.button(label, disabled=True, use_container_width=True,
                              help="Cấu hình SUPABASE_URL và SUPABASE_ANON_KEY trước.")
        if st.session_state.get("oauth_link"):
            st.link_button("Tiếp tục đăng nhập an toàn ↗", st.session_state["oauth_link"], use_container_width=True)
        st.info("Đăng nhập xã hội dùng Supabase Auth. Bạn phải bật Google/Facebook/Apple và cấu hình callback trong Supabase trước khi dùng thật.")

# Handle Supabase OAuth PKCE callback after the provider redirects back to APP_BASE_URL.
try:
    from phucs_integrations import setting, supabase_client
    oauth_code = st.query_params.get("code")
    if oauth_code and not current_user() and setting("SUPABASE_URL") and setting("SUPABASE_ANON_KEY"):
        try:
            auth_client = st.session_state.get("supabase_oauth_client") or supabase_client()
            auth_result = auth_client.auth.exchange_code_for_session(oauth_code)
            auth_user = getattr(auth_result, "user", None)
            if auth_user is None and isinstance(auth_result, dict):
                auth_user = auth_result.get("user")
            if auth_user:
                if isinstance(auth_user, dict):
                    au = auth_user
                else:
                    au = {"id": getattr(auth_user, "id", ""), "email": getattr(auth_user, "email", ""),
                          "user_metadata": getattr(auth_user, "user_metadata", {}) or {},
                          "app_metadata": getattr(auth_user, "app_metadata", {}) or {}}
                metadata = au.get("user_metadata") or {}
                provider = (au.get("app_metadata") or {}).get("provider", "supabase")
                name = metadata.get("full_name") or metadata.get("name") or au.get("email") or "Học viên"
                user_id = str(au.get("id") or uuid.uuid4())
                st.session_state.user = {"user_id": user_id, "display_name": name, "provider": provider}
                st.session_state.active_chat = None
                st.session_state.messages = []
                st.query_params.clear()
                st.rerun()
        except Exception as oauth_exc:
            st.error(f"Đăng nhập OAuth chưa hoàn tất: {oauth_exc}. Kiểm tra callback URL trong Supabase.")
except Exception:
    pass

if not current_user():
    login_screen()
    st.stop()

user = current_user()
uid = user["user_id"]

# ---------- Sidebar ----------
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    st.markdown("<div style='text-align:center' class='brand'>P.H.U.C.S</div>", unsafe_allow_html=True)
    st.caption("Đồng hành cùng P.H.U.C.S, vững bước thành công")
    st.divider()
    avatar_file = st.file_uploader("🖼️ Ảnh đại diện (tùy chọn)", type=["png", "jpg", "jpeg", "webp"], key="user_avatar")
    if avatar_file:
        st.image(avatar_file, width=88)
    st.markdown(f"### 👤 {user['display_name']}")
    st.caption(f"ID cá nhân: `{uid}`")
    st.caption(f"Tài khoản: {user['provider'].title()}")
    if st.button("↪ Đăng xuất", use_container_width=True):
        for key in ["user", "messages", "active_chat"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    language = st.selectbox("🌐 Ngôn ngữ", [
        "Tiếng Việt", "English", "한국어", "Français", "Deutsch", "日本語",
        "Español", "Русский", "中文", "ไทย", "Português", "Italiano"
    ])
    theme = st.selectbox("🎨 Giao diện & Hình nền", [
        "Hồng mộng mơ (động)", "Dải ngân hà hồng (động)", "Sóng biển pastel (động)",
        "Cực quang tím hồng (động)", "Bình minh đào (động)", "Mây trôi xanh hồng (động)",
        "Hoa anh đào (tĩnh)", "Bầu trời xanh (tĩnh)", "Hoàng hôn tím (tĩnh)",
        "Giấy kem tối giản (tĩnh)", "Dark mode hồng đêm"
    ])
    st.session_state.theme = theme
    if theme == "Dark mode hồng đêm":
        st.markdown("""<style>
        [data-testid="stAppViewContainer"], .stApp {background:linear-gradient(135deg,#171321,#2b2036 55%,#241a2b)!important;color:#f8edf7!important}
        [data-testid="stSidebar"] {background:linear-gradient(180deg,#241b2d,#302238)!important}
        h1,h2,h3,h4,p,label,span,li,.stMarkdown {color:inherit}
        [data-testid="stChatMessage"] {background:#34263d!important;border:1px solid #62445f!important;color:#fff5fb!important}
        [data-testid="stChatMessage"] p,[data-testid="stChatMessage"] li {color:#fff5fb!important}
        [data-testid="stChatInput"] textarea {background:#241b2d!important;color:#fff!important;border:1px solid #b66c9b!important}
        [data-testid="stExpander"],[data-testid="stMetric"] {background:#302238!important;color:#fff!important;border-color:#62445f!important}
        </style>""", unsafe_allow_html=True)
    bg = st.file_uploader("Tải hình nền riêng", type=["png", "jpg", "jpeg", "webp"], key="bg_upload")
    if bg:
        st.image(bg, caption="Xem trước hình nền", use_container_width=True)
        if len(bg.getvalue()) <= 5 * 1024 * 1024:
            encoded_bg = base64.b64encode(bg.getvalue()).decode("ascii")
            mime = bg.type or "image/png"
            st.markdown(f"""<style>
            [data-testid='stAppViewContainer'] {{background-image:linear-gradient(90deg,rgba(255,245,250,.82),rgba(255,245,250,.68)),url('data:{mime};base64,{encoded_bg}') !important;background-size:cover !important;background-position:center !important;background-attachment:fixed !important;}}
            [data-testid='stHeader'] {{background:rgba(255,245,250,.35) !important;}}
            [data-testid='stSidebar'] {{background:rgba(255,231,240,.92) !important;backdrop-filter:blur(16px);}}
            </style>""", unsafe_allow_html=True)
            st.caption("Đã áp dụng ảnh làm nền toàn trang trong phiên hiện tại. Tải lại file sau khi mở phiên mới.")
        else:
            st.warning("Ảnh nền vượt 5 MB. Hãy nén ảnh nhỏ hơn để áp dụng làm nền.")
    else:
        # Presets are CSS-only, so they work on Streamlit Cloud without external assets.
        presets = {
            "Hồng mộng mơ (động)": "@keyframes phucsDream{0%{background-position:0% 40%}50%{background-position:100% 60%}100%{background-position:0% 40%}} [data-testid='stAppViewContainer']{background:linear-gradient(120deg,#fff8fc,#ffe4ef,#f4e7ff,#fff1f7)!important;background-size:300% 300%!important;animation:phucsDream 22s ease infinite}",
            "Dải ngân hà hồng (động)": "@keyframes phucsGalaxy{0%{background-position:0% 50%}100%{background-position:100% 50%}} [data-testid='stAppViewContainer']{background:radial-gradient(circle at 20% 30%,#ffd6ee 0,transparent 28%),radial-gradient(circle at 80% 20%,#cfc4ff 0,transparent 32%),linear-gradient(120deg,#fff0f8,#e4d8ff,#ffddeb)!important;background-size:220% 220%!important;animation:phucsGalaxy 18s ease infinite}",
            "Sóng biển pastel (động)": "@keyframes phucsWave{0%{background-position:0% 50%}100%{background-position:100% 50%}} [data-testid='stAppViewContainer']{background:repeating-radial-gradient(ellipse at 50% 120%,rgba(255,255,255,.42) 0 16px,transparent 18px 42px),linear-gradient(135deg,#ffe5f1,#dff5ff,#ffd6e9)!important;background-size:auto,240% 240%!important;animation:phucsWave 24s linear infinite}",
            "Cực quang tím hồng (động)": "@keyframes phucsAurora{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}} [data-testid='stAppViewContainer']{background:radial-gradient(ellipse at 15% 15%,#e8c7ff 0,transparent 38%),radial-gradient(ellipse at 85% 30%,#ffc9e8 0,transparent 35%),linear-gradient(125deg,#f8efff,#dce8ff,#ffe7f3)!important;background-size:220% 220%!important;animation:phucsAurora 20s ease infinite}",
            "Bình minh đào (động)": "@keyframes phucsSunrise{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}} [data-testid='stAppViewContainer']{background:linear-gradient(125deg,#fff1dc,#ffd8d2,#ffe8f4,#fff4dd)!important;background-size:300% 300%!important;animation:phucsSunrise 25s ease infinite}",
            "Mây trôi xanh hồng (động)": "@keyframes phucsClouds{0%{background-position:0% 0%}100%{background-position:500px 0%}} [data-testid='stAppViewContainer']{background:radial-gradient(ellipse at 20% 20%,#fff 0 7%,transparent 30%),radial-gradient(ellipse at 70% 35%,#fff 0 8%,transparent 32%),linear-gradient(135deg,#dff5ff,#f7e8ff,#ffe7f2)!important;background-size:650px 500px,800px 600px,200% 200%!important;animation:phucsClouds 36s linear infinite}",
            "Hoa anh đào (tĩnh)": "[data-testid='stAppViewContainer']{background:radial-gradient(circle at 12% 18%,#ffd3e5 0,transparent 25%),radial-gradient(circle at 90% 70%,#f7d9ff 0,transparent 30%),linear-gradient(135deg,#fff8fc,#ffedf5,#fffafd)!important}",
            "Bầu trời xanh (tĩnh)": "[data-testid='stAppViewContainer']{background:radial-gradient(ellipse at 20% 15%,#fff 0 5%,transparent 28%),linear-gradient(155deg,#e0f5ff,#f4f0ff 55%,#ffeaf4)!important}",
            "Hoàng hôn tím (tĩnh)": "[data-testid='stAppViewContainer']{background:linear-gradient(145deg,#fbe4ff,#e7ddff 48%,#ffdfe8)!important}",
            "Giấy kem tối giản (tĩnh)": "[data-testid='stAppViewContainer']{background:linear-gradient(135deg,#fffaf0,#f8f1e8,#fff7fb)!important}"
        }
        if theme in presets:
            st.markdown(f"<style>{presets[theme]}</style>", unsafe_allow_html=True)
    st.divider()
    with st.expander("⚙️ Cài đặt"):
        st.markdown("**P.H.U.C.S AI Plus**")
        st.write("35.000 VNĐ/năm — giá hiển thị tham khảo; cần cấu hình Stripe trước khi thu tiền thật.")
        st.write("• Hạn mức sử dụng rộng hơn (phải triển khai quyền hạn ở máy chủ)")
        st.write("• Mục tiêu dung lượng 500 GB; dung lượng thật phụ thuộc gói lưu trữ đã mua")
        if st.button("Xem gói Plus", use_container_width=True, key="sidebar_plus"):
            st.session_state["open_plus_tab"] = True
        st.divider()
        st.markdown("**🔔 Thông báo**")
        notif = st.toggle("Bật thông báo", value=True)
        if not notif:
            st.caption("Thông báo đang tắt trong phiên hiện tại.")
        else:
            st.selectbox("Tắt thông báo trong", ["Không", "1 giờ", "2 giờ", "3 giờ", "4 giờ", "6 giờ", "12 giờ"])
        st.divider()
        st.markdown("**🗣️ Giọng đọc**")
        st.selectbox("Giọng P.H.U.C.S", [
            "Nữ trung — miền Bắc", "Nữ cao — miền Bắc", "Nữ trầm — miền Nam",
            "Nam trung — miền Bắc", "Nam trầm — miền Nam", "Nam cao — miền Trung"
        ])
        st.caption("Tùy chọn giọng đọc cần tích hợp dịch vụ Text-to-Speech.")
        st.divider()
        st.markdown("**ⓘ Giới thiệu**")
        st.write("P.H.U.C.S AlphaOS 2")
        st.caption("Bản khởi đầu. Các bản sau sẽ bổ sung đăng nhập, đồng bộ và công cụ nâng cao.")

    st.divider()
    st.markdown("**🔎 Tìm lịch sử chat**")
    search_text = st.text_input("Từ khóa", label_visibility="collapsed", placeholder="Tìm cuộc trò chuyện...")
    if st.button("Tìm", use_container_width=True):
        st.session_state.history_search = search_text

    if st.button("＋ Cuộc trò chuyện mới", type="primary", use_container_width=True):
        st.session_state.active_chat = None
        st.session_state.messages = []
        st.rerun()

    with db() as con:
        chats = con.execute("SELECT id,title,updated_at FROM chats WHERE user_id=? ORDER BY updated_at DESC", (uid,)).fetchall()
    st.markdown("**Lịch sử trò chuyện**")
    for chat in chats:
        if st.session_state.get("history_search") and st.session_state.history_search.lower() not in chat["title"].lower():
            continue
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button("💬 " + chat["title"][:27], key=f"open_chat_{chat['id']}", use_container_width=True):
                import json
                st.session_state.active_chat = chat["id"]
                with db() as con:
                    row = con.execute("SELECT messages FROM chats WHERE id=? AND user_id=?", (chat["id"], uid)).fetchone()
                st.session_state.messages = json.loads(row["messages"]) if row else []
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"delete_chat_{chat['id']}"):
                with db() as con:
                    con.execute("DELETE FROM chats WHERE id=? AND user_id=?", (chat["id"], uid))
                if st.session_state.get("active_chat") == chat["id"]:
                    st.session_state.active_chat = None
                    st.session_state.messages = []
                st.rerun()

# ---------- Header ----------
st.markdown(f"""
<div class="welcome-hero">
  <div style="display:flex;align-items:center;gap:18px;position:relative;z-index:1;flex-wrap:wrap">
    <div style="font-size:2.5rem;line-height:1">👋</div>
    <div style="flex:1;min-width:230px">
      <div style="font-family:Nunito,sans-serif;font-weight:900;font-size:clamp(1.7rem,3vw,2.45rem);color:#a82f62;line-height:1.2">Xin chào, {user['display_name']}!</div>
      <div style="font-size:1.02rem;color:#7b3155;margin-top:.55rem">Mình là P.H.U.C.S AI — luôn sẵn sàng hỗ trợ bạn học tập, khám phá và chinh phục mọi ước mơ!</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:1rem">
        <span style="background:#fff;border:1px solid #f5c6dc;border-radius:999px;padding:8px 13px;color:#a82f62;font-size:.86rem">✦ Học tập thông minh</span>
        <span style="background:#fff;border:1px solid #f5c6dc;border-radius:999px;padding:8px 13px;color:#a82f62;font-size:.86rem">🔎 Tìm kiếm kiến thức</span>
        <span style="background:#fff;border:1px solid #f5c6dc;border-radius:999px;padding:8px 13px;color:#a82f62;font-size:.86rem">🪄 Sáng tạo nội dung</span>
        <span style="background:#fff;border:1px solid #f5c6dc;border-radius:999px;padding:8px 13px;color:#a82f62;font-size:.86rem">♡ Đồng hành 24/7</span>
      </div>
    </div>
    <div style="text-align:center;min-width:125px;padding:10px 14px;background:rgba(255,255,255,.65);border:1px solid #f8d5e5;border-radius:22px">
      <div style="font-size:2.3rem">🎓</div><div style="font-family:Nunito,sans-serif;font-weight:900;font-size:1.25rem;color:#df2f8b">P.H.U.C.S AI</div><div style="font-size:.78rem;color:#986d83">AlphaOS 2 · Learning buddy</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

pages = st.tabs(["💬 Cơ bản", "⏱️ Đồng hồ học", "📅 Lịch & Sự kiện", "✅ To-do List",
                 "📝 Note & Studio", "📊 Biểu đồ", "🎮 Giải trí", "🧪 Phòng thí nghiệm",
                 "🌐 Web & Media AI", "👥 Nhóm & Gọi", "☁️ Plus & Cloud"])

def _friendly_ai_error(exc):
    """Turn common provider failures into actionable Vietnamese diagnostics."""
    status = getattr(exc, "status_code", None)
    detail = str(exc)
    lowered = detail.lower()
    if status == 401 or "invalid_api_key" in lowered or "unauthorized" in lowered:
        return "API key không hợp lệ hoặc đã bị thu hồi. Tạo khóa mới tại https://console.groq.com/keys và cập nhật Streamlit Secrets. Không gửi khóa vào chat/GitHub."
    if status == 429 or "rate_limit" in lowered or "quota" in lowered:
        return "Groq đang giới hạn tốc độ hoặc tài khoản đã hết hạn mức. Chờ rồi thử lại, hoặc kiểm tra Limits/Usage trong Groq Console."
    if status == 404 or "model_not_found" in lowered or "model not found" in lowered or "decommissioned" in lowered:
        return 'Model đã bị ngừng hỗ trợ hoặc không khả dụng cho tài khoản. Đặt GROQ_MODEL = "openai/gpt-oss-120b" trong Streamlit Secrets rồi khởi động lại app. Chi tiết: ' + detail[:500]
    if status in (400, 403):
        return f"Groq từ chối yêu cầu (HTTP {status}). Kiểm tra tên model, quyền truy cập và tham số API. Chi tiết: {detail[:500]}"
    return f"Chưa thể kết nối AI: {detail[:700]}. Kiểm tra API key, model, hạn mức và Logs của Streamlit."


# ---------- Chat ----------
with pages[0]:
    st.subheader("Trợ lý học tập của bạn")
    st.caption("Hỏi về Toán, Văn, Anh, Lý, Hóa, Sinh, Sử, Địa, ngoại ngữ, kỹ năng và kiến thức đời sống.")
    # Streamlit Cloud Secrets first, then environment/.env for local development.
    def setting(name, default=""):
        try:
            value = st.secrets.get(name, None)
            if value is not None and str(value).strip():
                return str(value).strip()
        except Exception:
            pass
        return os.getenv(name, default).strip()

    api_key = setting("GROQ_API_KEY") or setting("OPENAI_API_KEY")
    provider = "Groq" if setting("GROQ_API_KEY") else ("OpenAI" if setting("OPENAI_API_KEY") else "")
    configured_model = setting("GROQ_MODEL", "openai/gpt-oss-120b") if provider == "Groq" else setting("OPENAI_MODEL", "gpt-4.1-mini")
    # Resolve retired Groq IDs at runtime too, so stale Secrets cannot keep breaking chat.
    model = configured_model
    if provider == "Groq" and model in {"llama-3.3-70b-versatile", "llama-3.1-8b-instant", "meta-llama/llama-4-scout-17b-16e-instruct"}:
        model = {"llama-3.3-70b-versatile": "openai/gpt-oss-120b", "llama-3.1-8b-instant": "openai/gpt-oss-20b", "meta-llama/llama-4-scout-17b-16e-instruct": "openai/gpt-oss-120b"}[model]
    if not api_key:
        st.warning("Chưa cấu hình API. Tạo GROQ_API_KEY tại console.groq.com/keys rồi thêm vào Streamlit Secrets để bật AI.")
    else:
        st.caption(f"Đang dùng AI qua {provider} · model: {model}")
        if st.button("🔌 Kiểm tra kết nối AI", key="test_ai_connection"):
            try:
                with st.spinner("Đang kiểm tra kết nối AI..."):
                    checked_model, check_text = test_ai_connection()
                st.success(f"Kết nối thành công · model: {checked_model}")
                st.caption(check_text)
            except Exception as check_exc:
                st.error(_friendly_ai_error(check_exc))
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"], avatar="🎓" if message["role"] == "assistant" else "🙂"):
            st.markdown(message["content"])
    uploaded = st.file_uploader("📷 Đính kèm ảnh bài tập (tùy chọn)", type=["png", "jpg", "jpeg", "webp"], key="chat_image")
    if uploaded:
        st.image(uploaded, caption="Ảnh đính kèm sẽ được gửi cho model vision khi bạn đặt câu hỏi.", width=300)
    use_web = st.checkbox("🌐 Tra cứu Internet và đính kèm nguồn khi trả lời", value=False, key="chat_use_web")
    prompt = st.chat_input("Nhập câu hỏi hoặc bài tập bạn muốn giải...")
    if prompt:
        augmented_prompt = prompt
        image_context = ""
        web_context = ""
        if uploaded:
            try:
                with st.spinner("Đang đọc ảnh bài tập bằng AI vision..."):
                    image_context = analyze_image(uploaded.getvalue(), uploaded.type or "image/png", prompt)
                augmented_prompt += "\n\n[Phân tích ảnh đính kèm từ vision]:\n" + image_context
            except Exception as image_exc:
                st.warning(f"Không đọc được ảnh bằng model vision: {image_exc}. Hãy cấu hình model vision tương thích.")
        if use_web:
            try:
                with st.spinner("Đang tìm nguồn trên Internet..."):
                    web_data = tavily_search(prompt, 5)
                source_lines = []
                for item in web_data.get("results", [])[:5]:
                    source_lines.append(f"- {item.get('title','Nguồn')} | {item.get('url','')} | {item.get('content','')[:1200]}")
                web_context = "\n".join(source_lines)
                if web_context:
                    augmented_prompt += "\n\n[Thông tin tìm kiếm web — hãy đối chiếu, nêu rõ giới hạn và không xem snippet là bằng chứng tuyệt đối]:\n" + web_context
            except Exception as web_exc:
                st.warning(f"Không tìm được web: {web_exc}")
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🙂"):
            st.markdown(prompt)
            if uploaded: st.image(uploaded, width=220)
        answer = None
        if api_key:
            try:
                system_prompt = (
                    "Bạn là P.H.U.C.S, trợ lý học tập đa môn, thân thiện và có trách nhiệm. "
                    "Trả lời bằng ngôn ngữ người dùng đang dùng. Với Toán và khoa học, nêu dữ kiện, "
                    "công thức, đơn vị, các bước suy luận và tự kiểm tra kết quả khi có thể. Với bài trắc nghiệm, "
                    "giải thích vì sao đáp án đúng và vì sao lựa chọn gần đúng có thể sai. Với ngôn ngữ, giải thích "
                    "ngữ pháp và sắc thái dùng từ. Phân biệt dữ kiện đã xác minh với giả định/chưa chắc chắn; "
                    "nếu thiếu dữ kiện, hỏi lại thay vì bịa. Không bịa nguồn hoặc trích dẫn. Khi có kết quả web, "
                    "chỉ dùng nó làm manh mối và gắn nguồn phù hợp. Với y tế/pháp luật/tài chính, đưa thông tin "
                    "giáo dục thận trọng, không thay thế chuyên gia."
                )
                msgs = [{"role": "system", "content": system_prompt}]
                recent_messages = st.session_state.messages[-20:]
                first_index = len(st.session_state.messages) - len(recent_messages)
                msgs += [{"role": m["role"], "content": (augmented_prompt if first_index + i == len(st.session_state.messages)-1 and m["role"] == "user" else m["content"])} for i, m in enumerate(recent_messages)]
                with st.chat_message("assistant", avatar="🎓"):
                    with st.spinner("P.H.U.C.S đang suy nghĩ..."):
                        response, model_used = chat_completion(msgs)
                        answer = response.choices[0].message.content or "Mình nhận được phản hồi rỗng từ model. Bạn thử diễn đạt lại câu hỏi nhé."
                        if model_used != model:
                            st.info(f"Tự chuyển sang model đang được hỗ trợ: {model_used}")
                        if web_context:
                            answer += "\n\n### Nguồn tham khảo từ tìm kiếm web\n" + "\n".join([f"- [{item.get('title') or 'Nguồn tham khảo'}]({item.get('url')})" for item in web_data.get("results", [])[:5] if item.get("url")])
                        st.markdown(answer)
            except Exception as e:
                answer = _friendly_ai_error(e)
                with st.chat_message("assistant", avatar="🎓"):
                    st.error(answer)
        else:
            answer = ("Mình đã nhận được câu hỏi! Để bật AI, hãy tạo khóa Groq tại "
                      "https://console.groq.com/keys rồi thêm `GROQ_API_KEY` vào Streamlit Secrets. "
                      "Sau khi cấu hình, mình sẽ giải thích từng bước và ưu tiên độ chính xác.")
            with st.chat_message("assistant", avatar="🎓"):
                st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        if not st.session_state.get("active_chat"):
            title = prompt[:48] + ("…" if len(prompt) > 48 else "")
            import json
            with db() as con:
                cur = con.execute("INSERT INTO chats(user_id,title,messages,updated_at) VALUES(?,?,?,?)",
                                  (uid, title, json.dumps(st.session_state.messages, ensure_ascii=False),
                                   datetime.now().isoformat(timespec="seconds")))
                st.session_state.active_chat = cur.lastrowid
        else:
            import json
            with db() as con:
                con.execute("UPDATE chats SET messages=?,updated_at=? WHERE id=? AND user_id=?",
                            (json.dumps(st.session_state.messages, ensure_ascii=False),
                             datetime.now().isoformat(timespec="seconds"), st.session_state.active_chat, uid))
        st.rerun()
    with st.expander("＋ Công cụ bổ sung"):
        st.write("📷 Ảnh bài tập: tải ảnh lên, nhập câu hỏi rồi gửi; P.H.U.C.S sẽ gọi model vision nếu đã cấu hình.")
        st.write("🎙️ Voice chat: mở tab Web & Media AI → Giọng nói để ghi âm/chuyển chữ và đọc câu trả lời.")
        st.write("🎨 Tạo ảnh / 🎬 video / 🎵 nhạc: mở tab Web & Media AI và cấu hình API tương ứng trong Secrets.")
        st.write("🌐 Tìm kiếm Internet: bật ô 'Tra cứu Internet' phía trên ô chat; câu trả lời sẽ đính kèm liên kết nguồn nếu Tavily đã cấu hình.")

# ---------- Timer ----------
with pages[1]:
    st.subheader("⏱️ Đồng hồ tập trung")
    # Force Streamlit to rerun once per second while timer is active.
    if st.session_state.get("timer_running"):
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=1000, key="phucs_timer_refresh")
        except Exception:
            st.caption("Cài streamlit-autorefresh trong requirements.txt để đồng hồ tự cập nhật mỗi giây.")
    subjects = ["Ngữ Văn", "Toán học", "Vật lí", "Hóa học", "Sinh học", "Tiếng Anh", "Lịch sử", "Địa lí", "Tự đặt tên"]
    subject = st.selectbox("Môn học", subjects)
    custom_subject = st.text_input("Tên môn học tùy chỉnh") if subject == "Tự đặt tên" else ""
    subject_name = custom_subject.strip() or subject
    if "timer_started_at" not in st.session_state:
        st.session_state.timer_started_at = None
        st.session_state.timer_elapsed = 0
        st.session_state.timer_running = False
    if st.session_state.timer_running and st.session_state.timer_started_at:
        elapsed = st.session_state.timer_elapsed + int(time.time() - st.session_state.timer_started_at)
    else:
        elapsed = st.session_state.timer_elapsed
    hh, rem = divmod(elapsed, 3600); mm, ss = divmod(rem, 60)
    st.markdown(f"<div class='hero' style='text-align:center'><div style='font-size:3.5rem;font-weight:900;color:#d94f83;font-variant-numeric:tabular-nums'>{hh:02}:{mm:02}:{ss:02}</div><div class='small-muted'>Thời gian học tập trung</div></div>", unsafe_allow_html=True)
    b1,b2,b3,b4 = st.columns(4)
    with b1:
        if st.button("▶ Bắt đầu", type="primary", use_container_width=True) and not st.session_state.timer_running:
            st.session_state.timer_started_at = time.time()
            st.session_state.timer_running = True
            st.rerun()
    with b2:
        if st.button("Ⅱ Tạm dừng", use_container_width=True) and st.session_state.timer_running:
            st.session_state.timer_elapsed = elapsed
            st.session_state.timer_started_at = None
            st.session_state.timer_running = False
            st.rerun()
    with b3:
        if st.button("↺ Đặt lại", use_container_width=True):
            st.session_state.timer_elapsed = 0
            st.session_state.timer_started_at = time.time() if st.session_state.timer_running else None
            st.rerun()
    with b4:
        if st.button("💾 Lưu phiên", use_container_width=True):
            with db() as con:
                con.execute("INSERT INTO study_sessions(user_id,subject,seconds,saved_at) VALUES(?,?,?,?)",
                            (uid, subject_name, elapsed, datetime.now().isoformat(timespec="seconds")))
            st.success("Đã lưu phiên học.")
    if st.session_state.timer_running:
        st.caption("⏱️ Đồng hồ đang tự cập nhật mỗi giây. Chọn Tạm dừng để dừng đếm.")
    with db() as con:
        sessions = con.execute("SELECT subject,seconds,saved_at FROM study_sessions WHERE user_id=? ORDER BY id DESC LIMIT 20", (uid,)).fetchall()
    st.markdown("#### Lịch sử học gần đây")
    if sessions:
        for s in sessions:
            st.write(f"• {s['saved_at'][:10]} · **{s['subject']}** · {s['seconds']//3600:02}:{(s['seconds']%3600)//60:02}:{s['seconds']%60:02}")
    else:
        st.info("Chưa có phiên học được lưu.")

# ---------- Calendar ----------
with pages[2]:
    st.subheader("📅 Lịch & Sự kiện")
    chosen_date = st.date_input("Chọn ngày", value=date.today(), format="DD/MM/YYYY")
    with st.form("event_form", clear_on_submit=True):
        ev_title = st.text_input("Tên sự kiện")
        ev_cat = st.selectbox("Phân loại", ["Sinh nhật", "Kỷ niệm", "Thi cử", "Quan trọng", "Khác"])
        ev_date = st.date_input("Ngày diễn ra", value=chosen_date, format="DD/MM/YYYY")
        ev_submit = st.form_submit_button("＋ Thêm sự kiện", type="primary")
    if ev_submit:
        if ev_title.strip():
            with db() as con:
                con.execute("INSERT INTO events(user_id,title,category,event_date) VALUES(?,?,?,?)",
                            (uid, ev_title.strip(), ev_cat, ev_date.isoformat()))
            st.success("Đã thêm sự kiện.")
            st.rerun()
        else:
            st.error("Hãy nhập tên sự kiện.")
    with db() as con:
        events = con.execute("SELECT id,title,category FROM events WHERE user_id=? AND event_date=? ORDER BY id",
                             (uid, chosen_date.isoformat())).fetchall()
    st.markdown(f"#### Sự kiện ngày {chosen_date.strftime('%d/%m/%Y')}")
    if not events:
        st.info("Không có sự kiện trong ngày này.")
    for ev in events:
        c1,c2 = st.columns([5,1])
        c1.write(f"**{ev['title']}** · {ev['category']}")
        if c2.button("Xóa", key=f"del_ev_{ev['id']}"):
            with db() as con: con.execute("DELETE FROM events WHERE id=? AND user_id=?", (ev["id"],uid))
            st.rerun()

# ---------- Todo ----------
with pages[3]:
    st.subheader("✅ To-do List")
    todo_date = st.date_input("Ngày thực hiện", value=date.today(), format="DD/MM/YYYY", key="todo_date")
    with st.form("todo_form", clear_on_submit=True):
        task = st.text_input("Nhiệm vụ mới", placeholder="Ví dụ: Ôn 20 từ vựng IELTS")
        add_task = st.form_submit_button("＋ Thêm nhiệm vụ", type="primary")
    if add_task and task.strip():
        with db() as con:
            con.execute("INSERT INTO todos(user_id,task,due_date,done) VALUES(?,?,?,0)",
                        (uid,task.strip(),todo_date.isoformat()))
        st.rerun()
    with db() as con:
        todos = con.execute("SELECT id,task,done FROM todos WHERE user_id=? AND due_date=? ORDER BY done,id",
                            (uid,todo_date.isoformat())).fetchall()
    st.markdown("#### Chưa hoàn thành")
    for t in [x for x in todos if not x["done"]]:
        c1,c2 = st.columns([6,1])
        c1.write("✕ " + t["task"])
        if c2.button("✓", key=f"done_{t['id']}"):
            with db() as con: con.execute("UPDATE todos SET done=1 WHERE id=? AND user_id=?", (t["id"],uid))
            st.rerun()
    st.markdown("#### Đã hoàn thành")
    for t in [x for x in todos if x["done"]]:
        c1,c2 = st.columns([6,1])
        c1.markdown(f"~~{t['task']}~~")
        if c2.button("↩", key=f"undo_{t['id']}"):
            with db() as con: con.execute("UPDATE todos SET done=0 WHERE id=? AND user_id=?", (t["id"],uid))
            st.rerun()
    if not todos:
        st.info("Chưa có nhiệm vụ nào trong ngày này.")

# ---------- Notes and drawing ----------
with pages[4]:
    st.subheader("📝 Note & Studio Pro")
    mode = st.radio("Chế độ", ["Trình soạn thảo văn bản", "Bảng vẽ Studio Pro"], horizontal=True)
    if mode == "Trình soạn thảo văn bản":
        note_title = st.text_input("Tiêu đề ghi chú", key="rich_note_title")
        st.caption("Trình soạn thảo hỗ trợ định dạng văn bản, phông chữ, màu chữ, highlight, danh sách và ký hiệu học thuật nếu streamlit-quill được cài.")
        editor_html = ""
        try:
            from streamlit_quill import st_quill
            toolbar = [[{"font": []}, {"size": ["small", False, "large", "huge"]}],
                       ["bold", "italic", "underline", "strike"],
                       [{"color": []}, {"background": []}],
                       [{"script": "sub"}, {"script": "super"}],
                       [{"header": [1, 2, 3, False]}],
                       [{"list": "ordered"}, {"list": "bullet"}],
                       [{"align": []}], ["blockquote", "code-block", "link"], ["clean"]]
            editor_html = st_quill(placeholder="Soạn ghi chú, công thức, bài học...", html=True, toolbar=toolbar, key="rich_note_editor") or ""
        except Exception:
            st.warning("Trình soạn thảo nâng cao chưa tải được; đang dùng chế độ văn bản cơ bản. Kiểm tra streamlit-quill trong requirements.txt.")
            editor_html = st.text_area("Nội dung ghi chú", height=260, placeholder="Có thể nhập công thức: H₂O, v = s/t, x², ∑, √, π, Δ, →, ⇌, °C...", key="basic_note_body")
        with st.expander("∑ Ký hiệu Toán – Lý – Hóa – Sinh"):
            symbols = ["α", "β", "γ", "Δ", "θ", "λ", "μ", "π", "Σ", "Ω", "√", "∛", "∞", "≈", "≠", "≤", "≥", "±", "×", "÷", "∑", "∫", "∂", "∇", "→", "⇌", "°", "℃", "m/s", "mol", "H₂O", "CO₂", "Na⁺", "SO₄²⁻", "x²", "x₁", "Fe³⁺", "DNA", "RNA"]
            st.write("　".join(f"`{x}`" for x in symbols))
            st.caption("Có thể sao chép ký hiệu ở trên và dán vào ghi chú. Với Quill, dùng các nút sub/super để định dạng chỉ số.")
        if st.button("💾 Lưu ghi chú", type="primary", key="save_rich_note"):
            if note_title.strip() and str(editor_html).strip():
                with db() as con:
                    con.execute("INSERT INTO notes(user_id,title,body,created_at) VALUES(?,?,?,?)", (uid, note_title.strip(), str(editor_html), datetime.now().isoformat(timespec="seconds")))
                st.success("Đã lưu ghi chú.")
                st.rerun()
            else:
                st.error("Vui lòng nhập tiêu đề và nội dung.")
    else:
        st.caption("Studio Pro: bút bi, bút cọ, bút kim, highlight, tẩy, đường liền/nét đứt, hình chữ nhật, hình tròn, tam giác và tải PNG.")
        st.components.v1.html(r"""<!doctype html><html><head><style>
        body{font-family:Arial;background:#fff4f8;margin:0;padding:10px;color:#74314f} .toolbar{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:9px;align-items:center}
        button,select{border:1px solid #e8a7c2;background:white;border-radius:8px;padding:7px;color:#74314f;font-weight:600} canvas{display:block;width:100%;height:auto;background:#fff;border:1px solid #e8a7c2;border-radius:12px;touch-action:none}
        </style></head><body><div class="toolbar">
        <select id="tool"><option value="pen">Bút bi</option><option value="brush">Bút cọ</option><option value="fine">Bút kim</option><option value="highlighter">Highlight</option><option value="eraser">Tẩy</option><option value="line">Đường thẳng liền</option><option value="dashed">Đường nét đứt</option><option value="rect">Hình chữ nhật</option><option value="circle">Hình tròn</option><option value="triangle">Tam giác</option></select>
        <label>Màu <input id="color" type="color" value="#d94f83"></label><label>Nét <input id="width" type="range" min="1" max="30" value="4"></label>
        <button id="undo">↶ Hoàn tác</button><button id="clear">🗑 Tẩy hết</button><button id="download">⬇ Tải PNG</button></div>
        <canvas id="pad" width="1200" height="620"></canvas><script>
        const c=document.getElementById('pad'),ctx=c.getContext('2d');ctx.lineCap='round';ctx.lineJoin='round';ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height);let down=false,start=null,last=null,history=[];
        function save(){history.push(ctx.getImageData(0,0,c.width,c.height));if(history.length>30)history.shift()} save();
        function pos(e){let r=c.getBoundingClientRect();return{x:(e.clientX-r.left)*c.width/r.width,y:(e.clientY-r.top)*c.height/r.height}}
        function style(){let t=document.getElementById('tool').value;ctx.globalCompositeOperation=t==='eraser'?'destination-out':'source-over';ctx.strokeStyle=document.getElementById('color').value;ctx.lineWidth=+document.getElementById('width').value;ctx.globalAlpha=t==='highlighter'?.24:1;if(t==='brush')ctx.lineWidth*=2.5;if(t==='fine')ctx.lineWidth=Math.min(ctx.lineWidth,2);ctx.setLineDash(t==='dashed'?[12,8]:[])}
        function shape(a,b,t){style();ctx.beginPath();if(t==='line'||t==='dashed'){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y)}else if(t==='rect'){ctx.rect(a.x,a.y,b.x-a.x,b.y-a.y)}else if(t==='circle'){let r=Math.hypot(b.x-a.x,b.y-a.y);ctx.arc(a.x,a.y,r,0,Math.PI*2)}else if(t==='triangle'){ctx.moveTo((a.x+b.x)/2,a.y);ctx.lineTo(a.x,b.y);ctx.lineTo(b.x,b.y);ctx.closePath()}ctx.stroke();ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.setLineDash([])}
        c.addEventListener('pointerdown',e=>{save();down=true;start=last=pos(e);c.setPointerCapture(e.pointerId);if(['line','dashed','rect','circle','triangle'].includes(document.getElementById('tool').value)){} });
        c.addEventListener('pointermove',e=>{if(!down)return;let p=pos(e),t=document.getElementById('tool').value;if(['line','dashed','rect','circle','triangle'].includes(t)){let snap=history[history.length-1];ctx.putImageData(snap,0,0);shape(start,p,t)}else{style();ctx.beginPath();ctx.moveTo(last.x,last.y);ctx.lineTo(p.x,p.y);ctx.stroke();ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';last=p}});
        c.addEventListener('pointerup',()=>{down=false;start=last=null;ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.setLineDash([])});
        document.getElementById('clear').onclick=()=>{save();ctx.clearRect(0,0,c.width,c.height);ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height)};
        document.getElementById('undo').onclick=()=>{if(history.length>1){history.pop();ctx.putImageData(history[history.length-1],0,0)}};
        document.getElementById('download').onclick=()=>{let a=document.createElement('a');a.download='phucs-studio.png';a.href=c.toDataURL('image/png');a.click()};
        </script></body></html>""", height=720, scrolling=True)
    st.markdown("#### Kho lưu trữ ghi chú")
    with db() as con:
        notes = con.execute("SELECT id,title,body,created_at FROM notes WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    if not notes:
        st.caption("Chưa có ghi chú được lưu.")
    for n in notes:
        with st.expander(f"🗒️ {n['title']} · {n['created_at'][:10]}"):
            # Render only a small allowlist of formatting tags saved by the rich-text editor.
            try:
                import bleach
                safe_html = bleach.clean(n['body'], tags=['p','br','strong','b','em','i','u','s','ol','ul','li','h1','h2','h3','blockquote','pre','code','span','div','sub','sup','a'], attributes={'a':['href','target'], 'span':['style'], 'div':['style']}, protocols=['http','https','mailto'])
                st.markdown(safe_html, unsafe_allow_html=True)
            except Exception:
                st.text(n['body'])
            if st.button("Xóa ghi chú", key=f"delete_note_{n['id']}"):
                with db() as con: con.execute("DELETE FROM notes WHERE id=? AND user_id=?", (n['id'],uid))
                st.rerun()

# ---------- Charts ----------
with pages[5]:
    st.subheader("📊 Tạo biểu đồ")
    st.caption("Nhập dữ liệu theo từng dòng, mỗi dòng gồm nhãn và giá trị, phân cách bằng dấu phẩy.")
    chart_type = st.selectbox("Loại biểu đồ", ["Biểu đồ cột dọc", "Biểu đồ thanh ngang", "Biểu đồ đường", "Biểu đồ miền", "Biểu đồ tròn / quạt"])
    data_text = st.text_area("Dữ liệu", value="Toán,8\nVăn,7\nTiếng Anh,9", height=120)
    if st.button("Vẽ biểu đồ", type="primary"):
        import pandas as pd
        rows = []
        for line in data_text.splitlines():
            try:
                label, value = line.rsplit(",",1)
                rows.append({"Mục":label.strip(),"Giá trị":float(value.strip())})
            except ValueError:
                pass
        if rows:
            frame = pd.DataFrame(rows).set_index("Mục")
            if chart_type == "Biểu đồ cột dọc": st.bar_chart(frame)
            elif chart_type == "Biểu đồ thanh ngang":
                try:
                    import plotly.express as px
                    fig = px.bar(pd.DataFrame(rows), x="Giá trị", y="Mục", orientation="h", color="Mục", title="Biểu đồ thanh ngang")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.dataframe(pd.DataFrame(rows).sort_values("Giá trị"), use_container_width=True)
                    st.caption("Cài plotly để hiển thị biểu đồ thanh ngang tương tác.")
            elif chart_type == "Biểu đồ đường": st.line_chart(frame)
            elif chart_type == "Biểu đồ miền": st.area_chart(frame)
            else: st.vega_lite_chart(
                pd.DataFrame(rows),
                {"mark":{"type":"arc","innerRadius":35},
                 "encoding":{"theta":{"field":"Giá trị","type":"quantitative"},
                             "color":{"field":"Mục","type":"nominal"},
                             "tooltip":[{"field":"Mục"},{"field":"Giá trị"}]}}
            )
        else:
            st.error("Không đọc được dữ liệu. Hãy dùng định dạng Nhãn,Giá trị.")

# ---------- Games ----------
with pages[6]:
    st.subheader("🎮 Góc giải trí lành mạnh")
    st.markdown("<div class='hero'><h3>🌸 Học vui mỗi ngày</h3><p>Chọn một thử thách ngắn để nạp lại năng lượng sau khi học.</p><div style='font-size:2rem;letter-spacing:.25rem'>🧩 🎯 🧠 🚀 🪄 🐼 🌈 🎨</div></div>", unsafe_allow_html=True)
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=150, caption="Mascot P.H.U.C.S — chinh phục tri thức")
    games = {
        "Đố vui kiến thức": "Trả lời câu hỏi kiến thức tổng hợp.",
        "Đoán số": "Đoán một số từ 1 đến 20.",
        "Thử thách bảng cửu chương": "Luyện tính nhẩm.",
        "Từ vựng nhanh": "Ôn từ vựng ngoại ngữ.",
        "Ghi nhớ dãy số": "Rèn trí nhớ ngắn hạn.",
        "Câu đố logic": "Thử sức với suy luận."
    }
    game = st.selectbox("Trò chơi", list(games.keys()) + [
        "Sudoku mini", "Tìm từ khác biệt", "Đố cờ", "Quiz lịch sử", "Quiz địa lý",
        "Đố khoa học", "Nối từ", "Anagram", "Đoán thành ngữ", "Tính nhẩm 60 giây",
        "Flashcard", "Wordle mini", "Tìm cặp giống nhau", "Đố mẹo", "Quiz tiếng Anh",
        "Quiz IELTS", "Quiz HSK", "Đuổi hình bắt chữ", "Cờ caro", "Kéo búa bao",
        "Trắc nghiệm âm nhạc", "Đố thiên văn", "Thử thách chính tả", "Tìm đường mê cung",
        "Phản xạ màu sắc", "Ô chữ mini", "Đố toán", "Quiz sinh học"
    ])
    st.info(games.get(game, "Trò chơi được liệt kê trong lộ trình mở rộng; phiên bản hiện tại mới có một số trò chơi mẫu.") )
    if game == "Đoán số":
        import random
        if "secret_number" not in st.session_state: st.session_state.secret_number = random.randint(1,20)
        guess = st.number_input("Số bạn đoán", min_value=1, max_value=20, step=1)
        if st.button("Kiểm tra"):
            if guess == st.session_state.secret_number:
                st.success("Chính xác! Bạn giỏi lắm 🌸")
                st.session_state.secret_number = random.randint(1,20)
            elif guess < st.session_state.secret_number: st.warning("Thử số lớn hơn nhé.")
            else: st.warning("Thử số nhỏ hơn nhé.")
    elif game == "Thử thách bảng cửu chương":
        import random
        if "math_question" not in st.session_state:
            a,b=random.randint(2,12),random.randint(2,12); st.session_state.math_question=(a,b)
        a,b=st.session_state.math_question
        st.write(f"**{a} × {b} = ?**")
        ans=st.number_input("Đáp án", step=1, key="math_answer")
        if st.button("Chấm đáp án"):
            if ans==a*b: st.success("Đúng rồi!"); st.session_state.math_question=(random.randint(2,12),random.randint(2,12))
            else: st.error("Chưa đúng, thử lại nhé.")
    else:
        st.markdown(f"### 🌈 Thử thách: {game}")
        st.caption("Các trò chơi mẫu dùng câu hỏi tương tác để bạn có thể chơi ngay. Một số trò chuyên biệt sẽ được phát triển sâu hơn ở các phiên bản sau.")
        quiz_bank = [
            ("Hành tinh nào gần Mặt Trời nhất?", ["Sao Thủy", "Trái Đất", "Sao Hỏa"], "Sao Thủy"),
            ("Tích của 7 × 8 là bao nhiêu?", ["54", "56", "64"], "56"),
            ("Công thức hóa học của nước là gì?", ["CO₂", "H₂O", "O₂"], "H₂O"),
            ("Từ tiếng Anh 'library' nghĩa là gì?", ["Hiệu sách", "Thư viện", "Phòng thí nghiệm"], "Thư viện"),
            ("Một tam giác có tổng ba góc bằng bao nhiêu?", ["90°", "180°", "360°"], "180°"),
            ("Cơ quan nào bơm máu trong cơ thể người?", ["Phổi", "Tim", "Gan"], "Tim"),
        ]
        if st.session_state.get("quiz_game_name") != game:
            st.session_state.quiz_game_name = game
            st.session_state.quiz_game_item = random.choice(quiz_bank)
        q, opts, correct = st.session_state.quiz_game_item
        st.markdown(f"<div class='hero'><div style='font-size:2.4rem'>🧠 ✨ 🎯</div><h3>{q}</h3></div>", unsafe_allow_html=True)
        answer_choice = st.radio("Chọn đáp án", opts, key=f"quiz_answer_{game}")
        if st.button("Kiểm tra đáp án", key=f"quiz_check_{game}", type="primary"):
            if answer_choice == correct:
                st.success("Chính xác! Tuyệt vời 🌸")
                st.session_state.quiz_game_item = random.choice([item for item in quiz_bank if item != st.session_state.quiz_game_item])
            else:
                st.error(f"Chưa chính xác. Đáp án đúng là: {correct}")
        if st.button("Câu hỏi mới", key=f"quiz_new_{game}"):
            st.session_state.quiz_game_item = random.choice(quiz_bank)
            st.rerun()

# ---------- Lab ----------
with pages[7]:
    st.subheader("🧪 Phòng thí nghiệm ảo — 30 mô phỏng")
    lab_names = [
      "01. Quỹ đạo hành tinh", "02. Pha Mặt Trăng", "03. Hệ Mặt Trời theo tỷ lệ", "04. Trọng lực và khối lượng",
      "05. Chuyển động thẳng đều", "06. Chuyển động nhanh dần đều", "07. Ném ngang", "08. Dao động con lắc",
      "09. Sóng âm", "10. Sóng cơ", "11. Định luật Ohm", "12. Mạch điện nối tiếp/song song",
      "13. Thấu kính hội tụ", "14. Phản xạ ánh sáng", "15. Khúc xạ ánh sáng", "16. Lực đẩy Archimedes",
      "17. Áp suất chất lỏng", "18. Nhiệt độ và truyền nhiệt", "19. Phản ứng hóa học và bảo toàn khối lượng", "20. pH dung dịch",
      "21. Cấu tạo nguyên tử", "22. Di truyền Mendel", "23. Hệ sinh thái", "24. Phân bào khái niệm",
      "25. Đồ thị hàm số bậc hai", "26. Tam giác vuông", "27. Đường tròn lượng giác", "28. Xác suất gieo xúc xắc",
      "29. Thống kê và phân phối", "30. Hình học 3D — thể tích"
    ]
    lab = st.selectbox("Chọn mô phỏng", lab_names)
    st.info("Các mô phỏng dưới đây dùng công thức giáo dục đơn giản để minh họa, không thay thế mô hình nghiên cứu chuyên ngành.")
    if "01." in lab or "02." in lab or "03." in lab or "04." in lab:
        import numpy as np, pandas as pd
        if "01." in lab:
            radius=st.slider("Bán kính quỹ đạo (đơn vị tùy chọn)",1.0,10.0,4.0); angle=np.linspace(0,2*np.pi,240)
            st.line_chart(pd.DataFrame({"x":radius*np.cos(angle),"y":radius*np.sin(angle)})); st.caption("Quỹ đạo tròn minh họa, không phải mô hình N-body chính xác.")
        elif "02." in lab:
            phase=st.slider("Pha Mặt Trăng (%)",0,100,50); st.progress(phase/100); st.write("Pha minh họa:", "Trăng non" if phase<12 else "Lưỡi liềm" if phase<38 else "Bán nguyệt" if phase<62 else "Trăng khuyết/gần tròn" if phase<88 else "Trăng tròn")
        elif "03." in lab:
            scale=st.slider("Hệ số tỷ lệ khoảng cách",0.1,3.0,1.0,0.1); st.bar_chart(pd.DataFrame({"Khoảng cách minh họa": [0,0.39*scale,0.72*scale,1*scale,1.52*scale,5.2*scale,9.5*scale]},index=["Mặt Trời","Thủy","Kim","Trái Đất","Hỏa","Mộc","Thổ"]))
        else:
            m=st.slider("Khối lượng (kg)",1.0,100.0,10.0); g=st.slider("Gia tốc trọng trường (m/s²)",0.1,25.0,9.81); st.metric("Trọng lượng F = mg",f"{m*g:.2f} N")
    elif "05." in lab or "06." in lab or "07." in lab:
        import numpy as np, pandas as pd
        v=st.slider("Vận tốc ban đầu (m/s)",0.0,40.0,5.0); a=st.slider("Gia tốc (m/s²)",-10.0,10.0,2.0); tmax=st.slider("Thời gian mô phỏng (s)",1,30,10); t=np.linspace(0,tmax,101)
        if "05." in lab: x=v*t; st.caption("s = v·t")
        elif "06." in lab: x=v*t+0.5*a*t*t; st.caption("s = v₀t + ½at²")
        else: angle=st.slider("Góc ném (độ)",5,85,45); g=9.81; rad=np.deg2rad(angle); x=v*np.cos(rad)*t; y=v*np.sin(rad)*t-0.5*g*t*t; st.line_chart(pd.DataFrame({"Độ cao (m)":y[y>=0]},index=x[:len(y[y>=0])]))
        if "07." not in lab: st.line_chart(pd.DataFrame({"Quãng đường (m)":x},index=t))
    elif "08." in lab:
        import numpy as np,pandas as pd
        L=st.slider("Chiều dài con lắc (m)",0.1,5.0,1.0); theta=st.slider("Góc ban đầu (độ)",1,45,15); t=np.linspace(0,10,300); T=2*np.pi*(L/9.81)**0.5; st.metric("Chu kỳ gần đúng",f"{T:.2f} s"); st.line_chart(pd.DataFrame({"Góc (độ)":theta*np.cos(2*np.pi*t/T)},index=t))
    elif any(x in lab for x in ["09.","10."]):
        import numpy as np,pandas as pd
        freq=st.slider("Tần số (Hz)",1,20,4); amp=st.slider("Biên độ",0.1,5.0,1.0); x=np.linspace(0,4*np.pi,300); st.line_chart(pd.DataFrame({"Li độ":amp*np.sin(freq*x/4)},index=x)); st.metric("Tần số minh họa",f"{freq} Hz")
    elif "11." in lab or "12." in lab:
        voltage=st.slider("Điện áp U (V)",0.0,24.0,12.0); resistance=st.slider("Điện trở R (Ω)",1.0,100.0,6.0); st.metric("Dòng điện I=U/R",f"{voltage/resistance:.3f} A"); st.metric("Công suất P=UI",f"{voltage*voltage/resistance:.2f} W"); st.caption("Mô hình điện trở lý tưởng theo định luật Ohm.")
    elif any(x in lab for x in ["13.","14.","15."]):
        f=st.slider("Tiêu cự / tham số (cm)",5.0,50.0,20.0); d=st.slider("Khoảng cách vật (cm)",5.0,100.0,40.0)
        if "13." in lab:
            denom=(1/f-1/d); st.metric("Khoảng cách ảnh", "Ảnh ở vô cực" if abs(denom)<1e-6 else f"{1/denom:.2f} cm"); st.caption("Công thức thấu kính mỏng 1/f = 1/dᵥ + 1/dₐ, dấu quy ước được giản lược.")
        else:
            n=st.slider("Chiết suất môi trường",1.0,2.5,1.33); angle=st.slider("Góc tới (độ)",0,80,30); import math; val=math.sin(math.radians(angle))/n; st.metric("Góc khúc xạ gần đúng",f"{math.degrees(math.asin(min(1,val))):.1f}°")
    elif "16." in lab or "17." in lab:
        rho=st.slider("Khối lượng riêng (kg/m³)",100.0,13000.0,1000.0); volume=st.slider("Thể tích (lít)",0.1,100.0,2.0); depth=st.slider("Độ sâu (m)",0.0,50.0,3.0); st.metric("Lực đẩy Archimedes",f"{rho*9.81*volume/1000:.2f} N"); st.metric("Áp suất thủy tĩnh",f"{rho*9.81*depth:.0f} Pa")
    elif "18." in lab:
        mass=st.slider("Khối lượng (kg)",0.1,10.0,1.0); c=st.slider("Nhiệt dung riêng (J/kg·K)",100.0,5000.0,4200.0); dt=st.slider("Độ tăng nhiệt (°C)",1,100,20); st.metric("Nhiệt lượng Q=mcΔT",f"{mass*c*dt:,.0f} J")
    elif any(x in lab for x in ["19.","20.","21."]):
        if "19." in lab:
            m1=st.slider("Khối lượng chất phản ứng A (g)",1,100,20); m2=st.slider("Khối lượng chất phản ứng B (g)",1,100,30); st.metric("Tổng khối lượng trước phản ứng",f"{m1+m2} g"); st.caption("Theo mô hình hệ kín, tổng khối lượng được bảo toàn.")
        elif "20." in lab:
            ph=st.slider("pH",0.0,14.0,7.0,0.1); st.metric("Môi trường", "Axit" if ph<7 else "Trung tính" if ph==7 else "Bazơ")
        else:
            protons=st.slider("Số proton",1,20,6); neutrons=st.slider("Số neutron",0,30,6); st.metric("Số khối A = p + n",protons+neutrons); st.caption("Mô hình nguyên tử đơn giản, không biểu diễn quỹ đạo electron thực.")
    elif any(x in lab for x in ["22.","23.","24."]):
        if "22." in lab:
            A=st.selectbox("Kiểu gen bố mẹ",["Aa × Aa","AA × aa","Aa × aa"]); ratios={"Aa × Aa":"25% AA · 50% Aa · 25% aa","AA × aa":"100% Aa","Aa × aa":"50% Aa · 50% aa"}; st.success("Tỷ lệ kiểu gen lý thuyết: "+ratios[A])
        elif "23." in lab:
            sun=st.slider("Năng lượng mặt trời (đơn vị tương đối)",10,100,80); st.metric("Năng lượng đến sinh vật sản xuất",f"{sun} đơn vị"); st.metric("Năng lượng truyền lên bậc tiếp theo (quy tắc 10%)",f"{sun*0.1:.1f} đơn vị")
        else:
            n=st.slider("Số lần phân bào nguyên phân",1,8,3); st.metric("Số tế bào con lý thuyết",2**n)
    elif "25." in lab:
        import numpy as np,pandas as pd
        a=st.slider("Hệ số a",-5.0,5.0,1.0,0.5); b=st.slider("Hệ số b",-10.0,10.0,0.0,0.5); c=st.slider("Hệ số c",-10.0,10.0,0.0,0.5); x=np.linspace(-10,10,201); st.line_chart(pd.DataFrame({"y=ax²+bx+c":a*x*x+b*x+c},index=x))
    elif "26." in lab:
        x=st.slider("Cạnh góc vuông a",1.0,30.0,3.0); y=st.slider("Cạnh góc vuông b",1.0,30.0,4.0); st.metric("Diện tích",f"{x*y/2:.2f} đơn vị²"); st.metric("Cạnh huyền",f"{(x*x+y*y)**.5:.2f}")
    elif "27." in lab:
        import numpy as np,pandas as pd
        ang=st.slider("Góc θ (độ)",-360,360,45); st.metric("sin θ",f"{np.sin(np.deg2rad(ang)):.3f}"); st.metric("cos θ",f"{np.cos(np.deg2rad(ang)):.3f}"); st.metric("tan θ", "không xác định" if abs(np.cos(np.deg2rad(ang)))<1e-8 else f"{np.tan(np.deg2rad(ang)):.3f}")
    elif "28." in lab:
        import random
        sides=st.slider("Số mặt xúc xắc",2,20,6); trials=st.slider("Số lần gieo mô phỏng",10,1000,100,10); values=[random.randint(1,sides) for _ in range(trials)]; import pandas as pd; st.bar_chart(pd.Series(values).value_counts().sort_index()); st.caption("Kết quả mô phỏng ngẫu nhiên; tần suất dao động khi số lần thử nhỏ.")
    elif "29." in lab:
        import numpy as np,pandas as pd
        n=st.slider("Số điểm dữ liệu",10,1000,100,10); mu=st.slider("Trung bình μ",-10.0,10.0,0.0); sigma=st.slider("Độ lệch chuẩn σ",0.1,10.0,1.0); vals=np.random.normal(mu,sigma,n); st.bar_chart(pd.Series(vals).round(0).value_counts().sort_index()); st.metric("Trung bình mẫu",f"{vals.mean():.2f}"); st.metric("Độ lệch chuẩn mẫu",f"{vals.std():.2f}")
    else:
        shape=st.selectbox("Khối hình",["Lập phương","Hộp chữ nhật","Hình trụ","Hình cầu"]); a=st.slider("Kích thước 1 (cm)",1.0,30.0,5.0); b=st.slider("Kích thước 2 / bán kính (cm)",1.0,30.0,4.0); h=st.slider("Chiều cao (cm)",1.0,30.0,6.0); import math
        vol=a**3 if shape=="Lập phương" else a*b*h if shape=="Hộp chữ nhật" else math.pi*b*b*h if shape=="Hình trụ" else 4*math.pi*b**3/3; st.metric("Thể tích",f"{vol:.2f} cm³")

# ---------- Web search, vision, voice and generation ----------
with pages[8]:
    st.subheader("🌐 Tìm kiếm Internet có nguồn & Media AI")
    if INTEGRATION_IMPORT_ERROR:
        st.warning("Một số tích hợp chưa tải được. Ứng dụng vẫn chạy; hãy kiểm tra file phucs_integrations.py và requirements.txt. Chi tiết lỗi: " + str(INTEGRATION_IMPORT_ERROR))
    mode = st.radio("Công cụ", ["Tìm kiếm Internet", "Phân tích ảnh bằng AI", "Giọng nói", "Tạo ảnh AI", "Tạo video AI", "Tạo nhạc AI"], horizontal=True)
    if mode == "Tìm kiếm Internet":
        query = st.text_input("Bạn muốn tìm thông tin gì?", placeholder="Ví dụ: định luật Newton nguồn giáo dục đáng tin cậy")
        count = st.slider("Số nguồn", 3, 10, 5)
        if st.button("🔎 Tìm kiếm và trích dẫn", type="primary", key="tavily_search_btn"):
            if not query.strip():
                st.warning("Hãy nhập nội dung cần tìm.")
            else:
                try:
                    with st.spinner("Đang tìm trên Internet..."):
                        result = tavily_search(query.strip(), count)
                    if result.get("answer"):
                        st.markdown("#### Tóm tắt tìm kiếm")
                        st.write(result["answer"])
                    st.markdown("#### Nguồn tham khảo")
                    for i, item in enumerate(result.get("results", []), 1):
                        st.markdown(f"**[{i}] [{item.get('title') or 'Nguồn tham khảo'}]({item.get('url')})**")
                        st.write(item.get("content", "")[:900])
                        st.caption(f"Điểm liên quan: {item.get('score', '—')} · Hãy mở nguồn để xác minh nội dung.")
                except Exception as exc:
                    st.error(str(exc))
        st.caption("Cần TAVILY_API_KEY. Kết quả tìm kiếm có thể thiếu hoặc sai; hãy mở và kiểm chứng nguồn gốc.")
    elif mode == "Phân tích ảnh bằng AI":
        image_file = st.file_uploader("Tải ảnh bài tập, sơ đồ hoặc tài liệu", type=["png","jpg","jpeg","webp"], key="vision_image")
        question = st.text_area("Bạn muốn AI làm gì với ảnh?", value="Đọc nội dung ảnh và giải thích từng bước.")
        if image_file: st.image(image_file, width=420)
        if st.button("🧠 Phân tích ảnh", type="primary", key="analyze_img_btn"):
            if not image_file: st.warning("Hãy tải ảnh lên trước.")
            else:
                try:
                    with st.spinner("Đang phân tích ảnh..."):
                        st.markdown(analyze_image(image_file.getvalue(), image_file.type or "image/png", question))
                except Exception as exc: st.error(str(exc))
        st.caption("Cần model hỗ trợ vision; nếu dùng Groq, hãy đặt GROQ_VISION_MODEL theo danh sách model vision hiện hành.")
    elif mode == "Giọng nói":
        st.markdown("**Nói để nhập câu hỏi**")
        audio_file = st.audio_input("Ghi âm câu hỏi")
        if audio_file and st.button("🎙️ Chuyển giọng nói thành chữ", type="primary"):
            try:
                text = transcribe_audio(audio_file.getvalue(), "recording.wav")
                st.session_state["transcribed_text"] = text
                st.success("Đã chuyển thành văn bản:")
                st.text_area("Văn bản nhận diện", value=text, key="transcribed_result")
            except Exception as exc: st.error(str(exc))
        speech_text = st.text_area("Đọc câu trả lời thành tiếng", key="speech_text")
        if st.button("🔊 Đọc văn bản", key="speak_btn"):
            import json as _json
            safe_text = _json.dumps(speech_text, ensure_ascii=False)
            st.components.v1.html(f"""<button id="phucs-speak">▶ Phát giọng đọc</button><script>const phucsText={safe_text};document.getElementById("phucs-speak").onclick=()=>{{const u=new SpeechSynthesisUtterance(phucsText);u.lang="vi-VN";speechSynthesis.cancel();speechSynthesis.speak(u);}};</script>""", height=60)
        st.caption("Nhận diện giọng nói cần API transcription. Đọc văn bản dùng giọng hệ thống của trình duyệt, chất lượng tùy thiết bị.")
    elif mode == "Tạo ảnh AI":
        prompt = st.text_area("Mô tả ảnh muốn tạo", placeholder="Một mascot học tập màu hồng pastel, sách và mũ tốt nghiệp...")
        if st.button("🎨 Tạo ảnh", type="primary", key="generate_img_btn"):
            try:
                with st.spinner("Đang tạo ảnh..."):
                    image_bytes = generate_image(prompt)
                st.image(image_bytes, caption="Ảnh do AI tạo", use_container_width=True)
                st.download_button("Tải ảnh PNG", data=image_bytes, file_name="phucs-ai-image.png", mime="image/png")
            except Exception as exc: st.error(str(exc))
    elif mode in ("Tạo video AI", "Tạo nhạc AI"):
        is_video = mode == "Tạo video AI"
        secret_name = "REPLICATE_VIDEO_MODEL" if is_video else "REPLICATE_MUSIC_MODEL"
        prompt = st.text_area("Mô tả nội dung", placeholder="Mô tả cảnh video..." if is_video else "Mô tả phong cách nhạc, nhịp điệu và cảm xúc...")
        configured_model = setting(secret_name)
        st.caption(f"Model đang cấu hình: {configured_model or 'chưa cấu hình'}")
        if st.button("🎬 Tạo video" if is_video else "🎵 Tạo nhạc", type="primary", key="replicate_media_btn"):
            try:
                with st.spinner("Đang gửi yêu cầu đến dịch vụ tạo nội dung..."):
                    result = replicate_create(configured_model, prompt)
                st.json(result)
                output = result.get("output")
                if isinstance(output, str) and output.startswith("http"):
                    st.markdown(f"[Mở kết quả được tạo]({output})")
                elif isinstance(output, list):
                    for item in output:
                        if isinstance(item, str) and item.startswith("http"): st.markdown(f"[Mở kết quả]({item})")
                st.caption("Một số model trả về trạng thái processing; cần đợi hoặc mở URL prediction để lấy kết quả sau.")
            except Exception as exc: st.error(str(exc))
        st.caption("Cần REPLICATE_API_TOKEN và REPLICATE_VIDEO_MODEL / REPLICATE_MUSIC_MODEL tương thích với API Replicate.")

# ---------- Group chat and video calls ----------
with pages[9]:
    st.subheader("👥 Nhóm học tập & phòng gọi video")
    group_id = st.text_input("Mã nhóm", value="lop-hoc-1", help="Mọi người dùng cùng mã nhóm để xem cùng phòng chat.")
    st.markdown("#### 💬 Tin nhắn nhóm")
    remote_group = bool(setting("SUPABASE_URL") and setting("SUPABASE_ANON_KEY"))
    if st.button("↻ Tải tin nhắn", key="load_group_msgs"):
        try:
            if remote_group:
                st.session_state["group_msgs"] = group_messages(group_id)
            else:
                with db() as con:
                    rows = con.execute("SELECT group_id,user_id,display_name,content,created_at FROM local_group_messages WHERE group_id=? ORDER BY id DESC LIMIT 50", (group_id,)).fetchall()
                st.session_state["group_msgs"] = [dict(r) for r in reversed(rows)]
        except Exception as exc:
            st.warning(f"Không truy cập được Supabase ({exc}); đang hiển thị kho chat cục bộ của phiên triển khai.")
            with db() as con:
                rows = con.execute("SELECT group_id,user_id,display_name,content,created_at FROM local_group_messages WHERE group_id=? ORDER BY id DESC LIMIT 50", (group_id,)).fetchall()
            st.session_state["group_msgs"] = [dict(r) for r in reversed(rows)]
    for msg in st.session_state.get("group_msgs", []):
        st.markdown(f"**{msg.get('display_name','Học viên')}** · {msg.get('created_at','')}  \n{msg.get('content','')}")
    with st.form("group_message_form", clear_on_submit=True):
        content = st.text_input("Tin nhắn mới", max_chars=2000)
        send = st.form_submit_button("Gửi tin nhắn", type="primary")
    if send and content.strip():
        try:
            if remote_group:
                send_group_message(group_id, uid, user["display_name"], content.strip())
                st.session_state["group_msgs"] = group_messages(group_id)
            else:
                with db() as con:
                    con.execute("INSERT INTO local_group_messages(group_id,user_id,display_name,content,created_at) VALUES(?,?,?,?,?)", (group_id, uid, user["display_name"], content.strip(), datetime.now().isoformat(timespec="seconds")))
                    rows = con.execute("SELECT group_id,user_id,display_name,content,created_at FROM local_group_messages WHERE group_id=? ORDER BY id DESC LIMIT 50", (group_id,)).fetchall()
                st.session_state["group_msgs"] = [dict(r) for r in reversed(rows)]
            st.rerun()
        except Exception as exc:
            st.warning(f"Không gửi được qua Supabase ({exc}); đã chuyển sang kho chat cục bộ trên máy chủ này.")
            with db() as con:
                con.execute("INSERT INTO local_group_messages(group_id,user_id,display_name,content,created_at) VALUES(?,?,?,?,?)", (group_id, uid, user["display_name"], content.strip(), datetime.now().isoformat(timespec="seconds")))
                rows = con.execute("SELECT group_id,user_id,display_name,content,created_at FROM local_group_messages WHERE group_id=? ORDER BY id DESC LIMIT 50", (group_id,)).fetchall()
            st.session_state["group_msgs"] = [dict(r) for r in reversed(rows)]
    if not remote_group:
        st.info("Đang dùng chế độ chat nhóm cục bộ trên máy chủ hiện tại. Để nhiều người dùng chia sẻ dữ liệu thật, cấu hình Supabase và chạy supabase_schema.sql.")
    st.divider()
    st.markdown("#### 📹 Gọi video")
    room = st.text_input("Tên phòng gọi", value=f"phucs-{group_id}")
    room_url = "https://meet.jit.si/" + "".join(ch for ch in room if ch.isalnum() or ch in "-_ ").replace(" ", "-")
    st.markdown(f"[Mở phòng gọi Jitsi ↗]({room_url})")
    st.caption("Đây là phòng họp Jitsi bên ngoài; không phải hệ thống gọi video tự lưu trữ. Không dùng phòng công khai để trao đổi dữ liệu nhạy cảm.")

# ---------- Plus, cloud storage and payment ----------
with pages[10]:
    st.subheader("☁️ P.H.U.C.S Plus & Lưu trữ đám mây")
    st.markdown("### P.H.U.C.S Plus")
    st.write("Giá dự kiến: **35.000 VNĐ/năm**. Bạn cần tạo sản phẩm và giá định kỳ trong Stripe Dashboard trước khi bật thanh toán.")
    st.caption("Không đánh dấu tài khoản là Plus chỉ vì người dùng quay về trang thành công; trạng thái trả phí phải được xác minh bằng webhook Stripe và lưu trong database đáng tin cậy.")
    email = st.text_input("Email nhận hóa đơn (tùy chọn)", key="billing_email")
    if st.button("💳 Thanh toán Plus", type="primary"):
        try:
            checkout_url = create_checkout_url(uid, email.strip())
            st.link_button("Mở trang thanh toán bảo mật ↗", checkout_url, use_container_width=True)
        except Exception as exc: st.error(str(exc))
    st.divider()
    st.markdown("### Tải tệp lên lưu trữ đám mây")
    st.write("Mục tiêu dung lượng 400–500 GB là dung lượng dự kiến của gói, không phải dung lượng tự có. Cần mua/chọn gói lưu trữ phù hợp và đặt giới hạn theo người dùng.")
    cloud_file = st.file_uploader("Chọn tệp để tải lên Supabase Storage", key="cloud_upload")
    if st.button("☁️ Tải lên", key="cloud_upload_btn"):
        if not cloud_file: st.warning("Hãy chọn một tệp.")
        else:
            try:
                with st.spinner("Đang tải tệp lên..."):
                    meta = upload_supabase_file(uid, cloud_file)
                st.success(f"Đã tải lên: {meta['path']} ({meta['size']:,} byte)")
                st.json(meta)
            except Exception as exc:
                # Usable development fallback. Streamlit Cloud filesystem is ephemeral; use Supabase for durable cloud storage.
                try:
                    upload_dir = APP_DIR / "data" / "uploads" / uid
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = Path(cloud_file.name).name.replace(" ", "_")
                    out_path = upload_dir / (datetime.now().strftime("%Y%m%d_%H%M%S_") + safe_name)
                    out_path.write_bytes(cloud_file.getvalue())
                    st.success(f"Đã lưu tệp tạm trên máy chủ: {out_path.name}")
                    st.warning("Lưu cục bộ chỉ phù hợp thử nghiệm; trên Streamlit Cloud, tệp có thể mất khi máy chủ khởi động lại. Cấu hình Supabase Storage để lưu bền vững.")
                    st.download_button("Tải lại tệp", data=out_path.read_bytes(), file_name=safe_name)
                except Exception as local_exc:
                    st.error(f"Tải lên thất bại: {exc}. Lưu cục bộ cũng thất bại: {local_exc}")
    st.caption("Lưu trữ đám mây bền vững cần SUPABASE_URL, SUPABASE_ANON_KEY và bucket phucs-files cùng Storage policies.")

st.divider()
st.caption("💌P.H.U.C.S AI được tạo ra để thay đổi thế giới, còn Nguyễn Ngọc Gia Phúc được sinh ra để tạo nên những điều kỳ diệu - Copyright © 2026 by Nguyễn Ngọc Gia Phúc..")
