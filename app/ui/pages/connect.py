"""
app/ui/pages/connect.py

3-step database connection + schema configuration page.

Step 1 — Connect    : enter credentials, test connection
Step 2 — Select     : pick which tables to use for NL2SQL
Step 3 — Describe   : add plain-English descriptions per table/column,
                       optionally rewrite with AI
"""

import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import requests

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
    --bg:#080b0f; --bg2:#0d1117; --bg3:#131920;
    --border:#1c2635; --border2:#243042;
    --accent:#00d4aa; --danger:#ff4f4f; --green:#00e676;
    --text:#ffffff; --text-dim:#cccccc; --text-muted:#3a5068;
    --mono:'Space Mono',monospace; --sans:'DM Sans',sans-serif;
}
html,body,[class*="css"]{ font-family:var(--sans); background:var(--bg) !important; }
#MainMenu,footer,header{ visibility:hidden; height:0; }
[data-testid="stHeader"],.stAppHeader,[data-testid="stToolbar"]{ display:none !important; }
.stApp{ background:var(--bg) !important; }
.block-container{ padding-top:0 !important; padding-left:2rem !important; padding-right:2rem !important; max-width:1300px !important; }
[data-testid="stSidebar"]{ background:var(--bg2) !important; border-right:1px solid var(--border) !important; }
[data-testid="stSidebar"] *{ color:var(--text-dim) !important; }

.page-header{ padding:24px 0 20px 0; border-bottom:1px solid var(--border); margin-bottom:28px; }
.page-title{ font-family:var(--mono); font-size:22px; font-weight:700; color:var(--text); }
.page-title span{ color:var(--accent); }
.page-sub{ font-family:var(--mono); font-size:10px; color:var(--text-muted); letter-spacing:2px; text-transform:uppercase; margin-top:6px; }

.steps{ display:flex; gap:0; margin-bottom:28px; }
.step{ display:flex; align-items:center; gap:8px; padding:10px 20px;
       font-family:var(--mono); font-size:10px; letter-spacing:1px;
       color:var(--text-muted); border:1px solid var(--border); background:var(--bg2); }
