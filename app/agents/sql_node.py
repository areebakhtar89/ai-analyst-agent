from app.agents.state import AgentState
from app.agents.sql_agent import generate_sql
from app.tools.sql_tool import execute_sql


def sql_node(state: AgentState) -> AgentState:
    sql = generate_sql(state["question"])
    result = execute_sql(sql)

    state["sql"] = sql
    state["result"] = result
    return state