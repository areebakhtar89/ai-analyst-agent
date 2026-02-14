"""Streamlit frontend for the AI Analyst Agent.

This module provides the user interface for interacting with the AI analyst,
allowing users to ask natural language questions and view analysis results.
"""

import streamlit as st
import requests

# API endpoint for the backend service
API_URL = "http://127.0.0.1:8000/query"

# Configure Streamlit page
st.title("AI Analyst Agent")
st.markdown("Ask questions about your data and get AI-powered insights with visualizations.")

# User input section
question = st.text_input("Ask a data question:", placeholder="e.g., What are our top selling products?")

# Process user query when button is clicked
if st.button("Run Query") and question:
    try:
        # Send request to backend API
        response = requests.post(API_URL, json={"question": question})
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Display analysis results in organized sections
            st.subheader("📋 Analysis Plan")
            st.write(data["plan"])

            st.subheader("🔍 Generated SQL")
            st.code(data["sql"], language="sql")

            st.subheader("💡 Business Insights")
            st.write(data["insights"])

            st.subheader("📊 Query Results")
            st.write(data["result"])

            # Display chart if one was generated
            if data["chart_path"] and data["chart_type"] != "none":
                st.subheader("📈 Data Visualization")
                try:
                    # Read and display the HTML chart
                    with open(data["chart_path"], 'r') as f:
                        chart_html = f.read()
                    st.components.v1.html(chart_html, height=500)
                except FileNotFoundError:
                    st.error("Chart file not found. Please try again.")
                except Exception as e:
                    st.error(f"Error displaying chart: {str(e)}")
        else:
            st.error(f"Error: API returned status code {response.status_code}")
            st.error(response.text)
            
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend API. Please make sure the FastAPI server is running on http://127.0.0.1:8000")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

# Add instructions for first-time users
with st.expander("📖 How to use"):
    st.markdown("""
    1. Make sure the FastAPI backend is running (`python -m app.api.main`)
    2. Type your data question in the text box above
    3. Click "Run Query" to get AI-powered analysis
    4. View the generated plan, SQL, insights, and visualizations
    
    **Example questions:**
    - What are our top selling products?
    - Show me sales trends over time
    - Which customers have placed the most orders?
    - What is the average order value?
    """)
