from app.core.llm import get_llm
from app.agents.state import AgentState
from app.agents.sql_agent import clean_sql, get_full_schema_context, FORBIDDEN_COLUMNS
from app.core.schema_metadata import JOIN_RELATIONSHIPS
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

def error_fix_node(state: AgentState) -> AgentState:
    """Error fix agent node that attempts to fix broken SQL queries."""
    log_agent_activity(logger, "Error Fix Agent", "Starting", {"retry_count": state.get("retry_count", 0)})

    llm         = get_llm()
    retry_count = state.get("retry_count", 0)

    logger.warning(f"Fixing SQL error (attempt {retry_count + 1}): {state['error']}")
    logger.debug(f"Broken SQL: {state['sql']}")

    try:
        full_schema = get_full_schema_context()

        prompt = """You are a MySQL SQL expert fixing a broken query.

""" + FORBIDDEN_COLUMNS + """

""" + JOIN_RELATIONSHIPS + """

MYSQL SYNTAX RULES:
- Use DATE_FORMAT(col, '%Y-%m') for monthly grouping — NOT STRFTIME.
- Use CONCAT() for string concatenation — NOT ||.
- Column names are case-sensitive — use exact names from the schema below.

Full schema (all tables and columns):
""" + full_schema + """

Original question:
""" + state["question"] + """

Broken SQL:
""" + state["sql"] + """

Error message:
""" + state["error"] + """

HOW TO FIX:
- "Unknown column 'X'" → X does not exist. Check the schema above for the correct column name.
  Common mistakes:
    product_name       → use product_category_name (join product_category_translation for English)
    customer_zip_code  → use customer_zip_code_prefix
    seller_zip_code    → use seller_zip_code_prefix
- "Table X doesn't exist" → check table names in schema above.
- "Ambiguous column" → prefix with table alias.
- Syntax error → fix MySQL syntax (no STRFTIME, no ||).

Return ONLY the fixed SQL query. No explanations. Must end with semicolon.
"""

        response  = llm.invoke(prompt)
        fixed_sql = clean_sql(response.content)

        logger.info(f"SQL fix attempt {retry_count + 1} completed")
        logger.debug(f"Fixed SQL: {fixed_sql}")

        state["sql"]         = fixed_sql
        state["retry_count"] = retry_count + 1
        state["error"]       = ""

        log_agent_activity(logger, "Error Fix Agent", "Fixed successfully", {"retry_count": retry_count + 1})

    except Exception as e:
        logger.error(f"Error fix attempt failed: {str(e)}")
        state["error"] = f"Error fixing failed: {str(e)}"
        log_agent_activity(logger, "Error Fix Agent", "Fix failed", {"error": str(e)})

    return state