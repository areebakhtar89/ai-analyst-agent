from app.core.database import run_query


def execute_sql(sql: str):
    try:
        result = run_query(sql)
        return result.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}