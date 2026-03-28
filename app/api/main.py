"""
FastAPI backend for the AI Analyst Agent.
Handles requests, session memory, and SSE streaming for agent status.
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.agents.graph import build_graph
from app.core.database import set_active_connection, get_active_config
from app.core.connectors import test_connection, get_schema
from app.core.schema_store import (
    refresh_schema, reset_schema, set_table_selected,
    save_table_metadata, is_live_schema_available,
    list_saved_configs, load_saved_config
)
import math
import json
import time

app = FastAPI(title="AI Analyst Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()
session_memory_store = {}


@app.get("/")
def root():
    return {"message": "AI Analyst API running"}


# ── Connection ─────────────────────────────────────────────────────────────────

@app.post("/connect")
def connect_database(payload: dict):
    """
    Test connection, activate it, then immediately load live schema
    so agents stop using hardcoded schema_metadata.py.
    """
    success, message = test_connection(payload)
    if not success:
        return {"success": False, "message": message}

    set_active_connection(payload)

    # Load schema into schema_store — agents will use this from now on
    try:
        store = refresh_schema()
        table_count = len(store["tables"])
    except Exception as e:
        table_count = 0

    return {"success": True, "message": message, "table_count": table_count}


@app.get("/schema")
def fetch_schema():
    """
    Return raw schema of active connection.
    Used by connect.py Step 1 to display tables after connecting.
    """
    try:
        config = get_active_config()
        schema = get_schema(config)
        return {
            "success":   True,
            "db_type":   config.get("type"),
            "database":  config.get("database") or config.get("file"),
            "tables":    schema
        }
    except Exception as e:
        return {"success": False, "message": str(e), "tables": []}


@app.post("/disconnect")
def disconnect_database():
    """
    Clear the active connection and live schema.
    Agents fall back to hardcoded Olist schema_metadata.py.
    """
    from app.core.database import _DEFAULT_CONFIG
    global _active_config
    # Reset database.py active config to None (fallback kicks in)
    import app.core.database as _db_module
    _db_module._active_config = None
    # Clear schema store
    reset_schema()
    return {"success": True, "message": "Disconnected. Using default Olist/.env connection."}


@app.post("/schema/refresh")
def schema_refresh():
    """Re-read schema from active connection without reconnecting."""
    try:
        store = refresh_schema()
        return {"success": True, "table_count": len(store["tables"])}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/schema/table/select")
def schema_table_select(payload: dict):
    """
    Toggle a table on/off for NL2SQL.
    Called by connect.py Step 2 checkboxes.
    payload: { "table": "orders", "selected": true }
    """
    set_table_selected(payload["table"], payload["selected"])
    return {"success": True}


@app.post("/schema/table/describe")
def schema_table_describe(payload: dict):
    """
    Save user-written table + column descriptions into schema_store.
    Called by connect.py Step 3 Save buttons.
    payload: { "table": "orders", "description": "...", "columns": {"col": "desc", ...} }
    """
    save_table_metadata(
        table_name = payload["table"],
        table_desc = payload.get("description", ""),
        col_descs  = payload.get("columns", {})
    )
    return {"success": True}


@app.post("/schema/ai/rewrite")
def schema_ai_rewrite(payload: dict):
    """
    Use LLM to write or improve a table or column description.
    Called by connect.py 'Rewrite with AI' buttons.

    Table payload:  { "type": "table",  "table": "orders", "columns": [...], "current_description": "..." }
    Column payload: { "type": "column", "table": "orders", "column": "order_id",
                      "col_type": "varchar(50)", "current_description": "..." }
    """
    import traceback
    try:
        from app.core.llm import get_llm
        llm = get_llm()

        if payload["type"] == "table":
            cols_list = ", ".join(payload.get("columns", []))
            current   = payload.get("current_description", "")
            hint      = f'Existing description: "{current}"\n' if current else ""
            prompt = f"""{hint}Write a clear, concise one-sentence description for a database table.

Table name: {payload['table']}
Columns available: {cols_list}

Rules:
- One sentence only, max 20 words
- Describe what business entity or process this table represents
- Be specific, not generic
- Return ONLY the description text, nothing else"""

        else:  # column
            current = payload.get("current_description", "")
            hint    = f'Existing description: "{current}"\n' if current else ""
            prompt = f"""{hint}Write a clear, concise description for a database column.

Table: {payload['table']}
Column: {payload['column']} ({payload.get('col_type', '')})

