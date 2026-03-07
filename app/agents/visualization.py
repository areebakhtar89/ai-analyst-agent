import os
import re
import uuid
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from app.agents.state import AgentState
from app.core.llm import get_llm
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

TIME_KEYWORDS = ["date", "time", "month", "year", "day", "week", "quarter"]
CATEGORY_KEYWORDS = ["name", "region", "segment", "category", "type", "status",
                     "country", "city", "product", "brand", "department"]
METRIC_KEYWORDS = ["revenue", "sales", "amount", "price", "total", "count",
                   "profit", "cost", "value", "qty", "quantity", "avg", "sum"]

# Chart types explicitly supported
VALID_CHART_TYPES = ["bar", "line", "scatter", "pie", "area"]

# Keywords that map user intent to chart type
CHART_TYPE_HINTS = {
    "pie":       ["pie chart", "pie graph", "as a pie", "in a pie", "donut"],
    "line":      ["line chart", "line graph", "trend", "over time", "time series", "monthly", "yearly", "weekly"],
    "bar":       ["bar chart", "bar graph", "histogram", "column chart"],
    "scatter":   ["scatter", "scatter plot", "correlation", "vs ", " versus "],
    "area":      ["area chart", "area graph", "stacked area"],
}


def detect_explicit_chart_type(question: str) -> str | None:
    """
    If the user explicitly asked for a specific chart type, return it.
    This overrides ALL other logic — highest priority.
    """
    q = question.lower()
    for chart_type, keywords in CHART_TYPE_HINTS.items():
        if any(kw in q for kw in keywords):
            return chart_type
    return None


def classify_columns(df: pd.DataFrame) -> dict:
    """Classify columns as time, metric, or category based on keywords and data types."""
    logger.debug(f"Classifying columns for DataFrame with {len(df.columns)} columns")
    
    classification = {}
    for col in df.columns:
        col_lower = col.lower()
        dtype = df[col].dtype
        if any(k in col_lower for k in TIME_KEYWORDS):
            classification[col] = "time"
        elif any(k in col_lower for k in METRIC_KEYWORDS) and pd.api.types.is_numeric_dtype(dtype):
            classification[col] = "metric"
        elif pd.api.types.is_numeric_dtype(dtype):
            classification[col] = "metric" if df[col].nunique() > 20 else "category"
        elif any(k in col_lower for k in CATEGORY_KEYWORDS):
            classification[col] = "category"
        else:
            classification[col] = "category"
    return classification


def _reduce_to_plottable(df: pd.DataFrame, x: str, color: str, y: str) -> pd.DataFrame:
    """
    When there are more dimension columns than we can plot (4+ cols),
    aggregate the metric by x + color, summing away any extra dimensions.
    This prevents overlapping bars / invisible slivers.
    """
    group_cols = [c for c in [x, color] if c is not None]
    if not group_cols:
        return df
    try:
        return df.groupby(group_cols, as_index=False)[y].sum()
    except Exception:
        return df


