import streamlit as st
from pages import revenue_metrics, funnel_progression, rep_scorecards, pipegen_metrics, seller_performance

st.set_page_config(layout="wide")
st.title("📊 EliseAI GTM Dashboard")

tab = st.sidebar.radio("Select Tab", ["Revenue Metrics", "Funnel Progression", "Rep Scorecards", "Pipegen Metrics", "Seller Performance"])

if tab == "Revenue Metrics":
    revenue_metrics.render()
elif tab == "Funnel Progression":
    funnel_progression.render()
elif tab == "Rep Scorecards":
    rep_scorecards.render()
elif tab == "Pipegen Metrics":
    pipegen_metrics.render()
elif tab == "Seller Performance":
    seller_performance.render()
