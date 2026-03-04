import streamlit as st
import requests
import pandas as pd
import uuid

API_URL = "http://127.0.0.1:8000/query"

st.set_page_config(page_title="AI Analyst Agent", layout="wide")

st.title("AI Analyst Agent")
st.caption("Conversational multi-agent analytics system")

# -----------------------------
# Session Initialization
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# -----------------------------
# Display Chat History
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("chart_path"):
            try:
                with open(message["chart_path"], "r", encoding="utf-8") as f:
                    chart_html = f.read()
                st.components.v1.html(chart_html, height=400)
            except:
                pass

        if message.get("result"):
            df = pd.DataFrame(message["result"])
            if not df.empty:
                st.dataframe(df, use_container_width=True)

        if message.get("sql"):
            with st.expander("Show SQL"):
                st.code(message["sql"], language="sql")

# -----------------------------
# User Input
# -----------------------------
prompt = st.chat_input("Ask a data question...")

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            response = requests.post(
                API_URL,
                json={
                    "question": prompt,
                    "session_id": st.session_state.session_id
                }
            )

            data = response.json()

            assistant_message = {
                "role": "assistant",
                "content": data["insights"],
                "chart_path": data.get("chart_path"),
                "result": data.get("result"),
                "sql": data.get("sql")
            }

            st.markdown(data["insights"])

            if data.get("chart_path"):
                with open(data["chart_path"], "r", encoding="utf-8") as f:
                    chart_html = f.read()
                st.components.v1.html(chart_html, height=400)

            if data.get("result"):
                df = pd.DataFrame(data["result"])
                st.dataframe(df, use_container_width=True)

            with st.expander("Show SQL"):
                st.code(data["sql"], language="sql")

    st.session_state.messages.append(assistant_message)