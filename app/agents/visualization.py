import pandas as pd
import plotly.express as px
from app.agents.state import AgentState


def visualization_node(state: AgentState) -> AgentState:
    if not state["result"]:
        state["chart_path"] = ""
        return state

    df = pd.DataFrame(state["result"])

    # Simple heuristic: bar chart if 2 columns
    if df.shape[1] >= 2:
        x = df.columns[0]
        y = df.columns[1]

        fig = px.bar(df, x=x, y=y, title="Auto-generated chart")
        chart_path = "data/chart.html"
        fig.write_html(chart_path)

        state["chart_path"] = chart_path
    else:
        state["chart_path"] = ""

    return state