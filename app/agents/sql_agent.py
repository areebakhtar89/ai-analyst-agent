
### Replace `generate_sql` with this version:
import re
from app.core.llm import get_llm
from app.tools.sql_tool import execute_sql
from app.core.table_retriever import get_relevant_tables
from app.core.schema_metadata import SCHEMA_METADATA

def build_schema_context(tables):
    context = ""
    for table in SCHEMA_METADATA:
        if table["table"] in tables:
            context += f"\nTable: {table['table']}\n"
            for col, desc in table["columns"].items():
                context += f"- {col}: {desc}\n"
    return context

def clean_sql(sql: str) -> str:
    # Remove ```sql or ``` wrappers
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = sql.replace("```", "")
    return sql.strip()


def generate_sql(question: str):
    llm = get_llm()

    relevant_tables = get_relevant_tables(question)
    schema_context = build_schema_context(relevant_tables)

    prompt = f"""
    You are a senior data analyst.

    Convert the user question into a SQL query.

    Rules:
    - Use only the provided tables.
    - Use joins where needed.
    - Use EXTRACT(YEAR FROM column) for year calculations.
    - Return only SQL.
    - Do not use markdown.
    
    Available tables:
    {schema_context}

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
