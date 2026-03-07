import re
from app.core.llm import get_llm
from app.tools.sql_tool import execute_sql
from app.core.table_retriever import get_relevant_tables
from app.core.schema_metadata import SCHEMA_METADATA


def clean_sql(text: str) -> str:
    """Extract only the SQL query from LLM output."""
    text = re.sub(r"```sql", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")

    # Remove everything after first semicolon (extra explanations)
    parts = text.split(";")
    if len(parts) > 1:
        text = parts[0] + ";"

    # Remove common explanation phrases LLMs append
    text = re.sub(r"(?i)\bhowever\b.*", "", text)
    text = re.sub(r"(?i)\bnote\s*:.*", "", text)
    text = re.sub(r"(?i)\bexplanation\s*:.*", "", text)

    return text.strip()


def build_schema_context(tables):
    context = ""
    for table in SCHEMA_METADATA:
        if table["table"] in tables:
            context += f"\nTable: {table['table']}\n"
            for col, desc in table["columns"].items():
                context += f"  - {col}: {desc}\n"
    return context


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

QUERY LOGIC RULES:

1. TOP N OVERALL (e.g. "top 5 customers by revenue"):
   Use ORDER BY + LIMIT N.
   Example:
   SELECT customer_name, SUM(total_amount) AS total_revenue
   FROM orders GROUP BY customer_name
   ORDER BY total_revenue DESC LIMIT 5;

2. TOP N PER GROUP (e.g. "top 5 customers per region", "top 3 products per category"):
   ALWAYS use a CTE with ROW_NUMBER() OVER (PARTITION BY <group> ORDER BY <metric> DESC).
   Never use just GROUP BY + LIMIT — that gives wrong results.
   Example:
   WITH ranked AS (
     SELECT customer_name, region, SUM(total_amount) AS total_revenue,
            ROW_NUMBER() OVER (PARTITION BY region ORDER BY SUM(total_amount) DESC) AS rn
     FROM customers JOIN orders ON customers.customer_id = orders.customer_id
     GROUP BY region, customer_name
   )
   SELECT customer_name, region, total_revenue FROM ranked WHERE rn <= 5
   ORDER BY region, total_revenue DESC;

3. TRENDS OVER TIME (e.g. "monthly revenue", "monthly order count"):
   Group by the time dimension. Do NOT add LIMIT.
   Use STRFTIME(order_date, '%Y-%m') for monthly grouping in DuckDB.
   Example:
   SELECT STRFTIME(order_date, '%Y-%m') AS month, COUNT(*) AS order_count
   FROM orders GROUP BY month ORDER BY month;

4. FULL BREAKDOWN / DISTRIBUTION (e.g. "revenue by region", "sales by category"):
   Return all groups. Do NOT add LIMIT.

5. YEAR OVER YEAR (e.g. "year over year revenue"):
   Group by year only.
   Example:
   SELECT STRFTIME(order_date, '%Y') AS year, SUM(total_amount) AS total_revenue
   FROM orders GROUP BY year ORDER BY year;

Available tables:
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