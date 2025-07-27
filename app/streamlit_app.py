import streamlit as st
import requests
import json
import os
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="TCS Financial Forecasting Dashboard", layout="wide")

# --- Sidebar for global settings ---
st.sidebar.title("Settings")
default_api_url = "http://127.0.0.1:8000/forecast"
api_url = st.sidebar.text_input("FastAPI Forecast Endpoint URL", value=default_api_url, help="URL for the FastAPI /forecast endpoint.")

db_mode = st.sidebar.radio("DB Credentials Mode", ["Provide credentials", "Read from .env"], index=0, help="Choose how to provide MySQL credentials.")
if db_mode == "Provide credentials":
    db_host = st.sidebar.text_input("DB Host", value=os.getenv("DB_HOST", "localhost"), help="MySQL server host.")
    db_user = st.sidebar.text_input("DB User", value=os.getenv("DB_USER", "root"), help="MySQL username.")
    db_password = st.sidebar.text_input("DB Password", value=os.getenv("DB_PASSWORD", ""), type="password", help="MySQL password.")
    db_name = st.sidebar.text_input("DB Name", value=os.getenv("DB_NAME", "tcs"), help="MySQL database name.")
else:
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "tcs")
    st.sidebar.info(f"Using .env: Host: `{db_host}` | User: `{db_user}` | DB: `{db_name}`")

st.title("TCS Financial Forecasting Dashboard")

# --- Tabs for Forecast and Logs ---
tab1, tab2 = st.tabs(["📊 Forecast", "🗂️ Logs"])

with tab1:
    st.header("Generate Financial Forecast")
    st.markdown("""
    Enter your forecasting task below. The agent will analyze recent financial reports and transcripts to generate a qualitative business outlook for TCS.
    """)
    task_input = st.text_area(
        "Forecast Task", 
        "Analyze the financial reports and transcripts for the last three quarters and provide a qualitative forecast for the upcoming quarter. Your forecast must identify key financial trends (e.g., revenue growth, margin pressure), summarize management's stated outlook, and highlight any significant risks or opportunities mentioned",
        help="Describe the forecasting task you want the agent to perform."
    )
    if st.button("Generate Forecast", key="forecast_btn"):
        with st.spinner("Contacting the FastAPI agent..."):
            try:
                response = requests.post(api_url, json={"task": task_input})
                if response.status_code == 200:
                    result = response.json()
                    st.success("Forecast Generated!")
                    # Sectioned, appealing output
                    if "trends" in result:
                        st.subheader("Trends")
                        for k, v in result["trends"].items():
                            st.markdown(f"- **{k.replace('_',' ').title()}**: {v}")
                    if "management_outlook" in result:
                        st.subheader("Management Outlook")
                        for k, v in result["management_outlook"].items():
                            if isinstance(v, list):
                                st.markdown(f"- **{k.replace('_',' ').title()}**:")
                                for item in v:
                                    st.markdown(f"    - {item}")
                            else:
                                st.markdown(f"- **{k.replace('_',' ').title()}**: {v}")
                    if "risks" in result:
                        st.subheader("Risks")
                        for r in result["risks"]:
                            st.markdown(f"- **{r.get('risk','')}** (Impact: {r.get('impact','')})")
                    if "opportunities" in result:
                        st.subheader("Opportunities")
                        for o in result["opportunities"]:
                            st.markdown(f"- **{o.get('opportunity','')}** (Benefit: {o.get('benefit','')})")
                    if "assumptions" in result:
                        st.subheader("Assumptions")
                        for a in result["assumptions"]:
                            st.markdown(f"- {a}")
                    if "overall_forecast" in result:
                        st.subheader("Overall Forecast")
                        st.markdown(f"{result['overall_forecast'].get('summary','')}")
                        st.markdown(f"**Confidence Level:** {result['overall_forecast'].get('confidence_level','')}")
                else:
                    st.error(f"API Error: {response.status_code}")
                    try:
                        st.write(response.json())
                    except:
                        st.write(response.text)
            except Exception as e:
                st.error(f"Error contacting FastAPI: {e}")

with tab2:
    st.header("Recent Forecast Logs")
    st.markdown("""
    View the 10 most recent forecast requests and responses. Select a log to see full details.
    """)
    if st.button("Show Recent Logs", key="logs_btn"):
        with st.spinner("Querying MySQL database for logs..."):
            try:
                conn = mysql.connector.connect(
                    host=db_host,
                    user=db_user,
                    password=db_password,
                    database=db_name,
                )
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT timestamp, request_data, response_data FROM forecast_logs ORDER BY timestamp DESC LIMIT 10"
                )
                logs = cursor.fetchall()
                cursor.close()
                conn.close()
            except Exception as e:
                st.error(f"Database error: {e}")
                logs = []
            if logs:
                table_data = []
                for idx, log in enumerate(logs):
                    req = log.get("request_data", "")
                    resp = log.get("response_data", "")
                    req_short = req[:60] + ("..." if len(req) > 60 else "")
                    resp_short = resp[:60] + ("..." if len(resp) > 60 else "")
                    table_data.append({
                        "Index": idx,
                        "Timestamp": log.get("timestamp", "N/A"),
                        "Request": req_short,
                        "Response": resp_short
                    })
                df = pd.DataFrame(table_data)
                st.dataframe(df.style.apply(lambda x: ['background-color: #f9f9f9' if i%2==0 else '' for i in range(len(x))], axis=0), use_container_width=True)
                log_options = [f"{row['Timestamp']} (#{row['Index']})" for row in table_data]
                selected_idx = st.selectbox("Select log for details", options=list(range(len(logs))), format_func=lambda i: log_options[i])
                log = logs[selected_idx]
                with st.expander(f"Log Details for {log.get('timestamp','N/A')}"):
                    st.markdown("**Request (full):**")
                    try:
                        st.json(json.loads(log.get("request_data", "{}")))
                    except:
                        st.write(log.get("request_data", ""))
                    st.markdown("**Response (full):**")
                    try:
                        st.json(json.loads(log.get("response_data", "{}")))
                    except:
                        st.write(log.get("response_data", ""))
            else:
                st.info("No logs found.")