import re
from app.core.llm import get_llm
from app.tools.sql_tool import execute_sql
from app.core.table_retriever import get_relevant_tables
from app.core.schema_metadata import SCHEMA_METADATA


def clean_sql(text: str) -> str:
    """Extract only the SQL query from LLM output."""
    # Remove markdown code fences
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

    prompt = f"""
You are a senior data analyst.

Convert the user question into a SQL query.

STRICT RULES:
- Return ONLY a SQL query. Nothing else.
- Do NOT include explanations, comments, or notes.
- Do NOT use words like "However", "Explanation", or "Note".
- The output MUST start with SELECT or WITH.
- The output MUST end with a semicolon.
- If the query returns ranked or top results, limit to at most 20 rows using LIMIT 20.

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