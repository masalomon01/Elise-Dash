import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data

def render():
    df = load_data()
    st.header("📈 Revenue Metrics")

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

        st.subheader("📊 Dimensions")
        options = ["Close Quarter", "Opportunity Owner", "Segment", "Type", "Source", "Inbound Type", "Deal Size Band"]
        dim1 = st.selectbox("X-Axis (default: Close Quarter)", options, index=0)
        dim2 = st.selectbox("Color Grouping", [""] + options, index=0)
        dim3 = st.selectbox("Facet Row (Optional)", [""] + options, index=0)

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

    dimensions = [dim for dim in [dim1, dim2, dim3] if dim and dim in df_filtered.columns]

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

    for col in df_grouped.columns:
        if pd.api.types.is_period_dtype(df_grouped[col]):
            df_grouped[col] = df_grouped[col].astype(str)

    chart_list = [
        ("Bookings_ACV", "Bookings ACV"),
        ("Win Rate (ACV)", "Win Rate (ACV)"),
        ("Avg_Deal_Size", "Average Deal Size"),
        ("Deal_Velocity", "Average Deal Velocity (Days)"),
        ("Win_Count", "Count of Wins"),
        ("Total_ACV", "Total ACV (Won + Lost)"),
        ("Total_Count", "Total Opportunity Count")
    ]

    for y_col, title in chart_list:
        fig = px.bar(
            df_grouped,
            x=dim1,
            y=y_col,
            color=dim2 if dim2 else None,
            facet_row=dim3 if dim3 else None,
            barmode="group",
            title=f"{title} by {dim1}" + (f" colored by {dim2}" if dim2 else "")
        )
        st.plotly_chart(fig, use_container_width=True)

    df_formatted = df_grouped.copy()
    if "Bookings_ACV" in df_formatted:
        df_formatted["Bookings_ACV"] = (df_formatted["Bookings_ACV"] / 1000).round(0).map("${:,.0f}K".format)
    if "Total_ACV" in df_formatted:
        df_formatted["Total_ACV"] = (df_formatted["Total_ACV"] / 1000).round(0).map("${:,.0f}K".format)
    if "Avg_Deal_Size" in df_formatted:
        df_formatted["Avg_Deal_Size"] = df_formatted["Avg_Deal_Size"].round(0).map("${:,.0f}".format)
    if "Avg_Sales_Cycle" in df_formatted:
        df_formatted["Avg_Sales_Cycle"] = df_formatted["Avg_Sales_Cycle"].round(0).astype("Int64")
    if "Deal_Velocity" in df_formatted:
        df_formatted["Deal_Velocity"] = df_formatted["Deal_Velocity"].round(0).astype("Int64")
    if "Win Rate (ACV)" in df_formatted:
        df_formatted["Win Rate (ACV)"] = (df_grouped["Win Rate (ACV)"] * 100).round(1).map("{:.1f}%".format)
    if "Win Rate (Count)" in df_formatted:
        df_formatted["Win Rate (Count)"] = (df_grouped["Win Rate (Count)"] * 100).round(1).map("{:.1f}%".format)

    st.dataframe(df_formatted)