.step:first-child{ border-radius:4px 0 0 4px; }
.step:last-child{ border-radius:0 4px 4px 0; }
.step.active{ color:var(--accent); border-color:var(--accent); background:#0a1e18; }
.step.done{ color:var(--green); border-color:#1a3a2a; background:#091410; }
.step .num{ font-weight:700; font-size:12px; }

.sec{ font-family:var(--mono); font-size:9px; letter-spacing:3px; text-transform:uppercase;
      color:var(--text-muted); margin:24px 0 14px 0;
      display:flex; align-items:center; gap:8px; }
.sec::before{ content:''; display:inline-block; width:12px; height:1px; background:var(--accent); }

.banner{ border-radius:4px; padding:10px 16px; font-family:var(--mono); font-size:11px;
         display:flex; align-items:center; gap:10px; margin-bottom:16px; }
.banner.ok { background:#091410; border:1px solid #1a3a2a; color:var(--green); }
.banner.err{ background:#1e0a0a; border:1px solid #4a1a1a; color:var(--danger); }

.table-card{ background:var(--bg2); border:1px solid var(--border); border-radius:6px;
             padding:14px 18px; margin-bottom:8px; }
.table-card.on { border-color:var(--accent); }
.table-card.off{ opacity:0.45; }
.tc-head{ display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.tc-name{ font-family:var(--mono); font-size:12px; font-weight:700; color:var(--accent); }
.tc-meta{ font-family:var(--mono); font-size:10px; color:var(--text-muted); }
.col-pills{ display:flex; flex-wrap:wrap; gap:4px; }
.cpill{ background:var(--bg3); border:1px solid var(--border); border-radius:3px;
        padding:2px 7px; font-family:var(--mono); font-size:9px; color:var(--text-dim); }
.cpill .ct{ color:var(--text-muted); margin-left:3px; }

.stButton button{
    background:var(--bg3) !important; border:1px solid var(--border) !important;
    color:var(--text-dim) !important; border-radius:4px !important;
    font-family:var(--mono) !important; font-size:11px !important;
    padding:8px 14px !important; transition:all 0.15s !important; }
.stButton button:hover{ border-color:var(--accent) !important; color:var(--accent) !important; }
.primary button{ background:var(--accent) !important; border:none !important;
                 color:#000 !important; font-weight:700 !important; font-size:12px !important;
                 letter-spacing:1px !important; }
.primary button:hover{ opacity:0.85 !important; }
.ai-btn button{ background:#0a1e18 !important; border:1px solid var(--accent) !important;
                color:var(--accent) !important; font-size:10px !important;
                font-family:var(--mono) !important; padding:4px 10px !important; }
.save-btn button{ background:#0a1420 !important; border:1px solid #4d9fff !important;
                  color:#4d9fff !important; font-size:10px !important;
                  font-family:var(--mono) !important; }

[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{
    background:var(--bg3) !important; border:1px solid var(--border2) !important;
    color:var(--text) !important; border-radius:4px !important;
    font-family:var(--sans) !important; font-size:13px !important; }
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{
    border-color:var(--accent) !important; box-shadow:0 0 0 1px var(--accent) !important; }
[data-testid="stTextInput"] label,[data-testid="stTextArea"] label,[data-testid="stNumberInput"] label{
    font-family:var(--mono) !important; font-size:9px !important;
    color:var(--text-muted) !important; letter-spacing:1px !important; text-transform:uppercase !important; }
[data-testid="stNumberInput"] input{
    background:var(--bg3) !important; border:1px solid var(--border2) !important; color:var(--text) !important; }
[data-testid="stSelectbox"]>div>div{
    background:var(--bg3) !important; border:1px solid var(--border2) !important;
    color:var(--text) !important; font-family:var(--mono) !important; font-size:12px !important; }
[data-testid="stCheckbox"] label{ font-family:var(--sans) !important; font-size:13px !important; color:var(--text-dim) !important; }

.fallback-btn button{ background:transparent !important; border:1px solid #3a5068 !important;
                    color:#3a5068 !important; font-size:10px !important;
                    font-family:var(--mono) !important; letter-spacing:1px !important;
                    padding:6px 14px !important; }
.fallback-btn button:hover{ border-color:#ff4f4f !important; color:#ff4f4f !important; }
.saved-card{ background:var(--bg2); border:1px solid var(--border);
             border-radius:6px; padding:14px 18px; margin-bottom:8px;
             transition:border-color 0.15s; }
.saved-card:hover{ border-color:var(--border2); }
.saved-card-top{ display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
.saved-db{ font-family:var(--mono); font-size:12px; font-weight:700; color:var(--accent); }
.saved-meta{ font-family:var(--mono); font-size:10px; color:var(--text-muted); }
.saved-tags{ display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; }
.stag{ background:var(--bg3); border:1px solid var(--border); border-radius:3px;
       padding:2px 8px; font-family:var(--mono); font-size:9px; color:var(--text-muted); }
.stag.green{ border-color:#1a3a2a; color:var(--green); background:#091410; }
.load-btn button{ background:#0a1e18 !important; border:1px solid var(--accent) !important;
                  color:var(--accent) !important; font-size:10px !important;
                  font-family:var(--mono) !important; letter-spacing:1px !important; }
.ready{ display:inline-flex; align-items:center; gap:8px; background:#091410;
        border:1px solid var(--green); border-radius:4px; padding:8px 16px;
        font-family:var(--mono); font-size:11px; color:var(--green); margin-top:16px; }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
_defaults = {
    "step":             1,
    "conn_status":      None,   # None | "ok" | "err"
    "conn_message":     "",
    "conn_schema":      [],     # raw list from GET /schema
    "conn_config":      {},
    "db_type":          "mysql",
    "tbl_selected":     {},     # {table_name: bool}
    "tbl_descs":        {},     # {table_name: str}
    "col_descs":        {},     # {table_name: {col_name: str}}
    "schema_saved":     False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="page-title">Query<span>Mind</span> · Connect</div>
  <div class="page-sub">Connect database · Select tables · Describe schema · Start querying</div>
</div>""", unsafe_allow_html=True)


# ── Step indicator ────────────────────────────────────────────────────────────
def sc(n):
    s = st.session_state.step
    return "done" if s > n else ("active" if s == n else "")

# ── Saved configurations panel ────────────────────────────────────────────────
try:
    saved_resp = requests.get(f"{API_URL}/schema/saved", timeout=5).json()
    saved_list = saved_resp.get("configs", [])
except Exception:
    saved_list = []

if saved_list:
    st.markdown('<div class="sec">Saved Configurations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:Space Mono,monospace;font-size:10px;color:#3a5068;margin-bottom:14px">'
        'Previously saved schema configs. Click Load to restore descriptions and start querying instantly.</div>',
        unsafe_allow_html=True)

    for cfg in saved_list:
        db_icon = {"mysql":"🐬","postgresql":"🐘","sqlite":"🗃️","duckdb":"🦆"}.get(cfg["db_type"],"🗄️")
        desc_tag = '<span class="stag green">✓ descriptions saved</span>' if cfg["has_descriptions"] else '<span class="stag">no descriptions</span>'
        st.markdown(f"""
        <div class="saved-card">
          <div class="saved-card-top">
            <span class="saved-db">{db_icon} {cfg['db_name']}</span>
            <span class="saved-meta">{cfg['db_type'].upper()}</span>
          </div>
          <div class="saved-tags">
            <span class="stag">{cfg['table_count']} tables</span>
            <span class="stag">{cfg['selected_count']} selected</span>
            {desc_tag}
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="load-btn">', unsafe_allow_html=True)
        if st.button(f"⚡ Load {cfg['db_name']}", key=f"load_{cfg['filename']}"):
            with st.spinner(f"Loading {cfg['db_name']}..."):
                try:
                    r = requests.post(
                        f"{API_URL}/schema/load",
                        json={"filename": cfg["filename"]},
                        timeout=10
                    ).json()
                    if r.get("success"):
                        # Fetch full schema to populate Step 2/3 UI state
                        sr = requests.get(f"{API_URL}/schema/saved", timeout=5).json()
                        # Load the store directly into session state from the saved file
                        import json, os
                        fpath = os.path.join("data/schema_configs", cfg["filename"])
                        with open(fpath, "r") as f_in:
                            saved_data = json.load(f_in)
                        tables = saved_data.get("tables", [])
                        st.session_state.conn_schema  = tables
                        st.session_state.tbl_selected = {t["table"]: t.get("selected", True) for t in tables}
                        st.session_state.tbl_descs    = {t["table"]: t.get("description","") for t in tables}
                        st.session_state.col_descs    = {
                            t["table"]: {c["name"]: c.get("description","") for c in t.get("columns",[])}
                            for t in tables
                        }
                        st.session_state.conn_config  = {"type": cfg["db_type"], "database": cfg["db_name"]}
                        st.session_state.conn_status  = "ok"
                        st.session_state.conn_message = f"Loaded saved config: {cfg['db_name']}"
                        st.session_state.step         = 3
                        st.session_state.schema_saved = True
                        st.rerun()
                    else:
                        st.error(f"Load failed: {r.get('message','')}")
                except Exception as ex:
                    st.error(f"Error: {ex}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

st.markdown(f"""
<div class="steps">
  <div class="step {sc(1)}"><span class="num">01</span> CONNECT</div>
  <div class="step {sc(2)}"><span class="num">02</span> SELECT TABLES</div>
  <div class="step {sc(3)}"><span class="num">03</span> DESCRIBE SCHEMA</div>
</div>""", unsafe_allow_html=True)


# ════════════════════════════════════════
# STEP 1 — CONNECT
# ════════════════════════════════════════
st.markdown('<div class="sec">Database Connection</div>', unsafe_allow_html=True)

DB_LABELS = {"mysql":"🐬 MySQL","postgresql":"🐘 PostgreSQL","sqlite":"🗃️ SQLite","duckdb":"🦆 DuckDB"}
c1,c2,c3,c4 = st.columns(4)
for col, (key, label) in zip([c1,c2,c3,c4], DB_LABELS.items()):
    with col:
        if st.button(label, key=f"dt_{key}"):
            st.session_state.db_type = key
            st.session_state.conn_status = None
            st.rerun()

db_type = st.session_state.db_type
cfg = {"type": db_type}

if db_type in ("mysql", "postgresql"):
    a,b,c = st.columns([2,1,1])
    with a: cfg["host"]     = st.text_input("Host", value="localhost", key="h")
    with b: cfg["port"]     = st.number_input("Port", value=3306 if db_type=="mysql" else 5432, key="p")
    with c: cfg["database"] = st.text_input("Database", key="db")
    d,e = st.columns(2)
    with d: cfg["user"]     = st.text_input("Username", key="u")
    with e: cfg["password"] = st.text_input("Password", type="password", key="pw")
else:
    cfg["file"] = st.text_input("File Path", placeholder="data/analytics.duckdb", key="fp")

st.markdown('<div class="primary">', unsafe_allow_html=True)
if st.button("⚡  Connect", key="btn_connect"):
    with st.spinner("Connecting..."):
        try:
            r = requests.post(f"{API_URL}/connect", json=cfg, timeout=10).json()
            if r.get("success"):
                st.session_state.conn_status  = "ok"
                st.session_state.conn_message = r.get("message","Connected.")
                st.session_state.conn_config  = cfg
                # Fetch raw schema for Steps 2 & 3
                sr = requests.get(f"{API_URL}/schema", timeout=15).json()
                tables = sr.get("tables", [])
                st.session_state.conn_schema  = tables
                st.session_state.tbl_selected = {t["table"]: True for t in tables}
                st.session_state.tbl_descs    = {t["table"]: "" for t in tables}
                st.session_state.col_descs    = {
                    t["table"]: {c["name"]: "" for c in t.get("columns",[])}
                    for t in tables
                }
                st.session_state.step         = 2
                st.session_state.schema_saved = False
            else:
                st.session_state.conn_status  = "err"
                st.session_state.conn_message = r.get("message","Connection failed.")
        except Exception as ex:
            st.session_state.conn_status  = "err"
            st.session_state.conn_message = f"Cannot reach API: {ex}"
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.conn_status == "ok":
    db_label = st.session_state.conn_config.get("database") or st.session_state.conn_config.get("file","")
    st.markdown(
        f'<div class="banner ok">✓ Connected to <strong>{db_label}</strong>'
        f' · {len(st.session_state.conn_schema)} tables found</div>',
        unsafe_allow_html=True)
elif st.session_state.conn_status == "err":
    st.markdown(
        f'<div class="banner err">✕ {st.session_state.conn_message}</div>',
        unsafe_allow_html=True)


# ════════════════════════════════════════
# STEP 2 — SELECT TABLES
# ════════════════════════════════════════
if st.session_state.step >= 2 and st.session_state.conn_schema:
    st.markdown('<div class="sec">Select Tables for NL→SQL</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:Space Mono,monospace;font-size:10px;color:#3a5068;margin-bottom:14px">'
        'Only selected tables are shown to the AI when generating SQL. '
        'Deselect lookup or irrelevant tables to reduce noise.</div>',
        unsafe_allow_html=True)

    sa, sd, _ = st.columns([1,1,6])
    with sa:
        if st.button("✓ All", key="sel_all"):
            for t in st.session_state.conn_schema:
                st.session_state.tbl_selected[t["table"]] = True
            st.rerun()
    with sd:
        if st.button("✕ None", key="desel_all"):
            for t in st.session_state.conn_schema:
                st.session_state.tbl_selected[t["table"]] = False
            st.rerun()

    tables = st.session_state.conn_schema
    for i in range(0, len(tables), 2):
        row = tables[i:i+2]
        cols = st.columns(2)
        for col, t in zip(cols, row):
            with col:
                tname = t["table"]
                sel   = st.session_state.tbl_selected.get(tname, True)
                cls   = "on" if sel else "off"
                pills = "".join(
                    f'<span class="cpill">{c["name"]}<span class="ct">{c["type"]}</span></span>'
                    for c in t.get("columns",[])[:8]
                )
                if len(t.get("columns",[])) > 8:
                    pills += f'<span class="cpill" style="color:#3a5068">+{len(t["columns"])-8} more</span>'
                st.markdown(f"""
                <div class="table-card {cls}">
                  <div class="tc-head">
                    <span class="tc-name">{tname}</span>
                    <span class="tc-meta">{t.get('row_count',0):,} rows · {len(t.get('columns',[]))} cols</span>
                  </div>
                  <div class="col-pills">{pills}</div>
                </div>""", unsafe_allow_html=True)

                new_val = st.checkbox(f"Include {tname}", value=sel, key=f"chk_{tname}")
                if new_val != sel:
                    st.session_state.tbl_selected[tname] = new_val
                    try:
                        requests.post(f"{API_URL}/schema/table/select",
                                      json={"table": tname, "selected": new_val}, timeout=5)
                    except Exception:
                        pass
                    st.rerun()

    sel_count = sum(1 for v in st.session_state.tbl_selected.values() if v)
    st.markdown(
        f'<div style="font-family:Space Mono,monospace;font-size:10px;color:#3a5068;margin-top:8px">'
        f'{sel_count} of {len(tables)} tables selected</div>',
        unsafe_allow_html=True)

    if sel_count > 0 and st.session_state.step == 2:
        st.markdown('<div class="primary">', unsafe_allow_html=True)
        if st.button("→ Continue to Describe Schema", key="to_step3"):
            st.session_state.step = 3
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════
# STEP 3 — DESCRIBE SCHEMA
# ════════════════════════════════════════
if st.session_state.step >= 3:
    st.markdown('<div class="sec">Describe Schema</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:Space Mono,monospace;font-size:10px;color:#3a5068;margin-bottom:14px">'
        'Add plain-English descriptions so the AI understands your data. '
        '"Rewrite with AI" generates or improves any description automatically.</div>',
        unsafe_allow_html=True)

    selected_tables = [
        t for t in st.session_state.conn_schema
        if st.session_state.tbl_selected.get(t["table"], False)
    ]

    for t in selected_tables:
        tname = t["table"]
        with st.expander(
            f"📋  {tname}   ({t.get('row_count',0):,} rows · {len(t.get('columns',[]))} cols)",
            expanded=False
        ):
            # ── Table description ──────────────────────────────────────
            st.markdown(
                '<div style="font-family:Space Mono,monospace;font-size:9px;color:#3a5068;'
                'letter-spacing:2px;text-transform:uppercase;margin-bottom:6px">'
                'Table Description</div>', unsafe_allow_html=True)

            # key intentionally omitted — value always driven by session_state
            # so AI rewrites are reflected immediately after st.rerun()
            table_desc = st.text_area(
                "td_lbl", label_visibility="collapsed",
                value=st.session_state.tbl_descs.get(tname, ""),
                placeholder=f"What does the {tname} table contain? What business entity does it represent?",
                height=75)
            st.session_state.tbl_descs[tname] = table_desc

            ai1, _ = st.columns([1,5])
            with ai1:
                st.markdown('<div class="ai-btn">', unsafe_allow_html=True)
                if st.button("✦ Rewrite with AI", key=f"ai_t_{tname}"):
                    with st.spinner("Rewriting..."):
                        try:
                            res = requests.post(f"{API_URL}/schema/ai/rewrite", json={
                                "type": "table", "table": tname,
                                "columns": [c["name"] for c in t.get("columns",[])],
                                "current_description": table_desc
                            }, timeout=20).json()
                            if res.get("success"):
                                st.session_state.tbl_descs[tname] = res["description"]
                                st.rerun()
                            else:
                                err = res.get("message") or "Unknown error — check uvicorn terminal"
                                st.error(f"AI rewrite failed: {err}")
                        except Exception as ex:
                            st.error(f"Cannot reach API: {ex}")
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            # ── Column descriptions ────────────────────────────────────
            st.markdown(
                '<div style="font-family:Space Mono,monospace;font-size:9px;color:#3a5068;'
                'letter-spacing:2px;text-transform:uppercase;margin-bottom:10px">'
                'Column Descriptions</div>', unsafe_allow_html=True)

            for col in t.get("columns", []):
                cname = col["name"]
                ctype = col["type"]
                lc, rc = st.columns([3, 1])
                with lc:
                    st.markdown(
                        f'<div style="font-family:Space Mono,monospace;font-size:11px;'
                        f'color:#00d4aa;margin-bottom:2px">{cname} '
                        f'<span style="color:#3a5068;font-size:9px">({ctype})</span></div>',
                        unsafe_allow_html=True)
                    # key intentionally omitted — value always driven by session_state
                    # so AI rewrites reflect immediately after st.rerun()
                    col_desc = st.text_input(
                        f"cl_{tname}_{cname}", label_visibility="collapsed",
                        value=st.session_state.col_descs.get(tname,{}).get(cname,""),
                        placeholder=f"What does {cname} represent?")
                    if tname not in st.session_state.col_descs:
                        st.session_state.col_descs[tname] = {}
                    st.session_state.col_descs[tname][cname] = col_desc
                with rc:
                    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
                    st.markdown('<div class="ai-btn">', unsafe_allow_html=True)
                    if st.button("✦ AI", key=f"ai_c_{tname}_{cname}"):
                        with st.spinner("..."):
                            try:
                                res = requests.post(f"{API_URL}/schema/ai/rewrite", json={
                                    "type": "column", "table": tname,
                                    "column": cname, "col_type": ctype,
                                    "current_description": col_desc
                                }, timeout=20).json()
                                if res.get("success"):
                                    st.session_state.col_descs[tname][cname] = res["description"]
                                    st.rerun()
                                else:
                                    err = res.get("message") or "Unknown error — check uvicorn terminal"
                                    st.error(f"AI rewrite failed: {err}")
                            except Exception as ex:
                                st.error(f"Cannot reach API: {ex}")
                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ── Save this table ────────────────────────────────────────
            st.markdown('<div class="save-btn">', unsafe_allow_html=True)
            if st.button(f"💾  Save {tname}", key=f"save_{tname}"):
                try:
                    requests.post(f"{API_URL}/schema/table/describe", json={
                        "table":       tname,
                        "description": st.session_state.tbl_descs.get(tname,""),
                        "columns":     st.session_state.col_descs.get(tname,{})
                    }, timeout=10)
                    st.success(f"✓ {tname} saved")
                except Exception as ex:
                    st.error(f"Save failed: {ex}")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Save All ───────────────────────────────────────────────────────────────
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="primary">', unsafe_allow_html=True)
    if st.button("✓  Save All & Start Querying", key="save_all"):
        with st.spinner("Saving..."):
            errors = []
            for t in selected_tables:
                tname = t["table"]
                try:
                    requests.post(f"{API_URL}/schema/table/describe", json={
                        "table":       tname,
                        "description": st.session_state.tbl_descs.get(tname,""),
                        "columns":     st.session_state.col_descs.get(tname,{})
                    }, timeout=10)
                except Exception as ex:
                    errors.append(str(ex))
            if errors:
                st.error(f"Some saves failed: {errors}")
            else:
                st.session_state.schema_saved = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.schema_saved:
        st.markdown(
            '<div class="ready">✓ Schema ready · Return to main page to start querying</div>',
            unsafe_allow_html=True)

# ── Fallback to default ────────────────────────────────────────────────────────
if st.session_state.step >= 2:
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="border-top:1px solid #1c2635;padding-top:20px">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:Space Mono,monospace;font-size:9px;color:#3a5068;'
        'letter-spacing:2px;text-transform:uppercase;margin-bottom:10px">'
        'Reset Connection</div>',
        unsafe_allow_html=True)
    st.markdown('<div class="fallback-btn">', unsafe_allow_html=True)
    if st.button("↩  Disconnect & use default Olist DB", key="btn_fallback"):
        try:
            r = requests.post(f"{API_URL}/disconnect", timeout=10).json()
            if r.get("success"):
                # Reset all session state back to defaults
                for k, v in _defaults.items():
                    st.session_state[k] = v
                st.session_state.conn_status  = "ok"
                st.session_state.conn_message = "Using default Olist/.env connection"
                st.rerun()
        except Exception as ex:
            st.error(f"Disconnect failed: {ex}")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:Space Mono,monospace;font-size:9px;color:#3a5068;margin-top:8px">'
        'Clears the active connection and live schema. '
        'Agents fall back to the hardcoded Olist schema.</div>',
        unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)