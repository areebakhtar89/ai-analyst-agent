"""
app/ui/pages/1_Connect.py

Database connection page.
Users can connect MySQL, PostgreSQL, SQLite or DuckDB from the UI.
On success, all agents automatically use the new connection.
"""

import sys
import os
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
import requests
import json
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Connect · QueryMind",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #080b0f;
    --bg2:       #0d1117;
    --bg3:       #131920;
    --border:    #1c2635;
    --border2:   #243042;
    --accent:    #00d4aa;
    --accent2:   #f0a500;
    --danger:    #ff4f4f;
    --green:     #00e676;
    --text:      #ffffff;
    --text-dim:  #cccccc;
    --text-muted:#3a5068;
    --mono:      'Space Mono', monospace;
    --sans:      'DM Sans', sans-serif;
}

html, body, [class*="css"] { font-family: var(--sans); background-color: var(--bg) !important; }
#MainMenu, footer, header { visibility: hidden; height: 0; }
[data-testid="stHeader"], .stAppHeader, [data-testid="stToolbar"] { display: none !important; }
.stApp { background-color: var(--bg) !important; }
.block-container { padding-top: 0 !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 1200px !important; }

[data-testid="stSidebar"] { background-color: var(--bg2) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: var(--text-dim) !important; }

/* Page header */
.page-header {
    padding: 24px 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
}
.page-title {
    font-family: var(--mono);
    font-size: 22px; font-weight: 700;
    color: var(--text); letter-spacing: -0.5px;
}
.page-title span { color: var(--accent); }
.page-subtitle {
    font-family: var(--mono); font-size: 10px;
    color: var(--text-muted); letter-spacing: 2px;
    text-transform: uppercase; margin-top: 6px;
}

/* DB type selector cards */
.db-cards { display: flex; gap: 10px; margin-bottom: 28px; flex-wrap: wrap; }
.db-card {
    flex: 1; min-width: 120px;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
}
.db-card:hover { border-color: var(--accent); }
.db-card.active { border-color: var(--accent); background: #0a1e18; }
.db-card .db-icon { font-size: 20px; margin-bottom: 6px; }
.db-card .db-name {
    font-family: var(--mono); font-size: 11px;
    color: var(--text); font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
}
.db-card .db-desc { font-size: 10px; color: var(--text-muted); margin-top: 2px; }

/* Form section */
.form-section {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px 28px;
    margin-bottom: 20px;
}
.form-section-title {
    font-family: var(--mono); font-size: 9px;
    letter-spacing: 3px; text-transform: uppercase;
    color: var(--text-muted); margin-bottom: 18px;
    display: flex; align-items: center; gap: 8px;
}
.form-section-title::before {
    content: ''; display: inline-block;
    width: 12px; height: 1px; background: var(--accent);
}

/* Status banner */
.status-banner {
    border-radius: 6px; padding: 12px 16px;
    font-family: var(--mono); font-size: 11px;
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 20px;
}
.status-banner.success {
    background: #0a1e14; border: 1px solid #1a4a2e; color: var(--green);
}
.status-banner.error {
    background: #1e0a0a; border: 1px solid #4a1a1a; color: var(--danger);
}
.status-banner.info {
    background: #0a1420; border: 1px solid #1a2e4a; color: var(--accent);
}

/* Schema table */
.schema-header {
    font-family: var(--mono); font-size: 9px;
    letter-spacing: 3px; text-transform: uppercase;
    color: var(--text-muted); margin: 28px 0 14px 0;
    display: flex; align-items: center; gap: 8px;
}
.schema-header::before {
    content: ''; display: inline-block;
    width: 12px; height: 1px; background: var(--border2);
}

.table-card {
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 6px; padding: 14px 18px;
    margin-bottom: 8px; transition: border-color 0.15s;
}
.table-card:hover { border-color: var(--border2); }
.table-card-header {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 8px;
}
.table-name {
    font-family: var(--mono); font-size: 12px;
    font-weight: 700; color: var(--accent);
}
.table-meta {
    font-family: var(--mono); font-size: 10px;
    color: var(--text-muted);
}
.col-pills { display: flex; flex-wrap: wrap; gap: 5px; }
.col-pill {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 3px; padding: 2px 8px;
    font-family: var(--mono); font-size: 9px;
    color: var(--text-dim); display: flex; gap: 5px; align-items: center;
}
.col-pill .col-type { color: var(--text-muted); font-size: 8px; }

/* Connect button */
.stButton button {
    background: var(--accent) !important;
    border: none !important; color: #000 !important;
    font-family: var(--mono) !important; font-weight: 700 !important;
    font-size: 12px !important; letter-spacing: 1px !important;
    border-radius: 4px !important; padding: 10px 28px !important;
    transition: all 0.15s ease !important;
}
.stButton button:hover { opacity: 0.85 !important; transform: translateY(-1px) !important; }

/* Input styling */
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
    background: var(--bg3) !important;
    border: 1px solid var(--border2) !important;
    color: var(--text) !important;
    border-radius: 4px !important;
    font-family: var(--mono) !important;
    font-size: 12px !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}
