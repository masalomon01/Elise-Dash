import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data

def render():
    df = load_data()
    st.header("📥 PipeGen Metrics")

    with st.sidebar:
        st.subheader("🔍 Filters")
        owners = st.multiselect("Opportunity Owner", df["Opportunity Owner"].dropna().unique())
        segments = st.multiselect("Segment", df["Segment"].dropna().unique())
        types = st.multiselect("Type", df["Type"].dropna().unique())
        sources = st.multiselect("Source", df["Source"].dropna().unique())
        inbound = st.multiselect("Inbound Type", df["Inbound Type"].dropna().unique())
        created_qtrs = st.multiselect("Created Quarter", df["Created Quarter"].dropna().astype(str).unique())
        close_qtrs = st.multiselect("Close Quarter", df["Close Quarter"].dropna().astype(str).unique())
        bands = st.multiselect("Deal Size Band", df["Deal Size Band"].dropna().unique())
        acv_min, acv_max = float(df["Base Annual Contract Value"].min()), float(df["Base Annual Contract Value"].max())
        acv_range = st.slider("Base Annual Contract Value Range", min_value=acv_min, max_value=acv_max, value=(acv_min, acv_max))

        st.subheader("📊 Breakdown Dimensions")
        options = ["Opportunity Owner", "Segment", "Type", "Source", "Inbound Type", "Deal Size Band"]
        dim1 = st.selectbox("Dimension 1 (X-axis)", ["Created Quarter"])
        dim2 = st.selectbox("Dimension 2 (Color)", [""] + options, index=0)
        dim3 = st.selectbox("Dimension 3 (Facet Row)", [""] + options, index=0)

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

    dimensions = ["Created Quarter"]
    for d in [dim2, dim3]:
        if d and d in df_filtered.columns:
            dimensions.append(d)

    df_grouped = df_filtered.groupby(dimensions).agg(
        Pipeline_Generated_ACV=("Base Annual Contract Value", "sum"),
        Pipeline_Count=("Base Annual Contract Value", "count"),
        Avg_Deal_Size=("Base Annual Contract Value", "mean")
    ).reset_index()

    if "Created Quarter" in df_grouped.columns:
        df_grouped["Created Quarter"] = df_grouped["Created Quarter"].astype(str)

    fig = px.bar(df_grouped,
                 x="Created Quarter",
                 y="Pipeline_Generated_ACV",
                 color=dim2 if dim2 else None,
                 facet_row=dim3 if dim3 else None,
                 barmode="group",
                 title="Pipeline Generated ACV by Created Quarter")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df_grouped)
