import os
import uuid
import pandas as pd
import plotly.express as px
import json
from app.agents.state import AgentState
from app.core.llm import get_llm


# -----------------------------
# Column type classifiers
# -----------------------------

TIME_KEYWORDS = ["date", "time", "month", "year", "day", "week", "quarter"]
CATEGORY_KEYWORDS = ["name", "region", "segment", "category", "type", "status",
                     "country", "city", "product", "brand", "department"]
METRIC_KEYWORDS = ["revenue", "sales", "amount", "price", "total", "count",
                   "profit", "cost", "value", "qty", "quantity", "avg", "sum"]


def classify_columns(df: pd.DataFrame) -> dict:
    """
    Classify each column as: time | category | metric | unknown
    Returns dict: {col_name: type}
    """
    classification = {}
    for col in df.columns:
        col_lower = col.lower()
        dtype = df[col].dtype

        if any(k in col_lower for k in TIME_KEYWORDS):
            classification[col] = "time"
        elif any(k in col_lower for k in METRIC_KEYWORDS) and pd.api.types.is_numeric_dtype(dtype):
            classification[col] = "metric"
        elif pd.api.types.is_numeric_dtype(dtype):
            if df[col].nunique() > 20:
                classification[col] = "metric"
            else:
                classification[col] = "category"
        elif any(k in col_lower for k in CATEGORY_KEYWORDS):
            classification[col] = "category"
        else:
            classification[col] = "category"

    return classification


def smart_chart_config(df: pd.DataFrame, question: str = "") -> dict:
    """
    Decide chart type, x, y, color based on column semantics.
    Returns dict: {chart_type, x, y, color (optional), barmode (optional)}
    """
    cols = list(df.columns)
    n_cols = len(cols)
    classification = classify_columns(df)

    time_cols = [c for c, t in classification.items() if t == "time"]
    metric_cols = [c for c, t in classification.items() if t == "metric"]
    category_cols = [c for c, t in classification.items() if t == "category"]

    # ---- 2-column ----
    if n_cols == 2:
        if time_cols:
            x = time_cols[0]
            y = metric_cols[0] if metric_cols else cols[1]
            return {"chart_type": "line", "x": x, "y": y, "color": None}

        y = metric_cols[0] if metric_cols else cols[1]
        x = [c for c in cols if c != y][0]
        return {"chart_type": "bar", "x": x, "y": y, "color": None}

    # ---- 3-column ----
    if n_cols == 3:
        # category + category + metric → grouped bar (e.g. customer, region, revenue)
        if len(category_cols) >= 2 and metric_cols:
            # Use lower-cardinality category as color (grouping)
            cat_a, cat_b = category_cols[0], category_cols[1]
            if df[cat_a].nunique() <= df[cat_b].nunique():
                x, color = cat_b, cat_a
            else:
                x, color = cat_a, cat_b
            y = metric_cols[0]
            return {"chart_type": "bar", "x": x, "y": y, "color": color, "barmode": "group"}

        # time + category + metric → line per category
        if time_cols and category_cols and metric_cols:
            return {
                "chart_type": "line",
                "x": time_cols[0],
                "y": metric_cols[0],
                "color": category_cols[0]
            }

        # category + metric + metric → scatter
        if category_cols and len(metric_cols) >= 2:
            return {
                "chart_type": "scatter",
                "x": metric_cols[0],
                "y": metric_cols[1],
                "color": category_cols[0]
            }

        # generic fallback for 3 cols
        y = metric_cols[0] if metric_cols else cols[-1]
        x = category_cols[0] if category_cols else cols[0]
        color_candidates = [c for c in cols if c != x and c != y]
        return {"chart_type": "bar", "x": x, "y": y, "color": color_candidates[0] if color_candidates else None}

    # ---- 4+ columns ----
    if time_cols and metric_cols:
        return {
            "chart_type": "line",
            "x": time_cols[0],
            "y": metric_cols[0],
            "color": category_cols[0] if category_cols else None
        }

    if category_cols and metric_cols:
        x = category_cols[0]
        color = category_cols[1] if len(category_cols) > 1 else None
        return {"chart_type": "bar", "x": x, "y": metric_cols[0], "color": color, "barmode": "group"}

    # ---- absolute fallback ----
    return {"chart_type": "bar", "x": cols[0], "y": cols[-1], "color": None}


