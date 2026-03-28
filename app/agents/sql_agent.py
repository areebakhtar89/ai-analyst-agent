import re
from app.core.llm import get_llm
from app.tools.sql_tool import execute_sql
from app.core.table_retriever import get_relevant_tables
from app.core.schema_metadata import SCHEMA_METADATA, JOIN_RELATIONSHIPS
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

# Olist-specific forbidden columns — only injected when using fallback schema
FORBIDDEN_COLUMNS = """
COLUMNS THAT DO NOT EXIST — NEVER USE THESE:
- product_name / p.product_name         → does not exist. Use product_category_name instead.
- customer_zip_code                      → does not exist. Use customer_zip_code_prefix.
- seller_zip_code                        → does not exist. Use seller_zip_code_prefix.
- geolocation_zip_code                   → does not exist. Use geolocation_zip_code_prefix.
- product_description_length             → does not exist. Use product_description_lenght (typo is intentional).
- product_name_length                    → does not exist. Use product_name_lenght (typo is intentional).
"""


def clean_sql(text: str) -> str:
    """Extract only the SQL query from LLM output."""
    text = re.sub(r"```sql", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    parts = text.split(";")
    if len(parts) > 1:
        text = parts[0] + ";"
    text = re.sub(r"(?i)\bhowever\b.*", "", text)
    text = re.sub(r"(?i)\bnote\s*:.*", "", text)
    text = re.sub(r"(?i)\bexplanation\s*:.*", "", text)
    return text.strip()


# ── Hardcoded Olist schema helpers (fallback) ─────────────────────────────────

def build_schema_context(tables):
    """Build schema context from hardcoded schema_metadata.py (Olist fallback)."""
    context = ""
    for table in SCHEMA_METADATA:
        if table["table"] in tables:
            context += f"\nTable: {table['table']}\n"
            context += f"Description: {table['description']}\n"
            context += "Columns:\n"
            for col, desc in table["columns"].items():
                context += f"  - {col}: {desc}\n"
            if table.get("joins"):
                context += "JOIN hints:\n"
                for join in table["joins"]:
                    context += f"  - {join}\n"
    return context


def get_full_schema_context():
    """
    Full schema context for all tables.
    Called by error_fix_agent — uses live schema if available, else Olist fallback.
    """
    from app.core.schema_store import is_live_schema_available, get_full_schema_context_live
    if is_live_schema_available():
        logger.debug("[sql_agent] get_full_schema_context → LIVE schema")
        return get_full_schema_context_live()
    logger.debug("[sql_agent] get_full_schema_context → FALLBACK Olist schema")
    return build_schema_context([t["table"] for t in SCHEMA_METADATA])


# ── Schema + syntax selection ─────────────────────────────────────────────────

def _resolve_schema(question: str) -> tuple[str, str, str, bool]:
    """
    Decide which schema and syntax rules to use.

    Returns:
        schema_context : str   — table/column block for LLM prompt
        join_hints     : str   — JOIN relationship hints (Olist only)
        forbidden      : str   — forbidden columns block (Olist only)
        is_live        : bool  — True if using live DB schema
    """
    from app.core.schema_store import (
        is_live_schema_available,
        get_relevant_tables_live,
        get_schema_context,
        get_db_type,
    )

    if is_live_schema_available():
        relevant       = get_relevant_tables_live(question)
        schema_context = get_schema_context(relevant)
        db_type        = get_db_type() or "mysql"
        logger.info(f"[sql_agent] LIVE schema ({db_type.upper()}) — tables: {relevant}")
        # No hardcoded JOIN hints or forbidden columns for unknown DBs
        return schema_context, "", "", True

    else:
        relevant       = get_relevant_tables(question)   # sentence-transformer based
        schema_context = build_schema_context(relevant)
        logger.info(f"[sql_agent] FALLBACK Olist schema — tables: {relevant}")
        return schema_context, JOIN_RELATIONSHIPS, FORBIDDEN_COLUMNS, False


def _syntax_rules(db_type: str) -> str:
    """DB-specific syntax block injected into the LLM prompt."""
    if db_type == "postgresql":
        return """DB SYNTAX (PostgreSQL):
- Date format: TO_CHAR(col, 'YYYY-MM') monthly, TO_CHAR(col, 'YYYY') yearly
- String concat: || or CONCAT()
- Case-insensitive match: ILIKE"""
    elif db_type == "sqlite":
        return """DB SYNTAX (SQLite):
- Date format: STRFTIME('%Y-%m', col) monthly, STRFTIME('%Y', col) yearly
- String concat: || operator
- No FULL OUTER JOIN — use LEFT JOIN + UNION"""
    elif db_type == "duckdb":
        return """DB SYNTAX (DuckDB):
- Date format: STRFTIME(col, '%Y-%m') monthly
- String concat: || or CONCAT()"""
    else:  # mysql default
        return """DB SYNTAX (MySQL):
- Date format: DATE_FORMAT(col, '%Y-%m') monthly, DATE_FORMAT(col, '%Y') yearly
- String concat: CONCAT() — do NOT use ||
- Do NOT use STRFTIME() — that is DuckDB/SQLite syntax"""


# ── SQL generation ────────────────────────────────────────────────────────────

def generate_sql(question: str) -> str:
    logger.info(f"Generating SQL for: '{question[:60]}'")
    try:
        llm = get_llm()

        schema_context, join_hints, forbidden, is_live = _resolve_schema(question)

        # Determine DB type for syntax rules
        if is_live:
            from app.core.schema_store import get_db_type
            db_type = get_db_type() or "mysql"
        else:
            db_type = "mysql"

        syntax = _syntax_rules(db_type)

        prompt = f"""You are a senior data analyst expert in {db_type.upper()} SQL.

Convert the user question into a correct {db_type.upper()} query.

STRICT OUTPUT RULES:
- Return ONLY the SQL query. Nothing else.
- No explanations, comments, or markdown.
- Must start with SELECT or WITH.
- Must end with a semicolon.

{forbidden}

{join_hints}

{syntax}

QUERY LOGIC RULES:
1. TOP N OVERALL: Use ORDER BY + LIMIT N.
2. TOP N PER GROUP: Use CTE with ROW_NUMBER() OVER (PARTITION BY <group> ORDER BY <metric> DESC).
3. TRENDS OVER TIME: Group by date function. Do NOT add LIMIT.
4. FULL BREAKDOWN (by state/category etc): Return all groups. Do NOT add LIMIT.
5. PRODUCT QUESTIONS (Olist): No product_name column exists. Always group by product_category_name. Always JOIN product_category_translation for English names.

Available tables and columns:
{schema_context}

User question:
{question}"""

        response = llm.invoke(prompt)
        sql = clean_sql(response.content)

        # Cap non-aggregated queries at 100 rows for UI performance
        sql_upper = sql.upper()
        if "LIMIT" not in sql_upper and "GROUP BY" not in sql_upper:
            sql = sql.rstrip(";").rstrip() + " LIMIT 100;"
            logger.info("[sql_agent] Capped non-aggregated query at 100 rows")

        logger.info(f"[sql_agent] SQL generated ({len(sql)} chars)")
        logger.debug(f"[sql_agent] SQL: {sql}")
        return sql

    except Exception as e:
        logger.error(f"[sql_agent] SQL generation failed: {e}")
        return f"-- Error generating SQL: {str(e)}"


def run_agent(question: str):
    log_agent_activity(logger, "SQL Agent", "Starting", {"question": question})
    try:
        sql = generate_sql(question)
        if sql.startswith("-- Error"):
            log_agent_activity(logger, "SQL Agent", "SQL generation failed")
            return {"question": question, "sql": sql, "result": []}
        result = execute_sql(sql)
        logger.info(f"[sql_agent] Executed: {len(result) if result else 0} rows")
        log_agent_activity(logger, "SQL Agent", "Success", {"result_rows": len(result) if result else 0})
        return {"question": question, "sql": sql, "result": result}
    except Exception as e:
        logger.error(f"[sql_agent] Failed: {e}")
        log_agent_activity(logger, "SQL Agent", "Error", {"error": str(e)})
        return {"question": question, "sql": f"-- Error: {str(e)}", "result": []}