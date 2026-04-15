"""
AeroAnalytics - Minimal Clean UI (Claude-style)
Hides all Streamlit chrome. Custom header with exit button.
"""
import streamlit as st
import os
from utils.llm_provider import get_provider_status


def inject_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ═══════════════════════════════════════════════════
   HIDE ALL STREAMLIT CHROME — header, toolbar, menu
   ═══════════════════════════════════════════════════ */
#MainMenu                            { display:none !important; }
header[data-testid="stHeader"]       { display:none !important; }
div[data-testid="stToolbar"]         { display:none !important; }
div[data-testid="stDecoration"]      { display:none !important; }
div[data-testid="stStatusWidget"]    { display:none !important; }
footer                               { display:none !important; }

/* Hide sidebar collapse/expand toggle button entirely */
button[data-testid="baseButton-headerNoPadding"],
div[data-testid="collapsedControl"]  { display:none !important; }

/* ═══════════════════════════════════════════════════
   BASE
   ═══════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body,
.stApp,
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > section,
section[data-testid="stMain"],
div[data-testid="block-container"],
.main, .main > div {
    background-color: #f9f9f7 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: #1a1a1a !important;
}

div[data-testid="block-container"] {
    padding: 1rem 2rem 2rem !important;
    max-width: 100% !important;
}

/* ═══════════════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════════════ */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: #f0eeeb !important;
    border-right: 1px solid #e0ddd8 !important;
}
section[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif !important;
    color: #4a4a4a !important;
}

/* ═══════════════════════════════════════════════════
   TYPOGRAPHY
   ═══════════════════════════════════════════════════ */
