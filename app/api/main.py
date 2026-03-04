"""
FastAPI backend for the AI Analyst Agent.
Handles requests and maintains session-based conversational memory.
"""

from fastapi import FastAPI
from app.agents.graph import build_graph
import math

app = FastAPI(
    title="AI Analyst Agent API",
    description="API for multi-agent AI data analysis"
)

graph = build_graph()

# Session memory store
session_memory_store = {}


@app.get("/")
def root():
    return {"message": "AI Analyst API running"}


# -----------------------------
# Utility: Clean JSON results
# -----------------------------
def clean_result(result):
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
def update_structured_memory(structured, sql):

    if not sql:
        return structured

    sql_lower = sql.lower()

    if "sum(" in sql_lower:
        structured["metric"] = "sum"

    if "group by" in sql_lower:
        group_part = sql_lower.split("group by")[1]
        group_part = group_part.split("order by")[0]
        structured["group_by"] = group_part.strip()

    if "where" in sql_lower:
        where_part = sql_lower.split("where")[1]

        if "group by" in where_part:
            where_part = where_part.split("group by")[0]

        structured["filters"] = where_part.strip()

    return structured


# -----------------------------
# Main Query Endpoint
# -----------------------------
@app.post("/query")
def query_agent(payload: dict):

    question = payload.get("question")
    session_id = payload.get("session_id")

    # Initialize memory if new session
    if session_id not in session_memory_store:
        session_memory_store[session_id] = {
            "history": [],
            "structured": {}
        }

    memory = session_memory_store[session_id]

    # Build context block from previous turns
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

    # Update conversational memory
    memory["history"].append({
        "question": question,
        "sql": output.get("sql", "")
    })

    # Update structured memory
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