[data-testid="stTextInput"] label, [data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label {
    font-family: var(--mono) !important; font-size: 10px !important;
    color: var(--text-muted) !important; letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
[data-testid="stSelectbox"] > div > div {
    background: var(--bg3) !important; border: 1px solid var(--border2) !important;
    color: var(--text) !important; border-radius: 4px !important;
    font-family: var(--mono) !important; font-size: 12px !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "conn_status" not in st.session_state:
    st.session_state.conn_status = None      # None | "success" | "error"
if "conn_message" not in st.session_state:
    st.session_state.conn_message = ""
if "conn_schema" not in st.session_state:
    st.session_state.conn_schema = []
if "conn_config" not in st.session_state:
    st.session_state.conn_config = {}
if "db_type" not in st.session_state:
    st.session_state.db_type = "mysql"


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="page-title">Query<span>Mind</span> · Connect</div>
    <div class="page-subtitle">Configure database source · All agents use active connection</div>
</div>
""", unsafe_allow_html=True)


# ── DB type selector ──────────────────────────────────────────────────────────
DB_TYPES = {
    "mysql":      ("🐬", "MySQL",      "8.0+"),
    "postgresql": ("🐘", "PostgreSQL", "13+"),
    "sqlite":     ("🗃️",  "SQLite",     "File-based"),
    "duckdb":     ("🦆", "DuckDB",     "Analytics"),
}

cols = st.columns(len(DB_TYPES))
for col, (key, (icon, name, desc)) in zip(cols, DB_TYPES.items()):
    with col:
        active_cls = "active" if st.session_state.db_type == key else ""
        st.markdown(f"""
        <div class="db-card {active_cls}" id="card_{key}">
            <div class="db-icon">{icon}</div>
            <div class="db-name">{name}</div>
            <div class="db-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Select {name}", key=f"sel_{key}", use_container_width=True):
            st.session_state.db_type = key
            st.session_state.conn_status = None
            st.rerun()

db_type = st.session_state.db_type


# ── Connection form ───────────────────────────────────────────────────────────
st.markdown('<div class="form-section">', unsafe_allow_html=True)
st.markdown(f'<div class="form-section-title">Connection Details · {DB_TYPES[db_type][1]}</div>', unsafe_allow_html=True)

config = {"type": db_type}

if db_type in ("mysql", "postgresql"):
    default_port = 3306 if db_type == "mysql" else 5432
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        config["host"] = st.text_input("Host", value="localhost", key="inp_host")
    with c2:
        config["port"] = st.number_input("Port", value=default_port, key="inp_port")
    with c3:
        config["database"] = st.text_input("Database", key="inp_database")

    c4, c5 = st.columns(2)
    with c4:
        config["user"] = st.text_input("Username", key="inp_user")
    with c5:
        config["password"] = st.text_input("Password", type="password", key="inp_password")

elif db_type in ("sqlite", "duckdb"):
    config["file"] = st.text_input(
        "File Path",
        placeholder="data/analytics.duckdb  or  /absolute/path/to/db.sqlite",
        key="inp_file"
    )
    st.markdown(
        '<div style="font-family:Space Mono,monospace;font-size:10px;color:#3a5068;margin-top:4px">'
        'Path relative to project root, or absolute path.</div>',
        unsafe_allow_html=True
    )

st.markdown('</div>', unsafe_allow_html=True)


# ── Connect button ────────────────────────────────────────────────────────────
if st.button("⚡  Connect", key="btn_connect"):
    with st.spinner("Testing connection..."):
        try:
            resp = requests.post(f"{API_URL}/connect", json=config, timeout=10)
            data = resp.json()
            if data.get("success"):
                st.session_state.conn_status  = "success"
                st.session_state.conn_message = data.get("message", "Connected.")
                st.session_state.conn_config  = config
                # Fetch schema immediately after connecting
                schema_resp = requests.get(f"{API_URL}/schema", timeout=15)
                schema_data = schema_resp.json()
                st.session_state.conn_schema = schema_data.get("tables", [])
            else:
                st.session_state.conn_status  = "error"
                st.session_state.conn_message = data.get("message", "Connection failed.")
                st.session_state.conn_schema  = []
        except Exception as e:
            st.session_state.conn_status  = "error"
            st.session_state.conn_message = f"Could not reach API: {e}"
            st.session_state.conn_schema  = []
    st.rerun()


# ── Status banner ─────────────────────────────────────────────────────────────
if st.session_state.conn_status == "success":
    cfg = st.session_state.conn_config
    db_label = cfg.get("database") or cfg.get("file", "")
    st.markdown(
        f'<div class="status-banner success">✓ &nbsp; Connected to <strong>{db_label}</strong> '
        f'via {cfg.get("type", "").upper()} · '
        f'{len(st.session_state.conn_schema)} tables found</div>',
        unsafe_allow_html=True
    )
elif st.session_state.conn_status == "error":
    st.markdown(
        f'<div class="status-banner error">✕ &nbsp; {st.session_state.conn_message}</div>',
        unsafe_allow_html=True
    )


# ── Schema browser ────────────────────────────────────────────────────────────
if st.session_state.conn_schema:
    st.markdown('<div class="schema-header">Schema Explorer</div>', unsafe_allow_html=True)

    # Summary stats
    total_rows = sum(t.get("row_count", 0) for t in st.session_state.conn_schema)
    total_cols = sum(len(t.get("columns", [])) for t in st.session_state.conn_schema)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Tables", len(st.session_state.conn_schema))
    with m2:
        st.metric("Total Rows", f"{total_rows:,}")
    with m3:
        st.metric("Total Columns", total_cols)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Table cards
    for table in st.session_state.conn_schema:
        col_pills = "".join([
            f'<div class="col-pill">{c["name"]} <span class="col-type">{c["type"]}</span></div>'
            for c in table.get("columns", [])
        ])
        st.markdown(f"""
        <div class="table-card">
            <div class="table-card-header">
                <span class="table-name">{table["table"]}</span>
                <span class="table-meta">{table.get("row_count", 0):,} rows · {len(table.get("columns", []))} cols</span>
            </div>
            <div class="col-pills">{col_pills}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div style="font-family:Space Mono,monospace;font-size:10px;color:#3a5068;'
        'margin-top:16px;padding-top:16px;border-top:1px solid #1c2635">'
        '↩ Return to the main page to start querying.</div>',
        unsafe_allow_html=True
    )
