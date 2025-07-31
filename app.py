import streamlit as st

st.set_page_config(page_title="EliseAI Dashboard Test", layout="wide")

st.title("👋 Hello, EliseAI!")
st.subheader("Welcome to your first Streamlit dashboard.")
st.write("If you're seeing this, your deployment is working!")

# Add a basic chart
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "Quarter": ["2023 Q1", "2023 Q2", "2023 Q3", "2023 Q4"],
    "Bookings ($K)": np.random.randint(100, 500, size=4)
})

st.bar_chart(df.set_index("Quarter"))