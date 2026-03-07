"""Analysis agent for extracting business insights."""

import pandas as pd
from app.core.llm import get_llm
from app.agents.state import AgentState

# Max rows to send to LLM — keeps token usage well within free tier limits
MAX_ROWS_FOR_LLM = 15


def summarize_result(result: list) -> str:
    """
    Convert raw query result into a compact, token-efficient summary for the LLM.
    - Shows top N rows
    - Adds basic stats (min, max, mean) for numeric columns
    - Reports total row count so LLM knows the full picture
    """
    if not result:
        return "No data returned."

    df = pd.DataFrame(result)
    total_rows = len(df)

    lines = []
    lines.append(f"Total rows: {total_rows}")
    lines.append(f"Columns: {list(df.columns)}")

    # Basic stats for numeric columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        stats = df[numeric_cols].agg(["min", "max", "mean"]).round(2)
        lines.append("\nNumeric column stats:")
        lines.append(stats.to_string())

    # Top N sample rows
    sample = df.head(MAX_ROWS_FOR_LLM)
    lines.append(f"\nTop {min(MAX_ROWS_FOR_LLM, total_rows)} rows:")
    lines.append(sample.to_string(index=False))

    return "\n".join(lines)


def analysis_node(state: AgentState) -> AgentState:
    """Generate business insights from SQL query results."""

    result = state.get("result", [])
    question = state.get("question", "")

    llm = get_llm()

    # Build a compact summary instead of dumping all rows
    data_summary = summarize_result(result)

    prompt = f"""
You are a business analyst. A user asked: "{question}"

Here is a summary of the query result:

{data_summary}

Write 2-3 concise business insights based on this data.
Be specific — reference actual numbers and column values from the data.
Keep each insight to 1-2 sentences.
"""

    response = llm.invoke(prompt)
    state["insights"] = response.content
    return state