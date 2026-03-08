import re
from app.core.llm import get_llm
from app.tools.sql_tool import execute_sql
from app.core.table_retriever import get_relevant_tables
from app.core.schema_metadata import SCHEMA_METADATA, JOIN_RELATIONSHIPS
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

# Columns that do NOT exist in the database.
# LLM must never generate these — they cause immediate SQL errors.
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


def build_schema_context(tables):
    """Build schema context including column descriptions and JOIN hints."""
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
    """Return full schema context for all tables (used by error fix agent)."""
    all_tables = [t["table"] for t in SCHEMA_METADATA]
    return build_schema_context(all_tables)


def generate_sql(question: str) -> str:
    """Generate SQL query from natural language question."""
    logger.info(f"Generating SQL for question: '{question[:50]}...' if len(question) > 50 else question")

    try:
        llm = get_llm()
        relevant_tables = get_relevant_tables(question)
        schema_context  = build_schema_context(relevant_tables)

        prompt = """You are a senior data analyst expert in MySQL SQL.

Convert the user question into a correct MySQL query.

STRICT OUTPUT RULES:
- Return ONLY the SQL query. Nothing else.
- No explanations, comments, or markdown.
- Must start with SELECT or WITH.
- Must end with a semicolon.

""" + FORBIDDEN_COLUMNS + """

""" + JOIN_RELATIONSHIPS + """

MYSQL SYNTAX RULES:
- For monthly grouping use:  DATE_FORMAT(order_purchase_timestamp, '%Y-%m')
- For yearly grouping use:   DATE_FORMAT(order_purchase_timestamp, '%Y')
- For date truncation use:   DATE(column_name)
- Do NOT use STRFTIME() — that is DuckDB syntax, not MySQL.
- Do NOT use || for string concat — use CONCAT() instead.

QUERY LOGIC RULES:

1. TOP N OVERALL (e.g. "top 5 categories by revenue"):
   Use ORDER BY + LIMIT N.
   Example:
   SELECT t.product_category_name_english, SUM(op.payment_value) AS total_revenue
   FROM order_items oi
   JOIN products p ON oi.product_id = p.product_id
   JOIN product_category_translation t ON p.product_category_name = t.product_category_name
   JOIN order_payments op ON oi.order_id = op.order_id
   GROUP BY t.product_category_name_english
   ORDER BY total_revenue DESC LIMIT 10;

2. TOP N PER GROUP (e.g. "top 5 categories per state"):
   Use a CTE with ROW_NUMBER() OVER (PARTITION BY <group> ORDER BY <metric> DESC).
   Example:
   WITH ranked AS (
     SELECT c.customer_state, t.product_category_name_english,
            SUM(op.payment_value) AS revenue,
            ROW_NUMBER() OVER (PARTITION BY c.customer_state ORDER BY SUM(op.payment_value) DESC) AS rn
     FROM orders o
     JOIN customers c ON o.customer_id = c.customer_id
     JOIN order_items oi ON o.order_id = oi.order_id
     JOIN products p ON oi.product_id = p.product_id
     JOIN product_category_translation t ON p.product_category_name = t.product_category_name
     JOIN order_payments op ON o.order_id = op.order_id
     GROUP BY c.customer_state, t.product_category_name_english
   )
   SELECT customer_state, product_category_name_english, revenue
   FROM ranked WHERE rn <= 5
   ORDER BY customer_state, revenue DESC;

3. TRENDS OVER TIME (e.g. "monthly revenue", "monthly order count"):
   Group by time using DATE_FORMAT. Do NOT add LIMIT.
   Example:
   SELECT DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS month,
          COUNT(*) AS order_count
   FROM orders
   GROUP BY month
   ORDER BY month;

4. FULL BREAKDOWN (e.g. "revenue by state", "sales by category"):
   Return all groups. Do NOT add LIMIT.

5. PRODUCT QUESTIONS:
   There is NO product_name column. Always group by product_category_name.
   Always JOIN product_category_translation to show English names.

Available tables and columns:
""" + schema_context + """

User question:
""" + question

        response = llm.invoke(prompt)
        sql = clean_sql(response.content)

        # Cap rows sent to UI — keeps API fast and UI clean.
        # Aggregated queries (GROUP BY) already return small result sets — no cap needed.
        sql_upper = sql.upper()
        has_limit = "LIMIT" in sql_upper
        is_aggregated = "GROUP BY" in sql_upper
        if not has_limit and not is_aggregated:
            sql = sql.rstrip(";").rstrip() + " LIMIT 100;"
            logger.info("No LIMIT on non-aggregated query — capped at 100 rows for UI")

        logger.info(f"SQL generated successfully: {len(sql)} characters")
        logger.debug(f"Generated SQL: {sql}")
        return sql

    except Exception as e:
        logger.error(f"SQL generation failed: {str(e)}")
        return f"-- Error generating SQL: {str(e)}"


def run_agent(question: str):
    """Main SQL agent function that generates and executes SQL."""
    log_agent_activity(logger, "SQL Agent", "Starting", {"question": question})

    try:
        sql = generate_sql(question)

        if sql.startswith("-- Error"):
            logger.error("SQL generation failed, skipping execution")
            log_agent_activity(logger, "SQL Agent", "SQL generation failed")
            return {"question": question, "sql": sql, "result": []}

        result = execute_sql(sql)

        logger.info(f"SQL executed successfully: {len(result) if result else 0} rows returned")
        log_agent_activity(logger, "SQL Agent", "Success", {"result_rows": len(result) if result else 0})
        return {"question": question, "sql": sql, "result": result}

    except Exception as e:
        logger.error(f"SQL agent failed: {str(e)}")
        log_agent_activity(logger, "SQL Agent", "Error", {"error": str(e)})
        return {"question": question, "sql": f"-- Error: {str(e)}", "result": []}