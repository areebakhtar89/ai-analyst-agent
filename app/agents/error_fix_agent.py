from app.core.llm import get_llm
from app.agents.state import AgentState
from app.agents.sql_agent import clean_sql, get_full_schema_context, FORBIDDEN_COLUMNS
from app.core.schema_metadata import JOIN_RELATIONSHIPS
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)


def error_fix_node(state: AgentState) -> AgentState:
    """
    Fixes broken SQL using live schema if available, Olist fallback otherwise.

    Changes from original:
    - Checks is_live_schema_available() to decide schema source
    - Skips FORBIDDEN_COLUMNS and JOIN_RELATIONSHIPS when on live DB
      (those are Olist-specific and wrong for other databases)
    - Injects correct DB type into prompt so syntax fixes are accurate
    """
    log_agent_activity(logger, "Error Fix Agent", "Starting", {"retry_count": state.get("retry_count", 0)})

    llm         = get_llm()
    retry_count = state.get("retry_count", 0)

    logger.warning(f"[ErrorFix] Attempt {retry_count + 1}: {state['error']}")
    logger.debug(f"[ErrorFix] Broken SQL: {state['sql']}")

    try:
        from app.core.schema_store import is_live_schema_available, get_db_type

        is_live = is_live_schema_available()
        db_type = (get_db_type() or "mysql") if is_live else "mysql"

        # get_full_schema_context() already handles live vs fallback internally
        full_schema = get_full_schema_context()

        # Only inject Olist-specific blocks when on fallback schema
        forbidden_block = "" if is_live else FORBIDDEN_COLUMNS
        join_block      = "" if is_live else JOIN_RELATIONSHIPS

        schema_source = "LIVE DB" if is_live else "HARDCODED OLIST"
        logger.info(f"[ErrorFix] Using {schema_source} schema — DB: {db_type.upper()}")

        prompt = f"""You are a {db_type.upper()} SQL expert fixing a broken query.

{forbidden_block}

{join_block}

Full schema ({schema_source} — use ONLY these tables and columns):
{full_schema}

Original question:
{state["question"]}

Broken SQL:
{state["sql"]}

Error message:
{state["error"]}

HOW TO FIX:
- "Unknown column 'X'"    → X does not exist. Find the correct column in the schema above.
- "Table X doesn't exist" → Check exact table names in schema above.
- "Ambiguous column"      → Prefix column with its table alias.
- Syntax error            → Fix {db_type.upper()}-specific syntax.

IMPORTANT: Only use tables and columns listed in the schema above.
Return ONLY the fixed SQL query. No explanations. Must end with semicolon.
"""

        response  = llm.invoke(prompt)
        fixed_sql = clean_sql(response.content)

        logger.info(f"[ErrorFix] Fix attempt {retry_count + 1} completed")
        logger.debug(f"[ErrorFix] Fixed SQL: {fixed_sql}")

        state["sql"]         = fixed_sql
        state["retry_count"] = retry_count + 1
        state["error"]       = ""

        log_agent_activity(logger, "Error Fix Agent", "Fixed successfully", {"retry_count": retry_count + 1})

    except Exception as e:
        logger.error(f"[ErrorFix] Failed: {e}")
        state["error"] = f"Error fixing failed: {str(e)}"
        log_agent_activity(logger, "Error Fix Agent", "Fix failed", {"error": str(e)})

    return state