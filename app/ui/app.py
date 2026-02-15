import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000/query"

st.set_page_config(page_title="AI Analyst Agent", layout="wide")

st.title("AI Analyst Agent")
st.caption("Ask natural language questions and get instant insights.")

# -----------------------------
# Session state
# -----------------------------
if "response_data" not in st.session_state:
    st.session_state.response_data = None

# -----------------------------
# Input Row
# -----------------------------
input_col, button_col = st.columns([5, 1])

with input_col:
    question = st.text_input(
        "Ask a question",
        placeholder="e.g. Monthly revenue trend"
    )

with button_col:
    run_clicked = st.button("Run")

# -----------------------------
# Compact Example Questions
# -----------------------------
examples = [
    "Monthly revenue trend",
    "Top customers by revenue",
    "Revenue by region",
    "Top products by sales",
    "Average order value",
    "Year over year revenue",
    "Revenue by segment",
    "Top 5 customers per region",
    "Monthly order count",
    "Category revenue distribution",
]

st.markdown("**Try an example:**")

row1 = st.columns(5)
row2 = st.columns(5)

for i in range(5):
    if row1[i].button(examples[i]):
        question = examples[i]
        run_clicked = True

for i in range(5, 10):
    if row2[i - 5].button(examples[i]):
        question = examples[i]
        run_clicked = True

# -----------------------------
# Run Query
# -----------------------------
if run_clicked and question:
    with st.spinner("Analyzing your data..."):
        try:
            response = requests.post(
                API_URL,
                json={"question": question},
                timeout=60
            )
            if response.status_code == 200:
                st.session_state.response_data = response.json()
            else:
                st.error("API error.")
        except Exception as e:
            st.error(str(e))

data = st.session_state.response_data

# -----------------------------
# Results Section (Horizontal Layout)
# -----------------------------
# -----------------------------
# Results Section (Horizontal Layout)
# -----------------------------
if data:
    chart_col, insights_col, table_col = st.columns([2, 1.2, 1.8])

    # -------------------------
    # Chart Panel
    # -------------------------
    with chart_col:
        st.subheader("Chart")
        if data["chart_path"] and data["chart_type"] != "none":
            try:
                with open(data["chart_path"], "r", encoding="utf-8") as f:
                    chart_html = f.read()
                st.components.v1.html(chart_html, height=450)
            except Exception:
                st.info("Chart unavailable.")
        else:
            st.info("No chart generated.")

    # -------------------------
    # Insights Panel
    # -------------------------
    with insights_col:
        st.subheader("Insights")
        st.write(data["insights"])

        # Hidden agent plan
        with st.expander("Agent’s Plan"):
            st.write(data["plan"])

    # -------------------------
    # Table + SQL Panel
    # -------------------------
    with table_col:
        st.subheader("Data")

        df = pd.DataFrame(data["result"])

        if not df.empty:
            max_rows = len(df)
            rows_to_show = st.slider(
                "Rows",
                1,
                max_rows,
                min(20, max_rows)
            )

            filtered_df = df.head(rows_to_show)
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("No data returned.")
        st.write("DEBUG SQL:", data.get("sql"))
        # SQL section
        with st.expander("Show SQL"):
            st.code(data["sql"], language="sql")

# -----------------------------
# Help Section
# -----------------------------

with st.expander("📖 How to use"):
    st.markdown("""
    1. Start the FastAPI backend
       ```
       uvicorn app.api.main:app --reload
       ```
    2. Enter a data question
    3. Click **Run Query**
    4. Explore chart, insights, SQL, and data

    **Example questions:**
    - Monthly revenue trend
    - Top customers by revenue
    - Revenue by region
    """)