"""SQL execution node for the AI Analyst Agent workflow."""

from app.agents.state import AgentState
from app.agents.sql_agent import generate_sql
from app.tools.sql_tool import execute_sql
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

def sql_node(state: AgentState) -> AgentState:
    """Generate and execute SQL query for the user's question."""
    log_agent_activity(logger, "SQL Node", "Starting", {"question": state.get("question", "")})
    
    question = state["question"]
    logger.info(f"SQL node processing question: '{question[:50]}...' if len(question) > 50 else question")
    
    try:
        # Generate SQL from question
        sql = generate_sql(question)
        
        # Always store the SQL — error_fix_node needs it even on failure
        state["sql"] = sql
        
        logger.debug(f"Generated SQL for execution: {sql}")
        
        # Execute the query
        result = execute_sql(sql)
        
        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"]
            logger.error(f"SQL execution failed: {error_msg}")
            state["error"] = error_msg
            state["result"] = []
            
            log_agent_activity(logger, "SQL Node", "Execution error", {"error": error_msg})
        else:
            row_count = len(result) if result else 0
            logger.info(f"SQL execution successful: {row_count} rows returned")
            state["error"] = ""
            state["result"] = result
            
            log_agent_activity(logger, "SQL Node", "Success", {"row_count": row_count})
            
    except Exception as e:
        logger.error(f"SQL node failed unexpectedly: {str(e)}")
        state["error"] = str(e)
        state["result"] = []
        
        log_agent_activity(logger, "SQL Node", "Unexpected error", {"error": str(e)})

    return state