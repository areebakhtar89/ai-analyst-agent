import re
from app.core.llm import get_llm
from app.tools.sql_tool import execute_sql
from app.core.table_retriever import get_relevant_tables
from app.core.schema_metadata import SCHEMA_METADATA, JOIN_RELATIONSHIPS


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
    llm = get_llm()

    relevant_tables = get_relevant_tables(question)
    schema_context = build_schema_context(relevant_tables)

    prompt = """You are a senior data analyst expert in SQL.

Convert the user question into a correct SQL query for DuckDB.

STRICT OUTPUT RULES:
- Return ONLY the SQL query. Nothing else.
- No explanations, comments, or markdown.
- Must start with SELECT or WITH.
- Must end with a semicolon.

""" + JOIN_RELATIONSHIPS + """

QUERY LOGIC RULES:

1. TOP N OVERALL (e.g. "top 5 customers by revenue"):
   Use ORDER BY + LIMIT N.
   Example:
   SELECT c.customer_name, SUM(o.total_amount) AS total_revenue
   FROM orders o
   JOIN customers c ON o.customer_id = c.customer_id
   GROUP BY c.customer_name
   ORDER BY total_revenue DESC LIMIT 10;

2. TOP N PER GROUP (e.g. "top 5 customers per region"):
   ALWAYS use a CTE with ROW_NUMBER() OVER (PARTITION BY <group> ORDER BY <metric> DESC).
   Example:
   WITH ranked AS (
     SELECT c.customer_name, c.region, SUM(o.total_amount) AS total_revenue,
            ROW_NUMBER() OVER (PARTITION BY c.region ORDER BY SUM(o.total_amount) DESC) AS rn
     FROM orders o
     JOIN customers c ON o.customer_id = c.customer_id
     GROUP BY c.region, c.customer_name
   )
   SELECT customer_name, region, total_revenue FROM ranked WHERE rn <= 5
   ORDER BY region, total_revenue DESC;

3. TRENDS OVER TIME (e.g. "monthly revenue", "monthly order count"):
   Group by time. Do NOT add LIMIT.
   Use STRFTIME(order_date, '%Y-%m') for monthly grouping in DuckDB.
   Example:
   SELECT STRFTIME(order_date, '%Y-%m') AS month, COUNT(*) AS order_count
   FROM orders GROUP BY month ORDER BY month;

4. FULL BREAKDOWN (e.g. "revenue by region", "sales by category"):
   Return all groups. Do NOT add LIMIT.

5. YEAR OVER YEAR:
   SELECT STRFTIME(order_date, '%Y') AS year, SUM(total_amount) AS total_revenue
   FROM orders GROUP BY year ORDER BY year;

Available tables and columns:
""" + schema_context + """

User question:
""" + question

    response = llm.invoke(prompt)
    sql = clean_sql(response.content)
    return sql


def run_agent(question: str):
    sql = generate_sql(question)
    result = execute_sql(sql)
    return {
        "question": question,
        "sql": sql,
        "result": result
    }