def smart_chart_config(df: pd.DataFrame, question: str = "", forced_type: str = None) -> dict:
    """
    Decide chart config. If forced_type is set, use it regardless of column analysis.
    For 4+ column results, aggregates away extra dimensions so charts render cleanly.
    """
    logger.info(f"Generating smart chart config for question: '{question[:50]}...' if len(question) > 50 else question")
    
    cols = list(df.columns)
    n_cols = len(cols)
    classification = classify_columns(df)

    time_cols     = [c for c, t in classification.items() if t == "time"]
    metric_cols   = [c for c, t in classification.items() if t == "metric"]
    category_cols = [c for c, t in classification.items() if t == "category"]

    y = metric_cols[0] if metric_cols else cols[-1]

    # ── Resolve x and color using cardinality-aware logic ──
    # For 4+ cols with time + 2 categories: x=time, color=lowest-cardinality category
    # For 4+ cols with 2 time cols: x=highest-cardinality time, color=lowest
    dim_cols = time_cols + category_cols  # all non-metric dimensions

    if len(time_cols) >= 2:
        by_card = sorted(time_cols, key=lambda c: df[c].nunique(), reverse=True)
        x = by_card[0]
        color = by_card[1]
    elif time_cols and len(category_cols) >= 1:
        x = time_cols[0]
        # Pick lowest-cardinality category as color (most readable legend)
        color = min(category_cols, key=lambda c: df[c].nunique()) if category_cols else None
    elif len(category_cols) >= 2:
        by_card = sorted(category_cols, key=lambda c: df[c].nunique(), reverse=True)
        x = by_card[0]
        color = by_card[-1]
    elif category_cols:
        x = category_cols[0]
        color = None
    else:
        x = cols[0]
        color = None

    # If user explicitly requested a chart type, use it
    if forced_type:
        if forced_type == "pie":
            names_col  = category_cols[0] if category_cols else cols[0]
            values_col = metric_cols[0] if metric_cols else cols[-1]
            return {"chart_type": "pie", "names": names_col, "values": values_col}
        if forced_type == "area":
            return {"chart_type": "area", "x": x, "y": y, "color": color}
        return {"chart_type": forced_type, "x": x, "y": y, "color": color}

    # ── Auto-detect from data shape ──
    if n_cols == 2:
        chart_type = "line" if time_cols else "bar"
        return {"chart_type": chart_type, "x": x, "y": y, "color": None}

    if n_cols == 3:
        if len(category_cols) >= 2 and metric_cols:
            cat_a, cat_b = category_cols[0], category_cols[1]
            x     = cat_b if df[cat_a].nunique() <= df[cat_b].nunique() else cat_a
            color = cat_a if x == cat_b else cat_b
            return {"chart_type": "bar", "x": x, "y": y, "color": color, "barmode": "group"}
        if time_cols and category_cols and metric_cols:
            return {"chart_type": "line", "x": time_cols[0], "y": y, "color": category_cols[0]}
        if category_cols and len(metric_cols) >= 2:
            return {"chart_type": "scatter", "x": metric_cols[0], "y": metric_cols[1],
                    "color": category_cols[0] if category_cols else None}

    # ── 4+ columns: aggregate extra dimensions away, then plot ──
    if n_cols >= 4:
        if time_cols and metric_cols:
            chart_type = "line" if df[x].nunique() > 6 else "bar"
            barmode    = "group" if color else "relative"
            return {"chart_type": chart_type, "x": x, "y": y, "color": color,
                    "barmode": barmode, "_aggregate": True}
        if category_cols and metric_cols:
            return {"chart_type": "bar", "x": x, "y": y, "color": color,
                    "barmode": "group", "_aggregate": True}

    return {"chart_type": "bar", "x": cols[0], "y": cols[-1], "color": None}


def llm_refine_config(df: pd.DataFrame, config: dict, question: str, forced_type: str = None) -> dict:
    """
    LLM refinement pass. Skipped entirely if user forced a chart type.
    """
    # Don't let LLM override explicit user chart request
    if forced_type:
        return config

    try:
        llm = get_llm()

        col_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample = str(df[col].iloc[0]) if len(df) > 0 else "N/A"
            col_info.append(f"  - {col} ({dtype}), example: '{sample}'")

        prompt = f"""You are a data visualization expert.

User question: "{question}"

Available columns:
{chr(10).join(col_info)}

Current chart config:
{json.dumps(config)}

Valid chart types: bar, line, scatter, pie, area
Valid column names: {list(df.columns)}

Rules:
- x, y, names, values, color must be valid column names or null
- For pie charts use: {{"chart_type": "pie", "names": "<category_col>", "values": "<metric_col>"}}
- For bar/line/scatter/area use: {{"chart_type": "...", "x": "...", "y": "...", "color": null_or_col, "barmode": null_or_group_or_stack}}
- color = a categorical column for grouping, or null
- Do NOT change chart_type if current config is already correct

Return ONLY a JSON object. No markdown, no explanation.
"""
        response = llm.invoke(prompt)
        text = response.content.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            refined = json.loads(text[start:end])
            valid_cols = set(df.columns)
            chart_type = refined.get("chart_type")

            if chart_type not in VALID_CHART_TYPES:
                return config

            if chart_type == "pie":
                if refined.get("names") in valid_cols and refined.get("values") in valid_cols:
                    return refined
            else:
                if refined.get("x") in valid_cols and refined.get("y") in valid_cols:
                    color = refined.get("color")
                    if color and color not in valid_cols:
                        refined["color"] = None
                    return refined

    except Exception as e:
        print(f"LLM chart refinement failed: {e}")

    return config


