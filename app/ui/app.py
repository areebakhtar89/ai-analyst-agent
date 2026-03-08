import sys
import os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
import requests
import pandas as pd
import uuid
import re
import json
import time
import plotly.express as px
import plotly.io as pio
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="QueryMind · AI Analyst",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# GLOBAL CSS — Terminal Operations Aesthetic
# Sharp, dense, data-forward. Feels like
# infrastructure, not a chatbot.
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #080b0f;
    --bg2:       #0d1117;
    --bg3:       #131920;
    --border:    #1c2635;
    --border2:   #243042;
    --accent:    #00d4aa;
    --accent2:   #f0a500;
    --accent3:   #4d9fff;
    --danger:    #ff4f4f;
    --text:      #ffffff;
    --text-dim:  #cccccc;
    --text-muted:#3a5068;
    --green:     #00e676;
    --mono:      'Space Mono', monospace;
    --sans:      'DM Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--sans);
    background-color: var(--bg) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; height: 0; min-height: 0; padding: 0; }
[data-testid="stHeader"] { display: none !important; }
.stAppHeader { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.stApp { background-color: var(--bg) !important; }
.block-container {
    padding-top: 0 !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background-color: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-dim) !important; }

.sidebar-brand {
    padding: 20px 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.sidebar-brand .logo-mark {
    font-family: var(--mono);
    font-size: 22px;
    font-weight: 700;
    color: var(--accent) !important;
    letter-spacing: -1px;
    line-height: 1;
}
.sidebar-brand .logo-sub {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-muted) !important;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
}
.sidebar-brand .status-dot {
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    margin-right: 6px;
    box-shadow: 0 0 6px var(--green);
    animation: breathe 2s ease-in-out infinite;
}
.sidebar-brand .status-line {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-muted) !important;
    letter-spacing: 1px;
    margin-top: 10px;
}
@keyframes breathe {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

.sidebar-section {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-muted) !important;
    margin: 24px 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 6px;
}
.sidebar-section::before {
    content: '';
    display: inline-block;
    width: 3px; height: 3px;
    background: var(--accent);
    border-radius: 50%;
}

/* Sidebar question buttons */
[data-testid="stSidebar"] .stButton button {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-dim) !important;
    border-radius: 4px !important;
    font-size: 11px !important;
    font-family: var(--sans) !important;
    text-align: left !important;
    padding: 9px 12px !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
    margin-bottom: 3px !important;
    line-height: 1.4 !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: #0d1e2e !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    transform: translateX(2px) !important;
}

/* ── MAIN HEADER ── */
.main-header {
    padding: 24px 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
}
.main-title {
    font-family: var(--mono);
    font-size: 26px;
    font-weight: 700;
    color: #e8f4ff;
    letter-spacing: -1px;
    line-height: 1;
}
.main-title span { color: var(--accent); }
.main-subtitle {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 6px;
}
.header-stats {
    display: flex;
    gap: 20px;
    align-items: center;
}
.header-stat {
    text-align: right;
    font-family: var(--mono);
}
.header-stat .val {
    font-size: 18px;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
}
.header-stat .lbl {
    font-size: 9px;
    color: var(--text-muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
}
.header-divider {
    width: 1px; height: 36px;
    background: var(--border);
}

/* ── USER MESSAGE ── */
.user-bubble {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin: 20px 0 8px 0;
}
.user-avatar {
    width: 30px; height: 30px;
    background: var(--bg3);
    border: 1px solid var(--border2);
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px;
    flex-shrink: 0;
}
.user-text {
    background: var(--bg3);
    border: 1px solid var(--border2);
    border-radius: 0 8px 8px 8px;
    padding: 10px 16px;
    font-size: 14px;
    color: #ffffff;
    font-family: var(--sans);
    line-height: 1.5;
    max-width: 80%;
}

/* ── AGENT PIPELINE ── */
.agent-pipeline {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 8px 0 20px 0;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 9px 16px;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 1px;
}
.agent-step {
    display: flex; align-items: center; gap: 7px;
    color: var(--text-muted);
    padding: 0 12px 0 0;
    white-space: nowrap;
}
.agent-step.done { color: var(--accent); }
.agent-step.active { color: #ffffff; }
.agent-step .dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--text-muted);
    flex-shrink: 0;
}
.agent-step.done .dot { background: var(--accent); box-shadow: 0 0 6px var(--accent); }
.agent-step.active .dot { background: #fff; animation: pulse 0.8s infinite; }
.agent-sep { color: var(--border2); padding: 0 4px; font-size: 14px; }

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(0.6); }
}

