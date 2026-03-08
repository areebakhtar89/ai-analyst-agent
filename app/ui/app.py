import sys
import os

# Ensure project root is in path regardless of where Streamlit is launched from
# This fixes "No module named 'app.core'" when running from app/ui/
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
    page_title="AI Analyst Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; height: 0; min-height: 0; padding: 0; }
[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; padding: 0 !important; display: none !important; }
.stAppHeader { height: 0 !important; display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.stApp { background-color: #0d0d0d; }
.block-container { padding-top: 1.5rem !important; }

[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #222 !important;
}
[data-testid="stSidebar"] * { color: #ccc !important; }

.sidebar-logo {
    padding: 8px 0 24px 0;
    border-bottom: 1px solid #222;
    margin-bottom: 20px;
}
.sidebar-logo h2 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 18px; font-weight: 600;
    color: #f0f0f0 !important; margin: 0;
    letter-spacing: -0.5px;
}
.sidebar-logo span {
    font-size: 11px; color: #999 !important;
    letter-spacing: 2px; text-transform: uppercase;
}
.sidebar-section {
    font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
    color: #888 !important; margin: 20px 0 8px 0;
    padding-bottom: 4px; border-bottom: 1px solid #1e1e1e;
}

[data-testid="stSidebar"] .stButton button {
    background: #161616 !important; border: 1px solid #252525 !important;
    color: #ccc !important; border-radius: 6px !important;
    font-size: 12px !important; font-family: 'IBM Plex Sans', sans-serif !important;
    text-align: left !important; padding: 8px 12px !important;
    width: 100% !important; transition: all 0.15s ease !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: #1e1e1e !important; border-color: #f0a500 !important;
    color: #f0a500 !important;
}

/* User question pill — bot icon prefix */
.user-question {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 20px;
    padding: 8px 18px 8px 12px;
    font-size: 14px; color: #f0f0f0;
    font-family: 'IBM Plex Sans', sans-serif;
    margin: 4px 0;
}
.user-question .bot-icon {
    width: 24px; height: 24px;
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    line-height: 1;
}

/* Agent pipeline */
.agent-pipeline {
    display: flex; align-items: center; gap: 0;
    margin: 12px 0 20px 0; background: #111;
    border: 1px solid #1e1e1e; border-radius: 8px;
    padding: 10px 16px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px;
}
.agent-step { display: flex; align-items: center; gap: 6px; color: #555; padding: 0 12px 0 0; white-space: nowrap; }
.agent-step.done { color: #f0a500; }
.agent-step.active { color: #ffffff; }
.agent-step .dot { width: 6px; height: 6px; border-radius: 50%; background: #2a2a2a; flex-shrink: 0; }
.agent-step.done .dot { background: #f0a500; }
.agent-step.active .dot { background: #fff; animation: pulse 0.8s infinite; }
.agent-sep { color: #252525; padding: 0 4px; }

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.7); }
}

/* Insights */
.insights-header {
    font-family: 'IBM Plex Mono', monospace; font-size: 10px;
    letter-spacing: 2px; text-transform: uppercase; color: #999; margin-bottom: 10px;
}
.insight-card {
    display: flex; gap: 14px; align-items: flex-start;
    background: #111; border: 1px solid #222;
    border-left: 3px solid #f0a500; border-radius: 6px;
    padding: 12px 16px; margin-bottom: 8px;
}
.insight-num {
    font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    color: #f0a500; font-weight: 600; min-width: 20px; padding-top: 1px;
}
.insight-text { font-size: 13px; color: #d8d8d8; line-height: 1.6; }

/* Section labels — brighter */
.section-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 10px;
    letter-spacing: 2px; text-transform: uppercase;
    color: #999; margin-bottom: 8px;
}
.chart-type-badge {
    display: inline-block; background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 4px; padding: 2px 8px;
    font-family: 'IBM Plex Mono', monospace; font-size: 10px;
    color: #f0a500; margin-left: 8px; vertical-align: middle; text-transform: uppercase;
}

/* Chart wrapper with border */
.chart-wrapper {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    overflow: hidden;
    background: #0f0f0f;
    padding: 4px;
    margin-top: 4px;
}

/* Download buttons */
.stDownloadButton button {
    background: #1a1a1a !important; border: 1px solid #2a2a2a !important;
    color: #aaa !important; font-size: 11px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    border-radius: 4px !important; padding: 4px 12px !important;
}
.stDownloadButton button:hover {
    border-color: #f0a500 !important; color: #f0a500 !important;
}

/* Chat input */
[data-testid="stChatInput"] { border-top: 1px solid #1a1a1a !important; background: #0d0d0d !important; }
[data-testid="stChatInput"] textarea {
    background: #111 !important; border: 1px solid #222 !important;
    color: #f0f0f0 !important; border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important; font-size: 14px !important;
}

/* Typing cursor */
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.typing-cursor {
    display: inline-block; width: 2px; height: 14px;
    background: #f0a500; margin-left: 2px;
    vertical-align: middle; animation: blink 0.8s step-end infinite;
}

/* New session btn */
.new-session-btn button {
    background: transparent !important; border: 1px solid #252525 !important;
    color: #777 !important; font-size: 11px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    border-radius: 4px !important; width: 100% !important; margin-top: 8px !important;
}
.new-session-btn button:hover { border-color: #f0a500 !important; color: #f0a500 !important; }

[data-testid="stDataFrame"] {
    border: 1px solid #1e1e1e !important; border-radius: 6px !important; overflow: hidden !important;
}

/* Selectbox styling */
[data-testid="stSelectbox"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important; letter-spacing: 2px !important;
    text-transform: uppercase !important; color: #666 !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #161616 !important; border: 1px solid #2a2a2a !important;
    color: #f0a500 !important; border-radius: 4px !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 12px !important;
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
# Chart type overrides per message index: {msg_idx: chart_type}
if "chart_overrides" not in st.session_state:
    st.session_state.chart_overrides = {}


# ─────────────────────────────────────────
# CHART TYPE SWITCHER — regenerate chart client-side
# ─────────────────────────────────────────

CHART_OPTIONS = ["bar", "line", "scatter", "pie", "area"]


def get_applicable_chart_types(result: list) -> tuple[list, dict]:
    """
    Analyse the result data and return:
    - applicable: list of chart types that will work correctly
    - reasons: dict of {chart_type: reason_why_not} for inapplicable ones
    """
    if not result:
        return [], {}

    df = pd.DataFrame(result)
    cols = list(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = [c for c in cols if c not in numeric_cols]
    n_rows = len(df)

    applicable = []
    reasons = {}

    # BAR — needs at least 1 category + 1 numeric
    if cat_cols and numeric_cols:
        applicable.append("bar")
    else:
        reasons["bar"] = "needs a category column and a numeric column"

    # LINE — needs a time/ordered column + numeric; works on any ordered category too
    if numeric_cols and len(cols) >= 2:
        applicable.append("line")
    else:
        reasons["line"] = "needs at least one numeric column"

    # SCATTER — needs 2 numeric columns
    if len(numeric_cols) >= 2:
        applicable.append("scatter")
    else:
        reasons["scatter"] = "needs at least 2 numeric columns"

    # PIE — needs 1 category + 1 numeric, and ≤ 12 slices (more = unreadable)
    if cat_cols and numeric_cols and n_rows <= 12:
        applicable.append("pie")
    elif cat_cols and numeric_cols and n_rows > 12:
        reasons["pie"] = f"too many slices ({n_rows} rows) — pie charts work best with ≤12 categories"
    else:
        reasons["pie"] = "needs a category column and a numeric column"

    # AREA — same as line
    if numeric_cols and len(cols) >= 2:
        applicable.append("area")
    else:
        reasons["area"] = "needs at least one numeric column"

    return applicable, reasons


# Column classification keywords (mirrors visualization.py)
_TIME_KW     = ["date","time","month","year","day","week","quarter"]
_METRIC_KW   = ["revenue","sales","amount","price","total","count",
                 "profit","cost","value","qty","quantity","avg","sum"]
_CATEGORY_KW = ["name","region","segment","category","type","status",
                 "country","city","product","brand","department"]

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
    """
    Resolve x, y, color correctly for any column combination.

    Key cases:
    - year + month + metric  -> x=month (high cardinality), color=year (low cardinality)
    - region + product + metric -> x=product, color=region
    - time + category + metric -> x=time, color=category
    - 2 cols -> x=dim, y=metric, no color
    """
    cols = list(df.columns)
    time_cols, metric_cols, cat_cols = _classify_df(df)
    dim_cols = time_cols + cat_cols

    y = metric_cols[0] if metric_cols else cols[-1]
    x = None
    color = None

    if chart_type == "scatter":
        x = metric_cols[0] if len(metric_cols) >= 2 else (dim_cols[0] if dim_cols else cols[0])
        y = metric_cols[1] if len(metric_cols) >= 2 else y
        color = cat_cols[0] if cat_cols else None
        return x, y, color

    if chart_type == "pie":
        x = cat_cols[0] if cat_cols else (time_cols[0] if time_cols else cols[0])
        return x, y, None

    # 2+ time cols (e.g. year + month): highest cardinality = x, lowest = color
    if len(time_cols) >= 2:
        by_card = sorted(time_cols, key=lambda c: df[c].nunique(), reverse=True)
        x = by_card[0]
        color = by_card[1]
    # 1 time + categories: x=time, color=lowest-cardinality category
    elif len(time_cols) == 1 and cat_cols:
        x = time_cols[0]
        color = min(cat_cols, key=lambda c: df[c].nunique())
    # 1 time only
    elif len(time_cols) == 1:
        x = time_cols[0]
    # No time, 2+ categories: x=highest cardinality, color=lowest
    elif len(cat_cols) >= 2:
        by_card = sorted(cat_cols, key=lambda c: df[c].nunique(), reverse=True)
        x = by_card[0]
        color = by_card[-1]
    elif cat_cols:
        x = cat_cols[0]
    else:
        x = cols[0]

    return x, y, color


def regenerate_chart(result, chart_type, question):
    """Regenerate chart for the given type. Returns (chart_path, error_message)."""
    logger.info(f"Regenerating chart: type={chart_type}, question='{question[:50]}...' if len(question) > 50 else question")
    
    if not result:
        logger.warning("No data provided for chart regeneration")
        return "", "No data to chart"

    df = pd.DataFrame(result)
    if df.empty or df.shape[1] < 2:
        return "", "Not enough columns to chart"

    applicable, reasons = get_applicable_chart_types(result)
    if chart_type not in applicable:
        reason = reasons.get(chart_type, "not applicable to this data")
        return "", f"Cannot use {chart_type} chart: {reason}"

    try:
        cols = list(df.columns)
        _, metric_cols, cat_cols = _classify_df(df)

        x, y, color = _resolve_axes(df, chart_type)

        # Aggregate extra dimensions away when 4+ cols (e.g. month+category+region+revenue).
        # Without this Plotly receives unaggregated rows and produces overlapping bars.
        if len(cols) >= 4 and chart_type not in ("pie", "scatter"):
            group_cols = [c for c in [x, color] if c is not None]
            if group_cols and y in df.columns:
                try:
                    df = df.groupby(group_cols, as_index=False)[y].sum()
                except Exception:
                    pass

        title = question.capitalize() if question else "Query Results"
        common = dict(template="plotly_dark", height=420, title=title)

        if chart_type == "pie":
            names_col  = cat_cols[0] if cat_cols else cols[0]
            values_col = metric_cols[0] if metric_cols else cols[-1]
            fig = px.pie(df, names=names_col, values=values_col, hole=0.35, **common)
            fig.update_traces(textposition="outside", textinfo="percent+label")
        elif chart_type == "line":
            fig = px.line(df, x=x, y=y, color=color, markers=True, **common)
        elif chart_type == "scatter":
            sc_x = metric_cols[0] if len(metric_cols) >= 2 else x
            sc_y = metric_cols[1] if len(metric_cols) >= 2 else y
            fig = px.scatter(df, x=sc_x, y=sc_y, color=cat_cols[0] if cat_cols else None, **common)
        elif chart_type == "area":
            fig = px.area(df, x=x, y=y, color=color, **common)
        else:  # bar
            barmode = "group" if color else "relative"
            fig = px.bar(df, x=x, y=y, color=color, barmode=barmode, **common)

        fig.update_layout(
            margin=dict(l=50, r=20, t=55, b=80),
            font=dict(size=12),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        import os
        os.makedirs("data/charts", exist_ok=True)
        chart_id = str(uuid.uuid4())[:8]
        path = f"data/charts/chart_{chart_id}.html"
        fig.write_html(path, include_plotlyjs="cdn", full_html=True)
        logger.info(f"Chart regenerated successfully: {chart_type} -> {path}")
        return path, None

    except Exception as e:
        logger.error(f"Chart regeneration failed: {chart_type} - {str(e)}")
        return "", f"Chart generation failed: {str(e)}"


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
    """
    Robustly split LLM insight text into individual cards.
    Handles all common LLM output formats in priority order:
      1. Numbered:   "1. text"  "2) text"  "**1.** text"
      2. Bullets:    "- text"   "* text"
      3. Paragraphs: blank line between chunks
      4. Lines:      single newline splits (if chunks are long enough)
      5. Fallback:   return whole text as one card
    """
    text = sanitize_text(text)
    if not text:
        return []

    # Strip markdown bold wrapping numbers: **1.** → 1.
    text = re.sub(r'\*{1,2}(\d+[\.\)])\*{1,2}', r'\1', text)

    # 1. Numbered lines: "1." "2)" "1:" at line start
    parts = re.split(r'(?:^|\n)\s*\d+[\.\):]\s+', text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
    if len(parts) >= 2:
        return parts

    # 2. Bullet points: "- " or "* " at line start
    parts = re.split(r'\n\s*[-\*]\s+', text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
    if len(parts) >= 2:
        return parts

    # 3. Blank-line separated paragraphs
    parts = re.split(r'\n{2,}', text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
    if len(parts) >= 2:
        return parts

    # 4. Single newline splits (only if chunks are substantial)
    parts = re.split(r'\n', text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 40]
    if len(parts) >= 2:
        return parts

    # 5. Fallback: single card
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
    st.markdown('<div class="insights-header">● KEY INSIGHTS</div>', unsafe_allow_html=True)
    items = parse_insights(insights_text)
    for i, item in enumerate(items, 1):
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-num">#{i:02d}</div>
            <div class="insight-text">{item}</div>
        </div>""", unsafe_allow_html=True)


def render_chart(chart_path: str, chart_type: str, result: list, question: str,
                 chart_key: str, msg_idx: int = -1):
    """Render chart with border, download, and smart chart type switcher."""
    if not chart_path or chart_type == "none":
        return False

    # ── Resolve any persisted override FIRST so badge shows correct type ──
    if msg_idx >= 0 and msg_idx in st.session_state.chart_overrides:
        override = st.session_state.chart_overrides[msg_idx]
        chart_path = override.get("chart_path", chart_path)
        chart_type = override.get("chart_type", chart_type)

    # Work out which chart types are actually valid for this data
    applicable, reasons = get_applicable_chart_types(result)
    dropdown_options = applicable if applicable else CHART_OPTIONS
    current_idx = dropdown_options.index(chart_type) if chart_type in dropdown_options else 0

    # ── Header row: label + badge + dropdown — badge uses already-resolved chart_type ──
    hcol1, hcol2 = st.columns([2, 1])
    with hcol1:
        badge = f'<span class="chart-type-badge">↗ {chart_type} chart</span>' if chart_type else ""
        st.markdown(f'<div class="section-label">VISUALIZATION {badge}</div>', unsafe_allow_html=True)
    with hcol2:
        selected = st.selectbox(
            "Switch chart type",
            options=dropdown_options,
            index=current_idx,
            key=f"chart_select_{chart_key}",
            label_visibility="collapsed",
            help="Only chart types compatible with this data are shown"
        )

        if selected != chart_type:
            new_path, error = regenerate_chart(result, selected, question)
            if new_path:
                chart_path = new_path
                chart_type = selected
                if msg_idx >= 0:
                    st.session_state.chart_overrides[msg_idx] = {
                        "chart_type": selected,
                        "chart_path": new_path
                    }
                st.rerun()  # force immediate badge + chart refresh
            else:
                st.markdown(
                    f'<div style="font-size:11px;color:#e05a5a;font-family:IBM Plex Mono,monospace;'
                    f'padding:4px 0">{error}</div>',
                    unsafe_allow_html=True
                )

    # ── Chart with border wrapper ──
    try:
        with open(chart_path, "r", encoding="utf-8") as f:
            chart_html = f.read()

        st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
        st.components.v1.html(chart_html, height=430)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="↓ Download Chart",
            data=chart_html.encode("utf-8"),
            file_name=f"chart_{chart_key}.html",
            mime="text/html",
            key=f"dl_chart_{chart_key}"
        )
        return True
    except Exception:
        return False


def render_table(result: list, sql: str, slider_key: str):
    """Render data table with CSV download and SQL expander."""
    if not result:
        return False
    df = pd.DataFrame(result)
    if df.empty:
        return False

    st.markdown('<div class="section-label">DATA TABLE</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(
            f'<div style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#999">'
            f'{len(df)} rows</div>', unsafe_allow_html=True
        )
    with col_b:
        st.download_button(
            label="↓ CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="query_result.csv",
            mime="text/csv",
            key=f"dl_{slider_key}"
        )

    max_rows = len(df)
    rows = st.slider("Rows", min_value=5, max_value=max_rows,
                     value=min(20, max_rows), key=slider_key) if max_rows > 5 else max_rows

    st.dataframe(df.head(rows), use_container_width=True)

    if sql:
        with st.expander("Show SQL"):
            st.code(sql, language="sql")
    return True


def render_assistant_turn(insights, result, chart_path, sql, chart_type,
                          slider_key, question="", msg_idx=-1, agents_done=True):
    render_agent_pipeline(done=agents_done)

    if insights:
        render_insights(insights)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    has_chart = bool(chart_path and chart_type != "none")
    has_table = bool(result)

    if has_chart and has_table:
        col1, col2 = st.columns([1.3, 1])
        with col1:
            render_chart(chart_path, chart_type, result, question,
                         chart_key=slider_key, msg_idx=msg_idx)
        with col2:
            render_table(result, sql, slider_key)
    elif has_chart:
        render_chart(chart_path, chart_type, result, question,
                     chart_key=slider_key, msg_idx=msg_idx)
    elif has_table:
        render_table(result, sql, slider_key)


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>AI Analyst</h2>
        <span>Multi-Agent · NL→SQL</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Example Questions</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="new-session-btn">', unsafe_allow_html=True)
    if st.button("⟳ New Session", key="new_session"):
        logger.info(f"Creating new session: {st.session_state.session_id} -> {str(uuid.uuid4())}")
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.pending_prompt = None
        st.session_state.chart_overrides = {}
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────
st.markdown("""
<div style="padding: 8px 0 24px 0; border-bottom: 1px solid #1a1a1a; margin-bottom: 24px;">
    <h1 style="font-family: IBM Plex Sans, sans-serif; font-size: 28px; font-weight: 600;
               color: #f0f0f0; margin: 0; letter-spacing: -0.5px;">
        AI Analyst Agent
    </h1>
    <p style="font-family: IBM Plex Mono, monospace; font-size: 11px; color: #555;
              letter-spacing: 1px; text-transform: uppercase; margin: 4px 0 0 0; color: #888 !important;">
        Conversational multi-agent analytics
    </p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# PIPELINE HTML BUILDER (used during live streaming)
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
# CHAT HISTORY
# ─────────────────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-question">'
            f'<div class="bot-icon">👤</div>'
            f'{msg["content"]}'
            f'</div>', unsafe_allow_html=True
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
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
        st.markdown(
            "<div style='height:32px;border-bottom:1px solid #1a1a1a;margin-bottom:32px'></div>",
            unsafe_allow_html=True
        )


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

    st.markdown(
        f'<div class="user-question">'
        f'<div class="bot-icon">👤</div>'
        f'{prompt}'
        f'</div>', unsafe_allow_html=True
    )
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    pipeline_placeholder = st.empty()
    insights_placeholder = st.empty()
    pipeline_placeholder.markdown(render_pipeline_html(0), unsafe_allow_html=True)

    data = {}

    logger.info(f"Sending API request: session={st.session_state.session_id}, question='{prompt[:50]}...' if len(prompt) > 50 else prompt")

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

                    # Stream insights word by word
                    raw_insights = sanitize_text(data.get("insights", ""))
                    words = raw_insights.split()
                    streamed = ""
                    for w in words:
                        streamed += w + " "
                        insights_placeholder.markdown(
                            f'<div style="font-size:13px;color:#d8d8d8;line-height:1.7;padding:4px 0">'
                            f'{streamed}<span class="typing-cursor"></span></div>',
                            unsafe_allow_html=True
                        )
                        time.sleep(0.018)
                    insights_placeholder.empty()

                elif etype == "error":
                    logger.error(f"Agent error: {event.get('message')}")
                    st.error(f"Agent error: {event.get('message')}")
                    break

    except Exception as e:
        logger.error(f"API connection error: {str(e)}")
        st.error(f"Connection error: {e}")
        st.stop()

    insights  = data.get("insights", "")
    result    = data.get("result", [])
    chart_path = data.get("chart_path", "")
    chart_type = data.get("chart_type", "")
    sql       = data.get("sql", "")

    # Figure out what index this assistant message will be
    live_msg_idx = len(st.session_state.messages)  # will be appended next
    live_key = f"live_{uuid.uuid4()}"

    if insights:
        render_insights(insights)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    has_chart = bool(chart_path and chart_type != "none")
    has_table = bool(result)

    if has_chart and has_table:
        col1, col2 = st.columns([1.3, 1])
        with col1:
            render_chart(chart_path, chart_type, result, prompt,
                         chart_key=live_key, msg_idx=live_msg_idx)
        with col2:
            render_table(result, sql, live_key)
    elif has_chart:
        render_chart(chart_path, chart_type, result, prompt,
                     chart_key=live_key, msg_idx=live_msg_idx)
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