def build_plotly_figure(df: pd.DataFrame, config: dict, question: str):
    """Build Plotly figure supporting bar, line, scatter, pie, area.
    Aggregates df when config contains _aggregate=True to avoid overlapping series."""
    chart_type = config.get("chart_type", "bar")
    title = question.strip().capitalize() if question else "Query Results"

    base_layout = dict(
        template="plotly_dark",
        height=420,
        title=title,
        margin=dict(l=50, r=20, t=55, b=90),
        font=dict(size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    if chart_type == "pie":
        names = config.get("names")
        values = config.get("values")
        fig = px.pie(
            df, names=names, values=values,
            title=title, template="plotly_dark", height=420,
            hole=0.35  # donut style looks cleaner
        )
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(**{k: v for k, v in base_layout.items() if k not in ["margin"]})
        return fig

    x = config.get("x")
    y = config.get("y")
    color = config.get("color") or None
    barmode = config.get("barmode") or "group"

    common_kwargs = dict(x=x, y=y, title=title, template="plotly_dark",
                         height=420, color=color)

    if chart_type == "line":
        fig = px.line(df, **common_kwargs, markers=True)
    elif chart_type == "scatter":
        fig = px.scatter(df, **common_kwargs)
    elif chart_type == "area":
        fig = px.area(df, **common_kwargs)
    else:  # bar
        fig = px.bar(df, **common_kwargs, barmode=barmode)

    n_x_vals = df[x].nunique() if x in df.columns else 0
    if n_x_vals > 8:
        fig.update_layout(xaxis_tickangle=-40)

    fig.update_layout(
        **{k: v for k, v in base_layout.items() if k != "title"},
        xaxis_title=x,
        yaxis_title=y,
    )
    return fig


# ─────────────────────────────────────────
# Main visualization node
# ─────────────────────────────────────────

def visualization_node(state: AgentState) -> AgentState:
    log_agent_activity(logger, "Visualization", "Starting", {"question": state.get("question", "")})
    
    result = state.get("result")
    question = state.get("question", "")
    
    logger.info(f"Starting visualization node with {len(result) if result else 0} result rows")

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

    # Convert numeric time columns to string
    for col in df.columns:
        if any(k in col.lower() for k in TIME_KEYWORDS):
            try:
                if df[col].dtype in ["int64", "float64"]:
                    df[col] = df[col].astype(int).astype(str)
            except Exception:
                pass

    # Step 1: Check if user explicitly requested a chart type — HIGHEST PRIORITY
    forced_type = detect_explicit_chart_type(question)

    # Step 2: Smart deterministic config (respects forced_type)
    config = smart_chart_config(df, question, forced_type=forced_type)

    # Step 3: Aggregate BEFORE LLM refinement.
    # llm_refine_config returns a new JSON object that drops unknown keys like _aggregate.
    # So we must reduce the df HERE before LLM ever sees it, then remove the flag.
    if config.get("_aggregate"):
        df = _reduce_to_plottable(df, config.get("x"), config.get("color"), config.get("y"))
        config.pop("_aggregate", None)

    # Step 4: LLM refinement — now sees clean aggregated df (skipped if forced_type set)
    config = llm_refine_config(df, config, question, forced_type=forced_type)

    # Step 5: Build and save
    try:
        fig = build_plotly_figure(df, config, question)
        os.makedirs("data/charts", exist_ok=True)
        chart_id = str(uuid.uuid4())[:8]
        chart_path = f"data/charts/chart_{chart_id}.html"
        fig.write_html(chart_path, include_plotlyjs="cdn", full_html=True)
        
        logger.info(f"Chart saved successfully: {chart_path}")
        state["chart_path"] = chart_path
        state["chart_type"] = config.get("chart_type", "bar")
        
        log_agent_activity(logger, "Visualization", "Chart created", {"chart_type": config.get("chart_type", "bar")})
    except Exception as e:
        logger.error(f"Chart generation failed: {str(e)}")
        state["chart_path"] = ""
        state["chart_type"] = "none"
        
        log_agent_activity(logger, "Visualization", "Error", {"error": str(e)})

    return state