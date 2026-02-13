from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.planner import planner_node
from app.agents.sql_node import sql_node
from app.agents.analysis import analysis_node
from app.agents.visualization import visualization_node


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("sql", sql_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("viz", visualization_node)

    workflow.set_entry_point("planner")

    workflow.add_edge("planner", "sql")
    workflow.add_edge("sql", "analysis")
    workflow.add_edge("analysis", "viz")
    workflow.add_edge("viz", END)

    return workflow.compile()