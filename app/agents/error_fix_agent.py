from app.core.llm import get_llm
from app.agents.state import AgentState
from app.agents.sql_agent import clean_sql, get_full_schema_context
from app.core.schema_metadata import JOIN_RELATIONSHIPS


def error_fix_node(state: AgentState) -> AgentState:
    llm = get_llm()

    # Get full schema so the fix agent has complete context
    full_schema = get_full_schema_context()

    prompt = """You are a SQL expert fixing a broken DuckDB query.

""" + JOIN_RELATIONSHIPS + """

Full schema:
""" + full_schema + """

Original question:
""" + state["question"] + """

Broken SQL:
""" + state["sql"] + """

Error message:
""" + state["error"] + """

Instructions:
- Read the error carefully and fix the exact problem.
- If the error says a column is not found in a table, you must JOIN the correct table to access it.
- Return ONLY the fixed SQL query.
- No explanations. Must end with semicolon.
"""

    response = llm.invoke(prompt)
    fixed_sql = clean_sql(response.content)

    state["sql"] = fixed_sql
    state["retry_count"] = state.get("retry_count", 0) + 1
    state["error"] = ""

    return state