p, span, div, li, td, th { color: #1a1a1a !important; font-size: 14px !important; line-height: 1.6 !important; }
h1,h2,h3,h4,h5,h6 { color: #1a1a1a !important; font-weight: 600 !important; }
label { color: #666 !important; font-size: 12px !important; }

/* ═══════════════════════════════════════════════════
   INPUTS
   ═══════════════════════════════════════════════════ */
input[type="text"], input[type="password"], input[type="number"], textarea {
    background-color: #fff !important;
    color: #1a1a1a !important;
    border: 1px solid #d9d6cf !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
}
input:focus, textarea:focus {
    border-color: #c96442 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(201,100,66,.1) !important;
}
input::placeholder, textarea::placeholder { color: #a09d97 !important; }

/* ═══════════════════════════════════════════════════
   CHAT INPUT
   ═══════════════════════════════════════════════════ */
div[data-testid="stChatInput"] {
    background-color: #fff !important;
    border: 1.5px solid #d9d6cf !important;
    border-radius: 14px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.06) !important;
}
div[data-testid="stChatInput"]:focus-within {
    border-color: #c96442 !important;
    box-shadow: 0 0 0 3px rgba(201,100,66,.1) !important;
}
div[data-testid="stChatInput"] textarea {
    background: transparent !important;
    border: none !important;
    color: #1a1a1a !important;
    font-size: 14px !important;
    box-shadow: none !important;
    caret-color: #c96442 !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: #a09d97 !important; }
div[data-testid="stChatInput"] button {
    background: #c96442 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
}
div[data-testid="stChatInput"] button:hover { background: #b5552f !important; }

/* ═══════════════════════════════════════════════════
   SELECTBOX
   ═══════════════════════════════════════════════════ */
div[data-baseweb="select"] > div {
    background-color: #fff !important;
    border: 1px solid #d9d6cf !important;
    border-radius: 8px !important;
    color: #1a1a1a !important;
}
div[data-baseweb="select"] span,
div[data-baseweb="select"] div { color: #1a1a1a !important; background: transparent !important; }
div[data-baseweb="popover"], div[data-baseweb="menu"] {
    background-color: #fff !important;
    border: 1px solid #e0ddd8 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,.1) !important;
}
li[role="option"] { color: #1a1a1a !important; background: transparent !important; padding: 10px 14px !important; border-radius: 6px !important; margin: 2px 4px !important; }
li[role="option"]:hover, li[aria-selected="true"] { background-color: #f0eeeb !important; color: #c96442 !important; }

/* ═══════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════ */
.stButton > button {
    background-color: #fff !important;
    color: #1a1a1a !important;
    border: 1px solid #d9d6cf !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    transition: all .15s !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover {
    background-color: #f0eeeb !important;
    border-color: #c96442 !important;
    color: #c96442 !important;
}

/* Exit button */
.exit-btn .stButton > button {
    background-color: #fff0ed !important;
    color: #c96442 !important;
    border: 1px solid #f5c6b8 !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 7px 14px !important;
    border-radius: 8px !important;
}
.exit-btn .stButton > button:hover {
    background-color: #c96442 !important;
    color: #fff !important;
}

/* Suggestion chips */
.chip-btn .stButton > button {
    background-color: #fff !important;
    color: #4a4a4a !important;
    border: 1px solid #e0ddd8 !important;
    border-radius: 10px !important;
    font-size: 12px !important;
    padding: 10px 14px !important;
    width: 100% !important;
    text-align: left !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.04) !important;
    line-height: 1.4 !important;
}
.chip-btn .stButton > button:hover {
    background-color: #fff0ed !important;
    border-color: #c96442 !important;
    color: #c96442 !important;
}

/* Download */
.stDownloadButton > button {
    background-color: #fff !important;
    color: #c96442 !important;
    border: 1px solid #d9d6cf !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
.stDownloadButton > button:hover { background-color: #fff0ed !important; border-color: #c96442 !important; }

/* ═══════════════════════════════════════════════════
   TABS
   ═══════════════════════════════════════════════════ */
div[data-testid="stTabs"] > div:first-child { border-bottom: 1px solid #e0ddd8 !important; }
button[data-baseweb="tab"] {
    background: transparent !important; color: #888 !important;
    font-size: 13px !important; font-weight: 500 !important;
    padding: 10px 16px !important;
    border-bottom: 2px solid transparent !important; border-radius: 0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] { color: #c96442 !important; border-bottom: 2px solid #c96442 !important; }
div[data-testid="stTabsContent"] { background: transparent !important; padding-top: 1rem !important; }

/* ═══════════════════════════════════════════════════
   FILE UPLOADER
   ═══════════════════════════════════════════════════ */
div[data-testid="stFileUploader"] {
    background-color: #fff !important;
    border: 2px dashed #d9d6cf !important;
    border-radius: 10px !important; padding: 16px !important;
}
div[data-testid="stFileUploader"]:hover { border-color: #c96442 !important; }
div[data-testid="stFileUploader"] * { color: #4a4a4a !important; }
div[data-testid="stFileUploader"] button { background: #c96442 !important; color: #fff !important; border: none !important; border-radius: 8px !important; }

/* ═══════════════════════════════════════════════════
   EXPANDER / DATAFRAME / ALERTS
   ═══════════════════════════════════════════════════ */
details { background-color: #fff !important; border: 1px solid #e0ddd8 !important; border-radius: 10px !important; }
summary { color: #666 !important; font-size: 13px !important; padding: 10px 14px !important; cursor: pointer !important; }

div[data-testid="stDataFrame"] { border: 1px solid #e0ddd8 !important; border-radius: 10px !important; overflow: hidden !important; }
div[data-testid="stDataFrame"] th { background-color: #f0eeeb !important; color: #1a1a1a !important; font-weight: 600 !important; font-size: 12px !important; border-bottom: 1px solid #e0ddd8 !important; }
div[data-testid="stDataFrame"] td { color: #1a1a1a !important; font-size: 13px !important; }

div[data-testid="stAlert"] { background-color: #fff !important; border: 1px solid #e0ddd8 !important; border-radius: 10px !important; }
div[data-testid="stAlert"] * { color: #4a4a4a !important; }

/* ═══════════════════════════════════════════════════
   SCROLLBAR
   ═══════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f0eeeb; }
::-webkit-scrollbar-thumb { background: #d9d6cf; border-radius: 3px; }

/* ═══════════════════════════════════════════════════
   CHAT COMPONENTS
   ═══════════════════════════════════════════════════ */
.msg-user { display:flex; justify-content:flex-end; margin:12px 0; }
.msg-user-inner {
    background: #c96442; color: #fff !important;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px; max-width: 80%;
    font-size: 14px !important; line-height: 1.6 !important;
    box-shadow: 0 2px 8px rgba(201,100,66,.2);
}
.msg-user-inner * { color: #fff !important; }
.msg-ai { margin: 8px 0 16px; }

.sql-block {
    background: #faf6f2; border: 1px solid #e8e0d8;
    border-left: 3px solid #c96442; color: #7a3b10 !important;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px !important; line-height: 1.7 !important;
    padding: 14px 16px; border-radius: 0 10px 10px 0;
    margin: 10px 0; white-space: pre-wrap; overflow-x: auto;
}
.sql-block * { color: #7a3b10 !important; }

.insight-card {
    background: #fff; border: 1px solid #e0ddd8;
    border-left: 3px solid #2d8a5e;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px; margin: 10px 0;
    font-size: 14px !important; line-height: 1.8 !important;
    color: #1a1a1a !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.insight-card * { color: #1a1a1a !important; }
.insight-card b, .insight-card strong { color: #2d8a5e !important; font-weight: 600 !important; }

.error-card {
    background: #fff5f5; border: 1px solid #f5c6c6;
    border-left: 3px solid #e53e3e; border-radius: 0 10px 10px 0;
    padding: 12px 16px; margin: 8px 0;
    font-size: 13px !important; color: #c53030 !important;
}
.error-card * { color: #c53030 !important; }

/* ═══════════════════════════════════════════════════
   PILLS / LABELS / CARDS
   ═══════════════════════════════════════════════════ */
.pill-green { display:inline-flex;align-items:center;gap:6px;background:#f0faf5;color:#2d8a5e !important;border:1px solid #b2dfcc;border-radius:20px;padding:4px 12px;font-size:11px !important;font-weight:500; }
.pill-yellow { display:inline-flex;align-items:center;gap:6px;background:#fffbeb;color:#b7791f !important;border:1px solid #f6d860;border-radius:20px;padding:4px 12px;font-size:11px !important;font-weight:500; }
.dot-green  { width:6px;height:6px;border-radius:50%;background:#2d8a5e;display:inline-block; }
.dot-yellow { width:6px;height:6px;border-radius:50%;background:#d69e2e;display:inline-block; }

.slabel { font-size:10px !important;font-weight:700 !important;letter-spacing:.1em;text-transform:uppercase;color:#a09d97 !important;margin:16px 0 8px;display:block; }
.info-box { background:#fff;border:1px solid #e0ddd8;border-radius:8px;padding:10px 14px;font-size:11px !important;margin-top:8px;box-shadow:0 1px 3px rgba(0,0,0,.04); }
.info-box-label { color:#a09d97 !important;font-size:10px !important;font-weight:600 !important;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px;display:block; }
.info-box-val { color:#c96442 !important;font-family:'JetBrains Mono',monospace;font-size:11px !important;line-height:1.8 !important; }

.stat-row { display:grid;grid-template-columns:1fr 1fr minmax(0,2fr);gap:10px;margin-bottom:14px; }
.stat-card { background:#fff;border:1px solid #e0ddd8;border-radius:10px;padding:12px 16px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.04); }
.stat-num { font-size:22px !important;font-weight:700 !important;color:#c96442 !important;line-height:1.2 !important; }
.stat-label { font-size:10px !important;color:#a09d97 !important;margin-top:3px !important;text-transform:uppercase;letter-spacing:.06em; }
.stat-cols { display:flex;flex-direction:column;justify-content:center;text-align:left; }
.stat-cols-label { font-size:10px !important;color:#c96442 !important;font-weight:600 !important;margin-bottom:2px !important;text-transform:uppercase;letter-spacing:.06em; }
.stat-cols-val { font-size:11px !important;color:#888 !important; }

.empty-state { display:flex;flex-direction:column;align-items:center;justify-content:center;height:360px;border:1.5px dashed #e0ddd8;border-radius:16px;background:#faf9f7;text-align:center;gap:12px; }
.empty-icon { font-size:36px;opacity:.25; }
.empty-title { font-size:15px !important;font-weight:600 !important;color:#a09d97 !important; }
.empty-sub { font-size:13px !important;color:#c8c5bf !important;max-width:200px;line-height:1.5 !important; }

div[data-testid="stSpinner"] > div { border-top-color: #c96442 !important; }
</style>
""", unsafe_allow_html=True)


def render_header():
    """Header row: logo left, exit button right."""
    col_logo, col_exit = st.columns([6, 1])

    with col_logo:
        st.markdown("""
<div style="display:flex;align-items:center;gap:14px;padding:12px 20px;
            background:#fff;border:1px solid #e0ddd8;border-radius:14px;
            box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:20px;">
  <div style="background:linear-gradient(135deg,#c96442,#e8845e);
              width:42px;height:42px;border-radius:11px;
              display:flex;align-items:center;justify-content:center;
              font-size:20px;flex-shrink:0;">✈</div>
  <div>
    <div style="font-size:18px;font-weight:700;color:#1a1a1a;letter-spacing:-.3px;line-height:1.2;">
      AI Data Analyst
    </div>
    <div style="font-size:11px;color:#888;margin-top:2px;">
      Airline Intelligence &nbsp;·&nbsp; Claude on AWS Bedrock
    </div>
  </div>
  <div style="margin-left:auto;display:flex;gap:8px;align-items:center;">
    <span style="background:#fff0ed;color:#c96442;border:1px solid #f5c6b8;
                 border-radius:20px;padding:5px 12px;font-size:11px;font-weight:600;white-space:nowrap;">
      Text &#8594; SQL &#8594; Insight
    </span>
    <span style="background:#f0faf5;color:#2d8a5e;border:1px solid #b2dfcc;
                 border-radius:20px;padding:5px 12px;font-size:11px;font-weight:600;white-space:nowrap;">
      &#9679; Live
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

    with col_exit:
        st.markdown("<div style='margin-bottom:20px;'>", unsafe_allow_html=True)
        st.markdown('<div class="exit-btn">', unsafe_allow_html=True)
        if st.button("Stop & Exit", use_container_width=True):
            st.markdown("""
<div style="background:#fff0ed;border:1px solid #f5c6b8;border-radius:8px;
            padding:10px;text-align:center;margin-top:4px;">
  <div style="font-size:12px;color:#c96442;font-weight:600;">Stopped.</div>
  <div style="font-size:10px;color:#888;margin-top:2px;">Close this tab.</div>
</div>""", unsafe_allow_html=True)
            import time; time.sleep(1)
            os._exit(0)
        st.markdown('</div></div>', unsafe_allow_html=True)


def render_sidebar() -> dict:
    inject_styles()

    # Logo
    st.markdown("""
<div style="padding:14px 0 16px;border-bottom:1px solid #e0ddd8;margin-bottom:4px;">
  <div style="font-size:15px;font-weight:700;color:#1a1a1a;display:flex;align-items:center;gap:8px;">
    <span>✈</span> AeroAnalytics
  </div>
  <div style="font-size:11px;color:#a09d97;margin-top:3px;">Powered by Claude AI</div>
</div>
""", unsafe_allow_html=True)

    status = get_provider_status()

    # LLM Provider
    st.markdown('<span class="slabel">LLM Provider</span>', unsafe_allow_html=True)
    provider_choice = st.selectbox("Provider",
        ["AWS Bedrock (Claude)", "Azure OpenAI (GPT-4o)"],
        index=0 if status["provider"] == "bedrock" else 1,
        key="llm_provider_sel", label_visibility="collapsed")
    is_bedrock = "Bedrock" in provider_choice
    llm_config = {"provider": "bedrock" if is_bedrock else "azure"}

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if is_bedrock:
        if status["bedrock_ok"]:
            st.markdown('<span class="pill-green"><span class="dot-green"></span>Credentials loaded from .env</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="pill-yellow"><span class="dot-yellow"></span>Keys not found in .env</span>', unsafe_allow_html=True)
        st.markdown(f"""
<div class="info-box" style="margin-top:10px;">
  <span class="info-box-label">Auto-loaded from .env</span>
  <div class="info-box-val">Region: {status['region']}<br>Model: {status['model'][:42]}</div>
</div>""", unsafe_allow_html=True)
        with st.expander("Override credentials"):
            ak = st.text_input("Access Key ID", type="password", placeholder="Leave blank — uses .env")
            sk = st.text_input("Secret Access Key", type="password", placeholder="Leave blank — uses .env")
            region = st.selectbox("Region", ["ap-southeast-2","ap-southeast-1","us-east-1","us-west-2","eu-west-1"])
            model  = st.selectbox("Model", [
                "au.anthropic.claude-haiku-4-5-20251001-v1:0",
                "au.anthropic.claude-sonnet-4-5-20250929-v1:0",
                "us.anthropic.claude-haiku-4-5-20251001-v1:0",
                "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            ])
            if ak: llm_config["aws_access_key_id"]     = ak
            if sk: llm_config["aws_secret_access_key"] = sk
            llm_config["aws_region"] = region
            llm_config["model_id"]   = model
    else:
        if status["azure_ok"]:
            st.markdown('<span class="pill-green"><span class="dot-green"></span>Credentials loaded from .env</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="pill-yellow"><span class="dot-yellow"></span>Keys not found in .env</span>', unsafe_allow_html=True)
        with st.expander("Override credentials"):
            endpoint   = st.text_input("Endpoint URL", placeholder="Leave blank — uses .env")
            api_key    = st.text_input("API Key", type="password", placeholder="Leave blank — uses .env")
            deployment = st.text_input("Deployment name", value=status["deployment"])
            api_ver    = st.selectbox("API Version", ["2024-08-01-preview","2024-05-01-preview"])
            if endpoint: llm_config["azure_endpoint"]   = endpoint
            if api_key:  llm_config["azure_api_key"]    = api_key
            llm_config["azure_deployment"]  = deployment
            llm_config["azure_api_version"] = api_ver

    st.session_state.llm_config = llm_config

    # Data Source
    st.markdown('<span class="slabel" style="margin-top:20px;">Data Source</span>', unsafe_allow_html=True)
    source_type = st.selectbox("Source",
        ["Airline Demo DB","Upload File (CSV/Excel/JSON)","SQLite","PostgreSQL","MySQL","BigQuery","Demo data (clinic)"],
        key="source_type_sel", label_visibility="collapsed")
    config = {}

    if source_type == "Airline Demo DB":
        st.markdown("""
<div class="info-box" style="margin-top:8px;">
  <div style="color:#2d8a5e;font-weight:600;font-size:12px !important;margin-bottom:6px;">✈ Airline Intelligence DB</div>
  <div style="color:#888;font-size:11px !important;line-height:1.6;">17 tables · 44,657 rows<br>Flights · Bookings · Crew · Finance · Baggage</div>
</div>""", unsafe_allow_html=True)
        db_path = st.text_input("Path to DB", value="airline_dummy.db", label_visibility="collapsed")
        config = {"type": "airline_demo", "db_path": db_path}

    elif source_type == "Upload File (CSV/Excel/JSON)":
        st.markdown('<div style="font-size:12px;color:#888;margin:6px 0 8px;">Upload any CSV, Excel or JSON file</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Drop file here", type=["csv","xlsx","xls","json"])
        if uploaded:
            ext = uploaded.name.rsplit(".",1)[-1].lower()
            config = {"type": "excel" if ext in ("xlsx","xls") else ext,
                      "file_data": uploaded.read(), "file_name": uploaded.name}
            st.markdown(f'<div class="info-box"><div style="color:#2d8a5e;font-weight:600;font-size:12px !important;">Loaded: {uploaded.name}</div></div>', unsafe_allow_html=True)

    elif source_type == "SQLite":
        db_file = st.file_uploader("Upload .db file", type=["db","sqlite","sqlite3"])
        if db_file:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            tmp.write(db_file.read()); tmp.flush()
            config = {"type": "sqlite", "db_path": tmp.name}

    elif source_type in ("PostgreSQL","MySQL"):
        dialect = "postgres" if source_type=="PostgreSQL" else "mysql"
        with st.expander("Connection details", expanded=True):
            host     = st.text_input("Host", value="localhost")
            port     = st.number_input("Port", value=5432 if dialect=="postgres" else 3306)
            database = st.text_input("Database name")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        config = {"type": dialect, "host": host, "port": int(port),
                  "database": database, "username": username, "password": password}

    elif source_type == "BigQuery":
        key_file = st.file_uploader("Service account JSON", type=["json"])
        project  = st.text_input("GCP Project ID")
        dataset  = st.text_input("Dataset")
        if key_file and project:
            config = {"type":"bigquery","key_data":key_file.read(),"project":project,"dataset":dataset}

    elif source_type == "Demo data (clinic)":
        st.markdown('<div class="info-box"><div style="color:#2d8a5e;font-size:12px !important;font-weight:500;">Built-in clinic dataset</div></div>', unsafe_allow_html=True)
        config = {"type": "demo"}

    if config:
        st.session_state.connection_config = config

    st.markdown('<div style="margin-top:24px;padding-top:16px;border-top:1px solid #e0ddd8;">', unsafe_allow_html=True)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_result  = None
        st.rerun()
    st.markdown("""
<div style="font-size:10px;color:#c8c5bf;text-align:center;margin-top:10px;">
  AeroAnalytics v1.0 · Built with Claude
</div></div>
""", unsafe_allow_html=True)

    return config
