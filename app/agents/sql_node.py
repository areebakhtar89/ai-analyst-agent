"""SQL execution node for the AI Analyst Agent workflow.

This module bridges the SQL agent and database tools, coordinating
SQL generation and execution within the LangGraph workflow.
"""

from app.agents.state import AgentState
from app.agents.sql_agent import generate_sql
from app.tools.sql_tool import execute_sql


def sql_node(state: AgentState) -> AgentState:
    """Generate and execute SQL query for the user's question.
    
    This node coordinates between the SQL generation logic and database
    execution tools to answer the user's question with actual data.
    
    Args:
        state: Current workflow state containing the user's question
        
    Returns:
        Updated state with SQL query and execution results
    """
    # Generate SQL query from the user's question
    sql = generate_sql(state["question"])
    
    # Execute the SQL query and get results
    result = execute_sql(sql)

    # Store both the SQL and results in the state
    state["sql"] = sql
    state["result"] = result
    return state