/* ── INSIGHTS ── */
.insights-header {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.insights-header::before {
    content: '';
    display: inline-block;
    width: 16px; height: 1px;
    background: var(--accent);
}

.insight-card {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 2px solid var(--accent);
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 6px;
    transition: border-color 0.2s;
}
.insight-card:hover { border-color: var(--accent); border-left-color: var(--accent2); }
.insight-num {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--accent);
    font-weight: 700;
    min-width: 22px;
    padding-top: 2px;
    opacity: 0.7;
}
.insight-text {
    font-size: 13px;
    color: #ffffff;
    line-height: 1.65;
    font-family: var(--sans);
}

/* ── SECTION LABELS ── */
.section-label {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::before {
    content: '';
    display: inline-block;
    width: 10px; height: 1px;
    background: var(--border2);
}

.chart-type-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #0a1a14;
    border: 1px solid #1a3a2e;
    border-radius: 3px;
    padding: 2px 8px;
    font-family: var(--mono);
    font-size: 9px;
    color: var(--accent);
    margin-left: 8px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── CHART WRAPPER ── */
.chart-wrapper {
    border: 1px solid var(--border2);
    border-radius: 6px;
    overflow: hidden;
    background: #090e14;
    margin-top: 4px;
}

/* ── ROW LIMIT BANNER ── */
.row-limit-banner {
    background: #1a1400;
    border: 1px solid #3a2e00;
    border-radius: 4px;
    padding: 7px 14px;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--accent2);
    letter-spacing: 0.5px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.row-limit-banner::before { content: '⚠'; font-size: 11px; }

/* ── DATA TABLE ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
}

/* ── DOWNLOAD BUTTONS ── */
.stDownloadButton button {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-dim) !important;
    font-size: 10px !important;
    font-family: var(--mono) !important;
    border-radius: 3px !important;
    padding: 5px 12px !important;
    letter-spacing: 1px !important;
}
.stDownloadButton button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] {
    border-top: 1px solid var(--border) !important;
    background: var(--bg) !important;
    padding: 12px 0 !important;
}
[data-testid="stChatInput"] textarea {
    background: var(--bg2) !important;
    border: 1px solid var(--border2) !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    font-family: var(--sans) !important;
    font-size: 14px !important;
    caret-color: var(--accent) !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}

/* ── TYPING CURSOR ── */
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.typing-cursor {
    display: inline-block; width: 2px; height: 13px;
    background: var(--accent); margin-left: 2px;
    vertical-align: middle; animation: blink 0.9s step-end infinite;
}

/* ── NEW SESSION BUTTON ── */
.new-session-btn button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
    font-size: 10px !important;
    font-family: var(--mono) !important;
    border-radius: 4px !important;
    width: 100% !important;
    margin-top: 8px !important;
    letter-spacing: 1px !important;
    padding: 8px !important;
}
.new-session-btn button:hover {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
}

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    color: var(--accent) !important;
    border-radius: 4px !important;
    font-family: var(--mono) !important;
    font-size: 11px !important;
}

/* ── CONVERSATION DIVIDER ── */
.convo-divider {
    height: 1px;
    background: linear-gradient(to right, transparent, var(--border), transparent);
    margin: 28px 0;
}

