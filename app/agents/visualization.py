import pandas as pd
import plotly.express as px
import json
from app.agents.state import AgentState
from app.core.llm import get_llm


def visualization_node(state: AgentState) -> AgentState:
    result = state.get("result")

    # Handle error or empty result
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

    # Default fallback
    chart_type = "bar"
    x = df.columns[0]
    y = df.columns[1]

    try:
        llm = get_llm()

        prompt = f"""
You are a data visualization expert.

Given this dataset schema:
Columns: {list(df.columns)}

Decide:
1. Best chart type: bar, line, or scatter
2. x-axis column
3. y-axis column

Return JSON only:
{{
  "chart_type": "...",
  "x": "...",
  "y": "..."
}}
"""

        response = llm.invoke(prompt)
        chart_config = json.loads(response.content)

        chart_type = chart_config.get("chart_type", chart_type)
        x = chart_config.get("x", x)
        y = chart_config.get("y", y)

    except Exception as e:
        print("Visualization LLM failed, using fallback:", e)

        # Generate chart
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