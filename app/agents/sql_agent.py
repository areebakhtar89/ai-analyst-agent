
### Replace `generate_sql` with this version:
import re
from app.core.llm import get_llm
from app.tools.sql_tool import execute_sql
from app.core.table_retriever import get_relevant_tables
from app.core.schema_metadata import SCHEMA_METADATA

import re

def clean_sql(text: str) -> str:
    """
    Extract only the SQL query from LLM output.
    """
    # Remove markdown
    text = text.replace("```sql", "").replace("```", "")

    # Remove everything after first semicolon
    parts = text.split(";")
    if len(parts) > 1:
        text = parts[0] + ";"

    # Remove common explanation phrases
    text = re.sub(r"(?i)however.*", "", text)
    text = re.sub(r"(?i)note:.*", "", text)
    text = re.sub(r"(?i)explanation:.*", "", text)

    return text.strip()

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

        STRICT RULES:
        - Return ONLY a SQL query.
        - Do NOT include explanations.
        - Do NOT include comments.
        - Do NOT include words like "However", "Explanation", or "Note".
        - The output must start with SELECT or WITH.
        - The output must end with a semicolon.

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
