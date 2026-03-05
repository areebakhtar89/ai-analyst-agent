"""SQL execution node for the AI Analyst Agent workflow."""

from app.agents.state import AgentState
from app.agents.sql_agent import generate_sql
from app.tools.sql_tool import execute_sql


def sql_node(state: AgentState) -> AgentState:
    """Generate and execute SQL query for the user's question."""

    # Generate SQL from question
    sql = generate_sql(state["question"])

    # Always store the SQL — error_fix_node needs it even on failure
    state["sql"] = sql

    # Execute the query
    result = execute_sql(sql)

    if isinstance(result, dict) and "error" in result:
        state["error"] = result["error"]
        state["result"] = []
    else:
        state["error"] = ""
        state["result"] = result

    return state