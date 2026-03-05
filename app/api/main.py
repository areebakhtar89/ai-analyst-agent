"""
FastAPI backend for the AI Analyst Agent.
Handles requests and maintains session-based conversational memory.
"""

from fastapi import FastAPI
from app.agents.graph import build_graph
import math
import re

app = FastAPI(
    title="AI Analyst Agent API",
    description="API for multi-agent AI data analysis"
)

graph = build_graph()

# In-memory session store (replace with Redis in next upgrade)
session_memory_store = {}


@app.get("/")
def root():
    return {"message": "AI Analyst API running"}


# -----------------------------
# Utility: Clean JSON results
# -----------------------------

def clean_result(result):
    """Replace NaN/Inf float values with None for JSON serialization."""
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


# -----------------------------
# Utility: Update structured memory
# -----------------------------

def update_structured_memory(structured: dict, sql: str) -> dict:
    """Extract metric, filters, group_by from generated SQL."""
    if not sql:
        return structured

    sql_lower = sql.lower()
    new_structured = {}

    # Metric
    if "sum(" in sql_lower:
        new_structured["metric"] = "sum"
    elif "count(" in sql_lower:
        new_structured["metric"] = "count"
    elif "avg(" in sql_lower:
        new_structured["metric"] = "avg"
    else:
        new_structured["metric"] = structured.get("metric")

    # Group by
    if "group by" in sql_lower:
        group_part = sql_lower.split("group by")[1]
        group_part = group_part.split("order by")[0].split("having")[0]
        new_structured["group_by"] = group_part.strip()
    else:
        new_structured["group_by"] = None

    # Filters (WHERE clause)
    if "where" in sql_lower:
        where_part = sql_lower.split("where")[1]
        where_part = where_part.split("group by")[0].split("order by")[0]
        new_structured["filters"] = where_part.strip()
    else:
        new_structured["filters"] = None

    return new_structured


# -----------------------------
# Utility: Detect follow-up
# -----------------------------

FOLLOWUP_KEYWORDS = [
    "split by", "group by", "filter by", "break down",
    "by region", "by customer", "by month", "by year",
    "show only", "exclude", "compare", "vs", "now show",
    "also", "and", "what about", "how about"
]

def is_followup_question(question: str) -> bool:
    """Heuristic: short or keyword-based follow-up detection."""
    q = question.lower().strip()
    if len(q.split()) <= 4:
        return True
    return any(kw in q for kw in FOLLOWUP_KEYWORDS)


# -----------------------------
# Main Query Endpoint
# -----------------------------

@app.post("/query")
def query_agent(payload: dict):
    question = payload.get("question", "").strip()
    session_id = payload.get("session_id", "default")

    # Initialize memory for new sessions
    if session_id not in session_memory_store:
        session_memory_store[session_id] = {
            "history": [],
            "structured": {}
        }

    memory = session_memory_store[session_id]

    # If NOT a follow-up, reset structured memory to avoid context bleed
    if not is_followup_question(question):
        memory["structured"] = {}

    # Build context from last 3 turns
    context_block = ""
    for turn in memory["history"][-3:]:
        context_block += f"User: {turn['question']}\nSQL: {turn['sql']}\n\n"

    # Initialize LangGraph state
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

    # Run agent workflow
    output = graph.invoke(state)

    # Update memory
    memory["history"].append({
        "question": question,
        "sql": output.get("sql", "")
    })
    memory["structured"] = update_structured_memory(
        memory["structured"],
        output.get("sql", "")
    )

    cleaned_result = clean_result(output.get("result", []))

    return {
        "plan": output.get("plan", ""),
        "sql": output.get("sql", ""),
        "result": cleaned_result,
        "insights": output.get("insights", ""),
        "chart_path": output.get("chart_path", ""),
        "chart_type": output.get("chart_type", "")
    }