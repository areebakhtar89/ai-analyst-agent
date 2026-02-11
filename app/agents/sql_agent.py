
### Replace `generate_sql` with this version:
import re
from app.core.llm import get_llm
from app.tools.sql_tool import execute_sql

SCHEMA = """
Table: sales
Columns:
- customer_id (int)
- customer_name (text)
- region (text)
- product (text)
- revenue (int)
- date (date)
"""


def clean_sql(sql: str) -> str:
    # Remove ```sql or ``` wrappers
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = sql.replace("```", "")
    return sql.strip()


def generate_sql(question: str):
    llm = get_llm()

    prompt = f"""
You are a data analyst.

Convert the user question into a SQL query.

Rules:
- Use only the provided table.
- Return only SQL.
- Do not explain anything.
- Do not use markdown or code blocks.

{SCHEMA}

User question:
{question}
"""

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