Rules:
- One sentence only, max 15 words
- Describe what this column stores and how it is used
- Mention if it is a primary key, foreign key, or metric
- Return ONLY the description text, nothing else"""

        response    = llm.invoke(prompt)
        description = response.content.strip().strip('"').strip("'")
        return {"success": True, "description": description}

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[AI Rewrite ERROR]\n{tb}")   # visible in uvicorn terminal
        return {"success": False, "description": "", "message": f"{type(e).__name__}: {str(e)}"}


@app.get("/schema/saved")
def get_saved_configs():
    """
    List all previously saved schema configs from disk.
    Used by the Connect page to populate the Saved Configurations panel.
    Each entry: { db_type, db_name, table_count, selected_count, has_descriptions, filename }
    """
    try:
        configs = list_saved_configs()
        return {"success": True, "configs": configs}
    except Exception as e:
        return {"success": False, "configs": [], "message": str(e)}


@app.post("/schema/load")
def load_saved_config_endpoint(payload: dict):
    """
    Load a saved schema config from disk into the active schema store.
    Also reconnects the DB using the stored db_type/db_name so agents can query.
    payload: { "filename": "mysql_olist_db.json" }
    """
    filename = payload.get("filename", "")
    if not filename:
        return {"success": False, "message": "filename is required"}
    ok = load_saved_config(filename)
    if ok:
        from app.core.schema_store import get_store
        store = get_store()
        return {
            "success":    True,
            "db_type":    store.get("db_type"),
            "db_name":    store.get("db_name"),
            "table_count": len(store.get("tables", [])),
        }
    return {"success": False, "message": f"Could not load config: {filename}"}


@app.get("/connection/status")
def connection_status():
    """Return active connection info (no password) + schema readiness."""
    config = get_active_config().copy()
    config.pop("password", None)
    return {
        "active":       True,
        "config":       config,
        "schema_ready": is_live_schema_available()
    }


# ── Utilities ──────────────────────────────────────────────────────────────────

def clean_result(result):
    if not result:
        return []
    cleaned = []
    for row in result:
        clean_row = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                clean_row[k] = None
            else:
                clean_row[k] = v
        cleaned.append(clean_row)
    return cleaned


def update_structured_memory(structured: dict, sql: str) -> dict:
    if not sql:
        return structured
    sql_lower = sql.lower()
    new_structured = {}
    if "sum(" in sql_lower:
        new_structured["metric"] = "sum"
    elif "count(" in sql_lower:
        new_structured["metric"] = "count"
    elif "avg(" in sql_lower:
        new_structured["metric"] = "avg"
    else:
        new_structured["metric"] = structured.get("metric")
    if "group by" in sql_lower:
        group_part = sql_lower.split("group by")[1]
        group_part = group_part.split("order by")[0].split("having")[0]
        new_structured["group_by"] = group_part.strip()
    else:
        new_structured["group_by"] = None
    if "where" in sql_lower:
        where_part = sql_lower.split("where")[1]
        where_part = where_part.split("group by")[0].split("order by")[0]
        new_structured["filters"] = where_part.strip()
    else:
        new_structured["filters"] = None
    return new_structured


FOLLOWUP_KEYWORDS = [
    "split by", "group by", "filter by", "break down",
    "by region", "by customer", "by month", "by year",
    "show only", "exclude", "compare", "vs", "now show",
    "also", "and", "what about", "how about"
]

def is_followup_question(question: str) -> bool:
    q = question.lower().strip()
    if len(q.split()) <= 4:
        return True
    return any(kw in q for kw in FOLLOWUP_KEYWORDS)


# ── SSE Streaming ──────────────────────────────────────────────────────────────

@app.get("/query/stream")
def stream_query(question: str, session_id: str):
    def event_stream():
        AGENTS = [
            ("contextualizer", "Contextualizer", "Refining your question with memory..."),
            ("planner",        "Planner",        "Planning the analysis strategy..."),
            ("sql_agent",      "SQL Agent",      "Generating SQL query..."),
            ("analysis",       "Analysis Agent", "Extracting business insights..."),
            ("viz",            "Viz Agent",      "Building visualization..."),
        ]
        for i, (key, name, description) in enumerate(AGENTS):
            yield f"data: {json.dumps({'type':'agent_start','agent':key,'label':name,'description':description,'step':i+1,'total':len(AGENTS)})}\n\n"
            time.sleep(0.15)

        try:
            if session_id not in session_memory_store:
                session_memory_store[session_id] = {"history": [], "structured": {}}
            memory = session_memory_store[session_id]
            if not is_followup_question(question):
                memory["structured"] = {}
            context_block = "".join(
                f"User: {t['question']}\nSQL: {t['sql']}\n\n"
                for t in memory["history"][-3:]
            )
            state = {
                "question": question, "context": context_block,
                "structured_memory": memory["structured"].copy(),
                "plan": "", "sql": "", "result": [],
                "insights": "", "chart_path": "", "chart_type": "",
                "error": "", "retry_count": 0
            }
            output = graph.invoke(state)
            memory["history"].append({"question": question, "sql": output.get("sql", "")})
            memory["structured"] = update_structured_memory(memory["structured"], output.get("sql", ""))
            yield f"data: {json.dumps({'type':'result','plan':output.get('plan',''),'sql':output.get('sql',''),'result':clean_result(output.get('result',[])),'insights':output.get('insights',''),'chart_path':output.get('chart_path',''),'chart_type':output.get('chart_type','')})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"

        yield 'data: {"type":"done"}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ── Standard POST endpoint ─────────────────────────────────────────────────────

@app.post("/query")
def query_agent(payload: dict):
    question   = payload.get("question", "").strip()
    session_id = payload.get("session_id", "default")
    if session_id not in session_memory_store:
        session_memory_store[session_id] = {"history": [], "structured": {}}
    memory = session_memory_store[session_id]
    if not is_followup_question(question):
        memory["structured"] = {}
    context_block = "".join(
        f"User: {t['question']}\nSQL: {t['sql']}\n\n"
        for t in memory["history"][-3:]
    )
    state = {
        "question": question, "context": context_block,
        "structured_memory": memory["structured"].copy(),
        "plan": "", "sql": "", "result": [],
        "insights": "", "chart_path": "", "chart_type": "",
        "error": "", "retry_count": 0
    }
    output = graph.invoke(state)
    memory["history"].append({"question": question, "sql": output.get("sql", "")})
    memory["structured"] = update_structured_memory(memory["structured"], output.get("sql", ""))
    return {
        "plan":       output.get("plan", ""),
        "sql":        output.get("sql", ""),
        "result":     clean_result(output.get("result", [])),
        "insights":   output.get("insights", ""),
        "chart_path": output.get("chart_path", ""),
        "chart_type": output.get("chart_type", "")
    }