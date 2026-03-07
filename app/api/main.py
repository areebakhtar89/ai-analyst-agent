"""
FastAPI backend for the AI Analyst Agent.
Handles requests and maintains session-based conversational memory.
"""

from fastapi import FastAPI
from app.agents.graph import build_graph
import math
import re
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="AI Analyst Agent API",
    description="API for multi-agent AI data analysis"
)

graph = build_graph()

# In-memory session store (replace with Redis in next upgrade)
session_memory_store = {}

logger.info("AI Analyst Agent API started")


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "AI Analyst API running"}


# -----------------------------
# Utility: Clean JSON results
# -----------------------------

def clean_result(result):
    """Replace NaN/Inf float values with None for JSON serialization."""
    logger.debug(f"Cleaning {len(result) if result else 0} result rows")
    
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
    
    logger.debug(f"Cleaned {len(cleaned)} rows")
    return cleaned


# -----------------------------
# Utility: Update structured memory
# -----------------------------

def update_structured_memory(structured: dict, sql: str) -> dict:
    """Extract metric, filters, group_by from generated SQL."""
    logger.debug(f"Updating structured memory with SQL: {sql[:50] + '...' if len(sql) > 50 else sql}")
    
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

    logger.debug(f"Updated structured memory: {new_structured}")
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
    is_followup = len(q.split()) <= 4 or any(kw in q for kw in FOLLOWUP_KEYWORDS)
    
    logger.debug(f"Follow-up question detection: '{question[:30]}...' -> {is_followup}")
    return is_followup


# -----------------------------
# Main Query Endpoint
# -----------------------------

@app.post("/query")
def query_agent(payload: dict):
    question = payload.get("question", "").strip()
    session_id = payload.get("session_id", "default")
    
    logger.info(f"Received query for session {session_id}: {question[:50] + '...' if len(question) > 50 else question}")
    
    # Initialize memory for new sessions
    if session_id not in session_memory_store:
        logger.info(f"Creating new session: {session_id}")
        session_memory_store[session_id] = {
            "history": [],
            "structured": {}
        }

    memory = session_memory_store[session_id]
    logger.debug(f"Session {session_id} has {len(memory['history'])} previous interactions")

    # If NOT a follow-up, reset structured memory to avoid context bleed
    if not is_followup_question(question):
        logger.debug("Resetting structured memory for new question")
        memory["structured"] = {}

    # Build context from last 3 turns
    context_block = ""
    for turn in memory["history"][-3:]:
        context_block += f"User: {turn['question']}\nSQL: {turn['sql']}\n\n"
    
    logger.debug(f"Built context with {len(memory['history'][-3:])} previous turns")

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
    logger.debug("Running agent workflow")
    output = graph.invoke(state)
    
    logger.info(f"Agent workflow completed - Chart type: {output.get('chart_type', 'none')}, Rows: {len(output.get('result', []))}")

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

    response = {
        "plan": output.get("plan", ""),
        "sql": output.get("sql", ""),
        "result": cleaned_result,
        "insights": output.get("insights", ""),
        "chart_path": output.get("chart_path", ""),
        "chart_type": output.get("chart_type", "")
    }
    
    logger.info(f"Returning response for session {session_id}")
    return response