def llm_refine_config(df: pd.DataFrame, config: dict, question: str) -> dict:
    """
    Ask LLM to verify or improve the chart config.
    Only accepts the LLM answer if it uses valid column names.
    """
    try:
        llm = get_llm()

        col_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample = str(df[col].iloc[0]) if len(df) > 0 else "N/A"
            col_info.append(f"  - {col} ({dtype}), example value: '{sample}'")

        col_desc = "\n".join(col_info)

        prompt = f"""
You are a data visualization expert.

User question: "{question}"

Available columns:
{col_desc}

Current chart config:
{json.dumps(config)}

Valid chart types: bar, line, scatter
Valid column names: {list(df.columns)}

Instructions:
- "x" should be the axis that best represents categories, time, or grouping
- "y" should be the numeric metric to measure
- "color" should be used when there is a secondary categorical dimension to group by (e.g. region, segment). Set to null if not needed.
- "barmode" can be "group" or "stack" for grouped/stacked bar charts. Set to null if not a bar chart.
- All column names in x, y, color MUST exactly match the column names listed above.

Return ONLY a JSON object. No explanation. No markdown.
Example: {{"chart_type": "bar", "x": "region", "y": "total_revenue", "color": "segment", "barmode": "group"}}
"""

        response = llm.invoke(prompt)
        text = response.content.strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            refined = json.loads(text[start:end])
            valid_cols = set(df.columns)

            # Strict validation
            if (refined.get("x") in valid_cols and
                    refined.get("y") in valid_cols and
                    refined.get("chart_type") in ["bar", "line", "scatter"]):

                color = refined.get("color")
                if color and color not in valid_cols:
                    refined["color"] = None

                return refined

    except Exception as e:
        print(f"LLM chart refinement failed, using smart config: {e}")

    return config


def build_plotly_figure(df: pd.DataFrame, config: dict, question: str):
    """Build a Plotly figure from resolved config."""
    chart_type = config.get("chart_type", "bar")
    x = config.get("x")
    y = config.get("y")
    color = config.get("color") or None
    barmode = config.get("barmode") or "group"

    title = question.strip().capitalize() if question else "Query Results"

    common_kwargs = dict(
        x=x,
        y=y,
        title=title,
        template="plotly_dark",
        height=420,
        color=color,
    )

    if chart_type == "line":
        fig = px.line(df, **common_kwargs, markers=True)
    elif chart_type == "scatter":
        fig = px.scatter(df, **common_kwargs)
    else:
        fig = px.bar(df, **common_kwargs, barmode=barmode)

    # Rotate labels for many categories
    n_x_vals = df[x].nunique() if x in df.columns else 0
    if n_x_vals > 8:
        fig.update_layout(xaxis_tickangle=-40)

    fig.update_layout(
        margin=dict(l=50, r=20, t=55, b=90),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(size=12),
        xaxis_title=x,
        yaxis_title=y,
    )

    return fig


# -----------------------------
# Main visualization node
# -----------------------------

def visualization_node(state: AgentState) -> AgentState:
    result = state.get("result")
    question = state.get("question", "")

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

    # Convert numeric time-like columns to string for cleaner axis display
    for col in df.columns:
        if any(k in col.lower() for k in TIME_KEYWORDS):
            try:
                if df[col].dtype in ["int64", "float64"]:
                    df[col] = df[col].astype(int).astype(str)
            except Exception:
                pass

    # Step 1: Smart deterministic config
    config = smart_chart_config(df, question)

    # Step 2: LLM refinement pass
    config = llm_refine_config(df, config, question)

    # Step 3: Build and save chart
    try:
        fig = build_plotly_figure(df, config, question)
        os.makedirs("data/charts", exist_ok=True)
        chart_id = str(uuid.uuid4())[:8]
        chart_path = f"data/charts/chart_{chart_id}.html"
        fig.write_html(chart_path, include_plotlyjs="cdn", full_html=True)

        state["chart_path"] = chart_path
        state["chart_type"] = config.get("chart_type", "bar")

    except Exception as e:
        print(f"Chart generation failed: {e}")
        state["chart_path"] = ""
        state["chart_type"] = "none"

    return state