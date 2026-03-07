from app.core.llm import get_llm
from app.agents.state import AgentState
from app.agents.sql_agent import clean_sql, get_full_schema_context
from app.core.schema_metadata import JOIN_RELATIONSHIPS
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

def error_fix_node(state: AgentState) -> AgentState:
    """Error fix agent node that attempts to fix broken SQL queries."""
    log_agent_activity(logger, "Error Fix Agent", "Starting", {"retry_count": state.get("retry_count", 0)})
    
    llm = get_llm()
    
    question = state["question"]
    broken_sql = state["sql"]
    error_msg = state["error"]
    retry_count = state.get("retry_count", 0)
    
    logger.warning(f"Fixing SQL error (attempt {retry_count + 1}): {error_msg}")
    logger.debug(f"Broken SQL: {broken_sql}")
    
    try:
        # Get full schema so the fix agent has complete context
        full_schema = get_full_schema_context()
        logger.debug("Retrieved full schema context for error fixing")
        
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
        
        logger.info(f"SQL fix attempt {retry_count + 1} completed")
        logger.debug(f"Fixed SQL: {fixed_sql}")
        
        state["sql"] = fixed_sql
        state["retry_count"] = retry_count + 1
        state["error"] = ""
        
        log_agent_activity(logger, "Error Fix Agent", "Fixed successfully", {"retry_count": retry_count + 1})
        
    except Exception as e:
        logger.error(f"Error fix attempt failed: {str(e)}")
        state["error"] = f"Error fixing failed: {str(e)}"
        
        log_agent_activity(logger, "Error Fix Agent", "Fix failed", {"error": str(e)})

    return state