/* ── EMPTY STATE ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}
.empty-state .bigmark {
    font-family: var(--mono);
    font-size: 48px;
    color: var(--border2);
    line-height: 1;
    margin-bottom: 16px;
}
.empty-state h3 {
    font-family: var(--mono);
    font-size: 14px;
    color: var(--text-dim);
    font-weight: 400;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.empty-state p {
    font-size: 12px;
    color: var(--text-muted);
    font-family: var(--sans);
    max-width: 380px;
    margin: 0 auto;
    line-height: 1.6;
}

/* Slider */
[data-testid="stSlider"] > div > div > div {
    background: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "chart_overrides" not in st.session_state:
    st.session_state.chart_overrides = {}
if "query_count" not in st.session_state:
    st.session_state.query_count = 0


# ─────────────────────────────────────────
# CHART TYPE SWITCHER
# ─────────────────────────────────────────
CHART_OPTIONS = ["bar", "line", "scatter", "pie", "area"]

def get_applicable_chart_types(result: list) -> tuple[list, dict]:
    if not result:
        return [], {}
    df = pd.DataFrame(result)
    cols = list(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = [c for c in cols if c not in numeric_cols]
    n_rows = len(df)
    applicable, reasons = [], {}
    if cat_cols and numeric_cols:
        applicable.append("bar")
    else:
        reasons["bar"] = "needs a category + numeric column"
    if numeric_cols and len(cols) >= 2:
        applicable.append("line")
    else:
        reasons["line"] = "needs at least one numeric column"
    if len(numeric_cols) >= 2:
        applicable.append("scatter")
    else:
        reasons["scatter"] = "needs 2 numeric columns"
    if cat_cols and numeric_cols and n_rows <= 12:
        applicable.append("pie")
    elif cat_cols and numeric_cols:
        reasons["pie"] = f"too many slices ({n_rows}) — best with ≤12"
    else:
        reasons["pie"] = "needs a category + numeric column"
    if numeric_cols and len(cols) >= 2:
        applicable.append("area")
    else:
        reasons["area"] = "needs at least one numeric column"
    return applicable, reasons


_TIME_KW     = ["date","time","month","year","day","week","quarter"]
_METRIC_KW   = ["revenue","sales","amount","price","total","count",
                 "profit","cost","value","qty","quantity","avg","sum"]
_CATEGORY_KW = ["name","region","segment","category","type","status",
                 "country","city","product","brand","department","state"]

def _classify_df(df):
    time_cols, metric_cols, cat_cols = [], [], []
    for col in df.columns:
        cl = col.lower()
        dtype = df[col].dtype
        if any(k in cl for k in _TIME_KW):
            time_cols.append(col)
        elif any(k in cl for k in _METRIC_KW) and pd.api.types.is_numeric_dtype(dtype):
            metric_cols.append(col)
        elif pd.api.types.is_numeric_dtype(dtype):
            (metric_cols if df[col].nunique() > 20 else cat_cols).append(col)
        else:
            cat_cols.append(col)
    return time_cols, metric_cols, cat_cols


def _resolve_axes(df, chart_type):
    cols = list(df.columns)
    time_cols, metric_cols, cat_cols = _classify_df(df)
    dim_cols = time_cols + cat_cols
    y = metric_cols[0] if metric_cols else cols[-1]
    x, color = None, None
    if chart_type == "scatter":
        x = metric_cols[0] if len(metric_cols) >= 2 else (dim_cols[0] if dim_cols else cols[0])
        y = metric_cols[1] if len(metric_cols) >= 2 else y
        color = cat_cols[0] if cat_cols else None
        return x, y, color
    if chart_type == "pie":
        x = cat_cols[0] if cat_cols else (time_cols[0] if time_cols else cols[0])
        return x, y, None
    if len(time_cols) >= 2:
        by_card = sorted(time_cols, key=lambda c: df[c].nunique(), reverse=True)
        x, color = by_card[0], by_card[1]
    elif len(time_cols) == 1 and cat_cols:
        x = time_cols[0]
        color = min(cat_cols, key=lambda c: df[c].nunique())
    elif len(time_cols) == 1:
        x = time_cols[0]
    elif len(cat_cols) >= 2:
        by_card = sorted(cat_cols, key=lambda c: df[c].nunique(), reverse=True)
        x, color = by_card[0], by_card[-1]
    elif cat_cols:
        x = cat_cols[0]
    else:
        x = cols[0]
    return x, y, color


def regenerate_chart(result, chart_type, question):
    if not result:
        return "", "No data to chart"
    df = pd.DataFrame(result)
    if df.empty or df.shape[1] < 2:
        return "", "Not enough columns to chart"
    applicable, reasons = get_applicable_chart_types(result)
    if chart_type not in applicable:
        return "", f"Cannot use {chart_type}: {reasons.get(chart_type, 'not applicable')}"
    try:
        cols = list(df.columns)
        _, metric_cols, cat_cols = _classify_df(df)
        x, y, color = _resolve_axes(df, chart_type)
        if len(cols) >= 4 and chart_type not in ("pie", "scatter"):
            group_cols = [c for c in [x, color] if c is not None]
            if group_cols and y in df.columns:
                try:
                    df = df.groupby(group_cols, as_index=False)[y].sum()
                except Exception:
                    pass
        title = question.capitalize() if question else "Query Results"
        common = dict(
            template="plotly_dark", height=400, title=title,
            color_discrete_sequence=["#00d4aa","#4d9fff","#f0a500","#ff4f4f","#a78bfa","#34d399"]
        )
        if chart_type == "pie":
            names_col = cat_cols[0] if cat_cols else cols[0]
            values_col = metric_cols[0] if metric_cols else cols[-1]
            fig = px.pie(df, names=names_col, values=values_col, hole=0.4, **common)
            fig.update_traces(textposition="outside", textinfo="percent+label")
        elif chart_type == "line":
            fig = px.line(df, x=x, y=y, color=color, markers=True, **common)
        elif chart_type == "scatter":
            sc_x = metric_cols[0] if len(metric_cols) >= 2 else x
            sc_y = metric_cols[1] if len(metric_cols) >= 2 else y
            fig = px.scatter(df, x=sc_x, y=sc_y, color=cat_cols[0] if cat_cols else None, **common)
        elif chart_type == "area":
            fig = px.area(df, x=x, y=y, color=color, **common)
        else:
            barmode = "group" if color else "relative"
            fig = px.bar(df, x=x, y=y, color=color, barmode=barmode, **common)

        fig.update_layout(
            paper_bgcolor="#090e14",
            plot_bgcolor="#090e14",
            margin=dict(l=50, r=20, t=50, b=60),
            font=dict(family="Space Mono, monospace", size=11, color="#5a7a94"),
            title_font=dict(family="DM Sans", size=13, color="#ffffff"),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=10), bgcolor="rgba(0,0,0,0)"
            ),
            xaxis=dict(gridcolor="#1c2635", linecolor="#1c2635", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="#1c2635", linecolor="#1c2635", tickfont=dict(size=10)),
        )

        os.makedirs("data/charts", exist_ok=True)
        chart_id = str(uuid.uuid4())[:8]
        path = f"data/charts/chart_{chart_id}.html"
        fig.write_html(path, include_plotlyjs="cdn", full_html=True)
        return path, None
    except Exception as e:
        return "", f"Chart error: {str(e)}"


