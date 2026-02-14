import pandas as pd
import plotly.express as px
from app.agents.state import AgentState


def visualization_node(state: AgentState) -> AgentState:
    result = state.get("result")

    # Handle error or empty result
    if not result or isinstance(result, dict):
        state["chart_path"] = ""
        return state

    try:
        df = pd.DataFrame(result)
    except Exception:
        state["chart_path"] = ""
        return state

    # If only one column or empty, skip chart
    if df.empty or df.shape[1] < 2:
        state["chart_path"] = ""
        return state

    x = df.columns[0]
    y = df.columns[1]

    fig = px.bar(df, x=x, y=y, title="Auto-generated chart")
    chart_path = "data/chart.html"
    fig.write_html(chart_path)

    state["chart_path"] = chart_path
    return state
