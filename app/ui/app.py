import streamlit as st
import requests
import pandas as pd
import uuid
import re

API_URL = "http://127.0.0.1:8000/query"

st.set_page_config(page_title="AI Analyst Agent", layout="wide")

st.title("AI Analyst Agent")
st.caption("Conversational multi-agent analytics system")

# -----------------------------
# Session Init
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# -----------------------------
# Utility: Sanitize LLM text
# -----------------------------

def sanitize_text(text: str) -> str:
    """Remove LaTeX math and other symbols that break Streamlit markdown."""
    if not text:
        return ""
    # Replace $ signs (LaTeX math delimiters) with nothing
    text = re.sub(r'\$+', '', text)
    # Remove any leftover LaTeX-style formatting
    text = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', text)
    return text.strip()


# -----------------------------
# Utility: Render one assistant turn
# -----------------------------

def render_assistant_turn(insights, result, chart_path, sql, slider_key):
    """Renders insights + 3-column layout (chart | gap | table) consistently."""

    # Insights above columns
    if insights:
        st.markdown(sanitize_text(insights))

    col1, col2, col3 = st.columns([1.4, 0.2, 1.4])

    # --- Chart ---
    with col1:
        if chart_path:
            try:
                with open(chart_path, "r", encoding="utf-8") as f:
                    chart_html = f.read()
                st.components.v1.html(chart_html, height=420)
            except Exception:
                st.info("Chart unavailable")
        else:
            st.info("No chart generated")

    # --- Spacer ---
    with col2:
        pass

    # --- Data Table ---
    with col3:
        if result:
            df = pd.DataFrame(result)
            if not df.empty:
                st.subheader("Data")
                max_rows = len(df)
                if max_rows > 5:
                    rows = st.slider(
                        "Rows",
                        min_value=5,
                        max_value=max_rows,
                        value=min(20, max_rows),
                        key=slider_key
                    )
                else:
                    rows = max_rows

                st.dataframe(df.head(rows), use_container_width=True)

                if sql:
                    with st.expander("Show SQL"):
                        st.code(sql, language="sql")
        else:
            st.info("No data returned")


# -----------------------------
# Example Questions
# -----------------------------

example_questions = [
    "Monthly revenue trend",
    "Top customers by revenue",
    "Revenue by region",
    "Top products by sales",
    "Average order value",
    "Year over year revenue",
    "Revenue by segment",
    "Top 5 customers per region",
    "Monthly order count",
    "Category revenue distribution"
]

st.subheader("Try an example")
cols = st.columns(5)
for i, q in enumerate(example_questions):
    if cols[i % 5].button(q, key=f"ex_{i}"):
        st.session_state["example_prompt"] = q

st.divider()

# -----------------------------
# Chat History
# -----------------------------

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            render_assistant_turn(
                insights=msg.get("insights", ""),
                result=msg.get("result"),
                chart_path=msg.get("chart_path"),
                sql=msg.get("sql"),
                slider_key=f"history_slider_{idx}"
            )

# -----------------------------
# Input
# -----------------------------

prompt = st.chat_input("Ask a data question...")

if "example_prompt" in st.session_state:
    prompt = st.session_state.pop("example_prompt")

if prompt:
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Show assistant response
    with st.chat_message("assistant"):
        with st.spinner("Running agents..."):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "question": prompt,
                        "session_id": st.session_state.session_id
                    },
                    timeout=60
                )
                data = response.json()
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()

        insights = data.get("insights", "")
        result = data.get("result", [])
        chart_path = data.get("chart_path", "")
        sql = data.get("sql", "")

        render_assistant_turn(
            insights=insights,
            result=result,
            chart_path=chart_path,
            sql=sql,
            slider_key=f"live_slider_{uuid.uuid4()}"
        )

    st.session_state.messages.append({
        "role": "assistant",
        "insights": insights,
        "chart_path": chart_path,
        "result": result,
        "sql": sql
    })