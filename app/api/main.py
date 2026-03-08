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
import math
import re
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


# ── Connection endpoints ───────────────────────────────────────────────────────

@app.post("/connect")
def connect_database(payload: dict):
    """
    Test and activate a database connection.

    Payload examples:
      MySQL/PostgreSQL:
        {"type": "mysql", "host": "localhost", "port": 3306,
         "user": "root", "password": "...", "database": "olist_db"}

      SQLite/DuckDB:
        {"type": "sqlite", "file": "path/to/db.sqlite"}
    """
    success, message = test_connection(payload)
    if success:
        set_active_connection(payload)
        return {"success": True, "message": message}
    else:
        return {"success": False, "message": message}


@app.get("/schema")
def fetch_schema():
    """
    Return the schema (tables, columns, row counts) of the active connection.
    Used by the Connect page to display what's in the DB after connecting.
    """
    try:
        config = get_active_config()
        schema = get_schema(config)
        return {
            "success": True,
            "connection_type": config.get("type"),
            "database": config.get("database") or config.get("file"),
            "tables": schema
        }
    except Exception as e:
        return {"success": False, "message": str(e), "tables": []}


@app.get("/connection/status")
def connection_status():
    """Return the currently active connection info (without password)."""
    config = get_active_config().copy()
    config.pop("password", None)
    return {"active": True, "config": config}


# ── Utilities ─────────────────────────────────────────────────────────────────

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


# ── SSE Streaming endpoint ─────────────────────────────────────────────────────

@app.get("/query/stream")
def stream_query(question: str, session_id: str):
    """SSE endpoint — streams agent progress then final result."""
    def event_stream():
        AGENTS = [
            ("contextualizer", "Contextualizer", "Refining your question with memory..."),
            ("planner",        "Planner",        "Planning the analysis strategy..."),
            ("sql_agent",      "SQL Agent",      "Generating SQL query..."),
            ("analysis",       "Analysis Agent", "Extracting business insights..."),
            ("viz",            "Viz Agent",      "Building visualization..."),
        ]

        for i, (key, name, description) in enumerate(AGENTS):
            event = json.dumps({
                "type": "agent_start",
                "agent": key,
                "label": name,
                "description": description,
                "step": i + 1,
                "total": len(AGENTS)
            })
            yield f"data: {event}\n\n"
            time.sleep(0.15)

        try:
            if session_id not in session_memory_store:
                session_memory_store[session_id] = {"history": [], "structured": {}}

            memory = session_memory_store[session_id]

            if not is_followup_question(question):
                memory["structured"] = {}

            context_block = ""
            for turn in memory["history"][-3:]:
                context_block += f"User: {turn['question']}\nSQL: {turn['sql']}\n\n"

            state = {
                "question": question,
                "context": context_block,
                "structured_memory": memory["structured"].copy(),
                "plan": "",
                "sql": "",
                "result": [],
                "insights": "",
                "chart_path": "",
                "chart_type": "",
                "error": "",
                "retry_count": 0
            }

            output = graph.invoke(state)

            memory["history"].append({
                "question": question,
                "sql": output.get("sql", "")
            })
            memory["structured"] = update_structured_memory(
                memory["structured"], output.get("sql", "")
            )

            cleaned_result = clean_result(output.get("result", []))

            result_event = json.dumps({
                "type": "result",
                "plan": output.get("plan", ""),
                "sql": output.get("sql", ""),
                "result": cleaned_result,
                "insights": output.get("insights", ""),
                "chart_path": output.get("chart_path", ""),
                "chart_type": output.get("chart_type", "")
            })
            yield f"data: {result_event}\n\n"

        except Exception as e:
            error_event = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_event}\n\n"

        yield "data: {\"type\": \"done\"}\n\n"

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

    context_block = ""
    for turn in memory["history"][-3:]:
        context_block += f"User: {turn['question']}\nSQL: {turn['sql']}\n\n"

    state = {
        "question": question,
        "context": context_block,
        "structured_memory": memory["structured"].copy(),
        "plan": "", "sql": "", "result": [],
        "insights": "", "chart_path": "", "chart_type": "",
        "error": "", "retry_count": 0
    }

    output = graph.invoke(state)

    memory["history"].append({"question": question, "sql": output.get("sql", "")})
    memory["structured"] = update_structured_memory(
        memory["structured"], output.get("sql", "")
    )

    return {
        "plan":       output.get("plan", ""),
        "sql":        output.get("sql", ""),
        "result":     clean_result(output.get("result", [])),
        "insights":   output.get("insights", ""),
        "chart_path": output.get("chart_path", ""),
        "chart_type": output.get("chart_type", "")
    }
