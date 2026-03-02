from app.core.llm import get_llm
from app.agents.state import AgentState
from app.agents.sql_agent import clean_sql


def error_fix_node(state: AgentState) -> AgentState:
    llm = get_llm()

    prompt = f"""
You are a SQL expert.

The following SQL query failed.

Original question:
{state["question"]}

SQL:
{state["sql"]}

Error message:
{state["error"]}

Fix the SQL query.

Rules:
- Return only SQL
- No explanations
- End with semicolon
"""

    response = llm.invoke(prompt)
    fixed_sql = clean_sql(response.content)#response.content.strip()

    state["sql"] = fixed_sql
    state["retry_count"] += 1
    state["error"] = ""

    return state