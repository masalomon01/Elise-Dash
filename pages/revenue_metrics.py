import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data

def render():
    df = load_data()

    st.header("📈 Revenue Metrics")

    # Filters
    with st.sidebar:
        st.subheader("🔍 Filters")
        owners = st.multiselect("Opportunity Owner", df["Opportunity Owner"].unique())
        segments = st.multiselect("Segment", df["Segment"].unique())
        types = st.multiselect("Type", df["Type"].unique())
        sources = st.multiselect("Source", df["Source"].unique())
        inbound = st.multiselect("Inbound Type", df["Inbound Type"].unique())
        created_qtrs = st.multiselect("Created Quarter", df["Created Quarter"].astype(str).unique())
        close_qtrs = st.multiselect("Close Quarter", df["Close Quarter"].astype(str).unique())
        bands = st.multiselect("Deal Size Band", df["Deal Size Band"].dropna().unique())
        acv_min, acv_max = float(df["Base Annual Contract Value"].min()), float(df["Base Annual Contract Value"].max())
        acv_range = st.slider("Base Annual Contract Value Range", min_value=acv_min, max_value=acv_max, value=(acv_min, acv_max))

        st.subheader("📊 Breakdown Dimensions")
        dim1 = st.selectbox("Dimension 1 (optional)", [""] + df.columns.tolist(), index=0)
        dim2 = st.selectbox("Dimension 2 (optional)", [""] + df.columns.tolist(), index=0)
        dim3 = st.selectbox("Dimension 3 (optional)", [""] + df.columns.tolist(), index=0)

    # Apply filters
    df_filtered = df.copy()
    if owners: df_filtered = df_filtered[df_filtered["Opportunity Owner"].isin(owners)]
    if segments: df_filtered = df_filtered[df_filtered["Segment"].isin(segments)]
    if types: df_filtered = df_filtered[df_filtered["Type"].isin(types)]
    if sources: df_filtered = df_filtered[df_filtered["Source"].isin(sources)]
    if inbound: df_filtered = df_filtered[df_filtered["Inbound Type"].isin(inbound)]
    if created_qtrs: df_filtered = df_filtered[df_filtered["Created Quarter"].astype(str).isin(created_qtrs)]
    if close_qtrs: df_filtered = df_filtered[df_filtered["Close Quarter"].astype(str).isin(close_qtrs)]
    if bands: df_filtered = df_filtered[df_filtered["Deal Size Band"].isin(bands)]
    df_filtered = df_filtered[df_filtered["Base Annual Contract Value"].between(*acv_range)]

    # Grouping keys
    dimensions = ["Close Quarter"]
    for d in [dim1, dim2, dim3]:
        if d and d in df.columns:
            dimensions.append(d)

    # Aggregate metrics
    df_grouped = df_filtered.groupby(dimensions).agg(
        Bookings_ACV=pd.NamedAgg(column="Base Annual Contract Value", aggfunc=lambda x: x[df_filtered.loc[x.index, "Is_Won"]].sum()),
        Total_ACV=pd.NamedAgg(column="Base Annual Contract Value", aggfunc="sum"),
        Win_Count=pd.NamedAgg(column="Is_Won", aggfunc="sum"),
        Total_Count=pd.NamedAgg(column="Is_Won", aggfunc="count"),
        Avg_Deal_Size=pd.NamedAgg(column="Base Annual Contract Value", aggfunc=lambda x: x[df_filtered.loc[x.index, "Is_Won"]].mean()),
        Avg_Sales_Cycle=pd.NamedAgg(column="Close Date", aggfunc=lambda x: (df_filtered.loc[x.index, "Close Date"] - df_filtered.loc[x.index, "Created Date"]).dt.days.mean()),
        Deal_Velocity=pd.NamedAgg(column="Deal Velocity (Days)", aggfunc="mean")
    ).reset_index()

    df_grouped["Win Rate (ACV)"] = (df_grouped["Bookings_ACV"] / df_grouped["Total_ACV"]).fillna(0)
    df_grouped["Win Rate (Count)"] = (df_grouped["Win_Count"] / df_grouped["Total_Count"]).fillna(0)

    # Bar chart
    if "Close Quarter" in df_grouped:
        fig = px.bar(df_grouped, x="Close Quarter", y="Bookings_ACV", color=dim1 if dim1 else None,
                     barmode="group", title="Bookings ACV by Close Quarter")
        st.plotly_chart(fig, use_container_width=True)

    # Table
    st.dataframe(df_grouped)