# ─────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\$+', '', text)
    text = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', text)
    return text.strip()


def parse_insights(text: str) -> list:
    text = sanitize_text(text)
    if not text:
        return []
    text = re.sub(r'\*{1,2}(\d+[\.\)])\*{1,2}', r'\1', text)
    parts = re.split(r'(?:^|\n)\s*\d+[\.\):]\s+', text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
    if len(parts) >= 2:
        return parts
    parts = re.split(r'\n\s*[-\*]\s+', text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
    if len(parts) >= 2:
        return parts
    parts = re.split(r'\n{2,}', text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
    if len(parts) >= 2:
        return parts
    parts = re.split(r'\n', text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 40]
    if len(parts) >= 2:
        return parts
    return [text]


def render_agent_pipeline(active_step: int = -1, done: bool = False):
    steps = ["CONTEXT", "PLANNER", "SQL", "ANALYSIS", "VIZ"]
    html = '<div class="agent-pipeline">'
    for i, s in enumerate(steps):
        cls = "done" if (done or i < active_step) else ("active" if i == active_step else "")
        html += f'<div class="agent-step {cls}"><div class="dot"></div>{s}</div>'
        if i < len(steps) - 1:
            html += '<span class="agent-sep">›</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_insights(insights_text: str):
    st.markdown('<div class="insights-header">Key Insights</div>', unsafe_allow_html=True)
    items = parse_insights(insights_text)
    for i, item in enumerate(items, 1):
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-num">#{i:02d}</div>
            <div class="insight-text">{item}</div>
        </div>""", unsafe_allow_html=True)


def render_chart(chart_path, chart_type, result, question, chart_key, msg_idx=-1):
    if not chart_path or chart_type == "none":
        return False
    if msg_idx >= 0 and msg_idx in st.session_state.chart_overrides:
        override = st.session_state.chart_overrides[msg_idx]
        chart_path = override.get("chart_path", chart_path)
        chart_type = override.get("chart_type", chart_type)

    applicable, reasons = get_applicable_chart_types(result)
    dropdown_options = applicable if applicable else CHART_OPTIONS
    current_idx = dropdown_options.index(chart_type) if chart_type in dropdown_options else 0

    hcol1, hcol2 = st.columns([2, 1])
    with hcol1:
        badge = f'<span class="chart-type-badge">↗ {chart_type}</span>' if chart_type else ""
        st.markdown(f'<div class="section-label">Visualization {badge}</div>', unsafe_allow_html=True)
    with hcol2:
        selected = st.selectbox(
            "chart_type", options=dropdown_options, index=current_idx,
            key=f"chart_select_{chart_key}", label_visibility="collapsed",
            help="Only compatible chart types shown"
        )
        if selected != chart_type:
            new_path, error = regenerate_chart(result, selected, question)
            if new_path:
                chart_path, chart_type = new_path, selected
                if msg_idx >= 0:
                    st.session_state.chart_overrides[msg_idx] = {
                        "chart_type": selected, "chart_path": new_path
                    }
                st.rerun()
            else:
                st.markdown(
                    f'<div style="font-size:10px;color:#ff4f4f;font-family:Space Mono,monospace;padding:4px 0">{error}</div>',
                    unsafe_allow_html=True
                )

    try:
        with open(chart_path, "r", encoding="utf-8") as f:
            chart_html = f.read()
        st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
        st.components.v1.html(chart_html, height=420)
        st.markdown('</div>', unsafe_allow_html=True)
        st.download_button(
            label="↓ Export Chart",
            data=chart_html.encode("utf-8"),
            file_name=f"chart_{chart_key}.html",
            mime="text/html",
            key=f"dl_chart_{chart_key}"
        )
        return True
    except Exception:
        return False


def _get_full_csv(sql: str) -> bytes:
    """Re-execute SQL without LIMIT to get complete dataset for CSV export."""
    try:
        # Strip any LIMIT clause we added for UI display
        import re as _re
        full_sql = _re.sub(r'\s+LIMIT\s+\d+\s*;?\s*$', ';', sql.strip(), flags=_re.IGNORECASE)
        if not full_sql.endswith(';'):
            full_sql += ';'
        from app.core.database import run_query
        df_full = run_query(full_sql)
        return df_full.to_csv(index=False).encode("utf-8")
    except Exception as e:
        logger.error(f"Full CSV export failed: {e}")
        return b""


def render_table(result, sql, slider_key):
    if not result:
        return False
    df = pd.DataFrame(result)
    if df.empty:
        return False

    st.markdown('<div class="section-label">Data</div>', unsafe_allow_html=True)

    n_rows = len(df)
    # Capped if we hit the 100-row UI limit
    is_capped = n_rows >= 100

    if is_capped:
        st.markdown(
            f'<div class="row-limit-banner">Showing first {n_rows:,} rows · CSV export contains full dataset</div>',
            unsafe_allow_html=True
        )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(
            f'<div style="font-family:Space Mono,monospace;font-size:10px;color:#3a5068">'
            f'{n_rows:,} rows · {len(df.columns)} columns</div>',
            unsafe_allow_html=True
        )
    with col_b:
        if is_capped and sql:
            # Re-execute without LIMIT — gives user the complete dataset
            csv_data = _get_full_csv(sql)
            st.download_button(
                label="↓ Full CSV",
                data=csv_data if csv_data else df.to_csv(index=False).encode("utf-8"),
                file_name="query_result_full.csv",
                mime="text/csv",
                key=f"dl_{slider_key}"
            )
        else:
            st.download_button(
                label="↓ CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="query_result.csv",
                mime="text/csv",
                key=f"dl_{slider_key}"
            )

    st.dataframe(df, use_container_width=True)

    if sql:
        with st.expander("▸ SQL Query"):
            st.code(sql, language="sql")
    return True


def render_assistant_turn(insights, result, chart_path, sql, chart_type,
                          slider_key, question="", msg_idx=-1, agents_done=True):
    render_agent_pipeline(done=agents_done)
    if insights:
        render_insights(insights)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    has_chart = bool(chart_path and chart_type != "none")
    has_table = bool(result)

    if has_chart and has_table:
        col1, col2 = st.columns([1.4, 1])
        with col1:
            render_chart(chart_path, chart_type, result, question, chart_key=slider_key, msg_idx=msg_idx)
        with col2:
            render_table(result, sql, slider_key)
    elif has_chart:
        render_chart(chart_path, chart_type, result, question, chart_key=slider_key, msg_idx=msg_idx)
    elif has_table:
        render_table(result, sql, slider_key)


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    n_q = st.session_state.query_count
    st.markdown(f"""
    <div class="sidebar-brand">
        <div class="logo-mark">QueryMind</div>
        <div class="logo-sub">AI Analyst · NL→SQL</div>
        <div class="status-line">
            <span class="status-dot"></span>OLIST · MySQL · llama-3.3-70b
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Example Queries</div>', unsafe_allow_html=True)

    example_questions = [
        "What is the total revenue by customer state?",
        "Which product categories generate the most revenue?",
        "What is the monthly order trend throughout 2017 and 2018?",
        "Which sellers have the highest number of delivered orders?",
        "What is the average delivery time by customer state?",
        "What percentage of orders were delivered late compared to the estimated date?",
        "What is the average review score by product category?",
        "Which payment methods are most popular and what is their average order value?",
    ]

    for i, q in enumerate(example_questions):
        if st.button(q, key=f"ex_{i}",
                     disabled=st.session_state.pending_prompt is not None):
            logger.info(f"Example question selected: {q}")
            st.session_state.pending_prompt = q
            st.rerun()

    st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)

    if n_q > 0:
        st.markdown(
            f'<div style="font-family:Space Mono,monospace;font-size:10px;color:#3a5068;margin-bottom:8px">'
            f'{n_q} quer{"y" if n_q == 1 else "ies"} this session</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="new-session-btn">', unsafe_allow_html=True)
    if st.button("⟳  Clear Session", key="new_session"):
        logger.info(f"New session started")
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.pending_prompt = None
        st.session_state.chart_overrides = {}
        st.session_state.query_count = 0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────
n_q = st.session_state.query_count
st.markdown(f"""
<div class="main-header">
    <div>
        <div class="main-title">Query<span>Mind</span></div>
        <div class="main-subtitle">Conversational multi-agent analytics engine</div>
    </div>
    <div class="header-stats">
        <div class="header-stat">
            <div class="val">9</div>
            <div class="lbl">Tables</div>
        </div>
        <div class="header-divider"></div>
        <div class="header-stat">
            <div class="val">1.4M</div>
            <div class="lbl">Rows</div>
        </div>
        <div class="header-divider"></div>
        <div class="header-stat">
            <div class="val">{n_q}</div>
            <div class="lbl">Queries</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# PIPELINE HTML BUILDER
# ─────────────────────────────────────────
AGENT_STEPS = [("contextualizer","CONTEXT"),("planner","PLANNER"),
               ("sql_agent","SQL"),("analysis","ANALYSIS"),("viz","VIZ")]

def render_pipeline_html(current_step_idx: int, done: bool = False) -> str:
    steps = [s[1] for s in AGENT_STEPS]
    html = '<div class="agent-pipeline">'
    for i, s in enumerate(steps):
        cls = "done" if (done or i < current_step_idx) else ("active" if i == current_step_idx else "")
        html += f'<div class="agent-step {cls}"><div class="dot"></div>{s}</div>'
        if i < len(steps) - 1:
            html += '<span class="agent-sep">›</span>'
    html += '</div>'
    return html


# ─────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="bigmark">⬡</div>
        <h3>Ready for analysis</h3>
        <p>Ask a question in plain English. The agent pipeline will generate SQL,
        execute it against the Olist dataset, and return insights with a visualization.</p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# CHAT HISTORY
# ─────────────────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="user-bubble">
            <div class="user-avatar">👤</div>
            <div class="user-text">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        render_assistant_turn(
            insights=msg.get("insights", ""),
            result=msg.get("result"),
            chart_path=msg.get("chart_path"),
            sql=msg.get("sql"),
            chart_type=msg.get("chart_type", ""),
            slider_key=f"history_slider_{idx}",
            question=msg.get("question", ""),
            msg_idx=idx,
            agents_done=True
        )
        st.markdown('<div class="convo-divider"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
# INPUT HANDLING
# ─────────────────────────────────────────
chat_prompt = st.chat_input("Ask a data question...")

if chat_prompt:
    prompt = chat_prompt
elif st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
else:
    prompt = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.query_count += 1

    st.markdown(f"""
    <div class="user-bubble">
        <div class="user-avatar">👤</div>
        <div class="user-text">{prompt}</div>
    </div>
    """, unsafe_allow_html=True)

    pipeline_placeholder  = st.empty()
    insights_placeholder  = st.empty()
    pipeline_placeholder.markdown(render_pipeline_html(0), unsafe_allow_html=True)

    data = {}
    logger.info(f"Sending API request: session={st.session_state.session_id}, question='{prompt[:50]}'")

    try:
        with requests.get(
            f"{API_URL}/query/stream",
            params={"question": prompt, "session_id": st.session_state.session_id},
            stream=True, timeout=120
        ) as resp:
            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8") if isinstance(line, bytes) else line
                if not line.startswith("data: "):
                    continue
                try:
                    event = json.loads(line[6:])
                except Exception:
                    continue

                etype = event.get("type")

                if etype == "agent_start":
                    step = event.get("step", 1) - 1
                    pipeline_placeholder.markdown(render_pipeline_html(step), unsafe_allow_html=True)

                elif etype == "result":
                    data = event
                    pipeline_placeholder.markdown(render_pipeline_html(0, done=True), unsafe_allow_html=True)
                    raw_insights = sanitize_text(data.get("insights", ""))
                    words = raw_insights.split()
                    streamed = ""
                    for w in words:
                        streamed += w + " "
                        insights_placeholder.markdown(
                            f'<div style="font-size:13px;color:#ffffff;line-height:1.7;'
                            f'font-family:DM Sans,sans-serif;padding:4px 0">'
                            f'{streamed}<span class="typing-cursor"></span></div>',
                            unsafe_allow_html=True
                        )
                        time.sleep(0.016)
                    insights_placeholder.empty()

                elif etype == "error":
                    logger.error(f"Agent error: {event.get('message')}")
                    st.error(f"Agent error: {event.get('message')}")
                    break

    except Exception as e:
        logger.error(f"API connection error: {str(e)}")
        st.error(f"Connection error: {e}")
        st.stop()

    insights   = data.get("insights", "")
    result     = data.get("result", [])
    chart_path = data.get("chart_path", "")
    chart_type = data.get("chart_type", "")
    sql        = data.get("sql", "")

    live_msg_idx = len(st.session_state.messages)
    live_key     = f"live_{uuid.uuid4()}"

    if insights:
        render_insights(insights)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    has_chart = bool(chart_path and chart_type != "none")
    has_table = bool(result)

    if has_chart and has_table:
        col1, col2 = st.columns([1.4, 1])
        with col1:
            render_chart(chart_path, chart_type, result, prompt, chart_key=live_key, msg_idx=live_msg_idx)
        with col2:
            render_table(result, sql, live_key)
    elif has_chart:
        render_chart(chart_path, chart_type, result, prompt, chart_key=live_key, msg_idx=live_msg_idx)
    elif has_table:
        render_table(result, sql, live_key)

    st.session_state.messages.append({
        "role": "assistant",
        "insights": insights,
        "chart_path": chart_path,
        "chart_type": chart_type,
        "result": result,
        "sql": sql,
        "question": prompt
    })