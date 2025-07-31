import streamlit as st
from pages import revenue_metrics

st.set_page_config(layout="wide")
st.title("📊 EliseAI GTM Dashboard")

tab = st.sidebar.radio("Select Tab", ["Revenue Metrics"])

if tab == "Revenue Metrics":
    revenue_metrics.render()
