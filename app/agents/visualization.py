import pandas as pd
import plotly.express as px
import json
from app.agents.state import AgentState
from app.core.llm import get_llm


def detect_chart_type(df):
    """
    Deterministic chart selection logic.
    """
    cols = df.columns
    first_col = cols[0].lower()

    # Time-series detection
    time_keywords = ["date", "time", "month", "year", "day"]
    if any(k in first_col for k in time_keywords):
        return "line", cols[0], cols[1]

    # Numeric vs numeric → scatter
    if pd.api.types.is_numeric_dtype(df[cols[0]]) and pd.api.types.is_numeric_dtype(df[cols[1]]):
        return "scatter", cols[0], cols[1]

    # Default → bar
    return "bar", cols[0], cols[1]


def visualization_node(state: AgentState) -> AgentState:
    result = state.get("result")

    if not result or isinstance(result, dict):
        state["chart_path"] = ""
        state["chart_type"] = "none"
        return state

    try:
        df = pd.DataFrame(result)
    except Exception:
        state["chart_path"] = ""
        state["chart_type"] = "none"
        return state

    if df.empty or df.shape[1] < 2:
        state["chart_path"] = ""
        state["chart_type"] = "none"
        return state

    # Step 1: deterministic logic
    chart_type, x, y = detect_chart_type(df)

    # Step 2: optional LLM override
    try:
        llm = get_llm()

        prompt = f"""
You are a data visualization expert.

Dataset columns:
{list(df.columns)}

Current suggested chart:
{chart_type}

If a better chart exists, return JSON:
{{
  "chart_type": "bar|line|scatter",
  "x": "column",
  "y": "column"
}}

If current chart is fine, return:
{{"chart_type": "{chart_type}", "x": "{x}", "y": "{y}"}}

Return JSON only.
"""

        response = llm.invoke(prompt)

        # Extract JSON safely
        text = response.content.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            chart_config = json.loads(text[start:end])
            chart_type = chart_config.get("chart_type", chart_type)
            x = chart_config.get("x", x)
            y = chart_config.get("y", y)

    except Exception as e:
        print("Visualization LLM failed, using deterministic logic:", e)

    # Step 3: generate chart
    if chart_type == "line":
        fig = px.line(df, x=x, y=y, title="Auto-generated chart")
    elif chart_type == "scatter":
        fig = px.scatter(df, x=x, y=y, title="Auto-generated chart")
    else:
        fig = px.bar(df, x=x, y=y, title="Auto-generated chart")

    chart_path = "data/chart.html"
    fig.write_html(chart_path)

    state["chart_path"] = chart_path
    state["chart_type"] = chart_type
    return state
