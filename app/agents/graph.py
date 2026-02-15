from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.planner import planner_node
from app.agents.sql_node import sql_node
from app.agents.analysis import analysis_node
from app.agents.visualization import visualization_node
from app.agents.error_fix_agent import error_fix_node


MAX_RETRIES = 2


def route_after_sql(state: AgentState):
    """
    Decide next step after SQL execution.
    """
    if state.get("error") and state.get("retry_count", 0) < MAX_RETRIES:
        return "error_fix"
    else:
        return "analysis"


def build_graph():
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("sql_agent", sql_node)
    workflow.add_node("error_fix", error_fix_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("viz", visualization_node)

    # Entry point
    workflow.set_entry_point("planner")

    # Main flow
    workflow.add_edge("planner", "sql_agent")

    # Conditional routing after SQL
    workflow.add_conditional_edges(
        "sql_agent",
        route_after_sql,
        {
            "error_fix": "error_fix",
            "analysis": "analysis",
        },
    )

    # Retry loop
    workflow.add_edge("error_fix", "sql_agent")

    # Normal flow
    workflow.add_edge("analysis", "viz")
    workflow.add_edge("viz", END)

    return workflow.compile()
