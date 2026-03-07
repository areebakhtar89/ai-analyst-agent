from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.planner import planner_node
from app.agents.sql_node import sql_node
from app.agents.analysis import analysis_node
from app.agents.visualization import visualization_node
from app.agents.error_fix_agent import error_fix_node
from app.agents.contextualizer import contextualizer_node
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

MAX_RETRIES = 2


def route_after_sql(state: AgentState):
    """
    Decide next step after SQL execution.
    """
    has_error = bool(state.get("error"))
    retry_count = state.get("retry_count", 0)
    
    logger.debug(f"Routing decision: has_error={has_error}, retry_count={retry_count}, max_retries={MAX_RETRIES}")
    
    if has_error and retry_count < MAX_RETRIES:
        logger.info(f"Routing to error fix (attempt {retry_count + 1})")
        return "error_fix"
    else:
        if has_error:
            logger.warning(f"Max retries ({MAX_RETRIES}) exceeded, proceeding to analysis")
        else:
            logger.info("SQL execution successful, routing to analysis")
        return "analysis"


def build_graph():
    """Build and compile the agent workflow graph."""
    logger.info("Building agent workflow graph")
    
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("sql_agent", sql_node)
    workflow.add_node("error_fix", error_fix_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("viz", visualization_node)
    workflow.add_node("contextualizer", contextualizer_node)
    
    logger.debug("Added all nodes to workflow")

    # Entry point
    workflow.set_entry_point("contextualizer")
    workflow.add_edge("contextualizer","planner")
    
    logger.debug("Set entry point and contextualizer -> planner edge")

    # Main flow
    workflow.add_edge("planner", "sql_agent")
    
    logger.debug("Added planner -> sql_agent edge")

    # Conditional routing after SQL
    workflow.add_conditional_edges(
        "sql_agent",
        route_after_sql,
        {
            "error_fix": "error_fix",
            "analysis": "analysis",
        },
    )
    
    logger.debug("Added conditional routing from sql_agent")

    # Retry loop
    workflow.add_edge("error_fix", "sql_agent")
    
    logger.debug("Added error_fix -> sql_agent retry loop")

    # Normal flow
    workflow.add_edge("analysis", "viz")
    workflow.add_edge("viz", END)
    
    logger.debug("Added analysis -> viz -> END flow")
    
    compiled_graph = workflow.compile()
    logger.info("Agent workflow graph compiled successfully")
    
    return compiled_graph