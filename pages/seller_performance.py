import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data

def render():
    st.header("📈 Seller Performance (vs Segment Peers)")
    df = load_data()

    df["Reference Quarter"] = df["Created Quarter"].combine_first(df["Close Quarter"]).astype(str)
    df["Created Quarter"] = df["Created Quarter"].astype(str)
    df["Close Quarter"] = df["Close Quarter"].astype(str)

    with st.sidebar:
        st.subheader("Filters")
        owners = st.multiselect("Opportunity Owner", df["Opportunity Owner"].dropna().unique())
        segments = st.multiselect("Segment", df["Segment"].dropna().unique())
        sources = st.multiselect("Source", df["Source"].dropna().unique())
        ref_qtrs = st.multiselect("Reference Quarter", df["Reference Quarter"].dropna().unique())

    if owners: df = df[df["Opportunity Owner"].isin(owners)]
    if segments: df = df[df["Segment"].isin(segments)]
    if sources: df = df[df["Source"].isin(sources)]
    if ref_qtrs: df = df[df["Reference Quarter"].isin(ref_qtrs)]

    df["Bookings_ACV"] = df.apply(lambda x: x["Base Annual Contract Value"] if x["Is_Won"] else 0, axis=1)
    df["Pipeline_ACV"] = df["Base Annual Contract Value"]

    grouped = df.groupby(["Segment", "Opportunity Owner", "Reference Quarter"]).agg(
        Bookings_ACV=("Bookings_ACV", "sum"),
        Pipeline_ACV=("Pipeline_ACV", "sum"),
        Avg_Deal_Size=("Base Annual Contract Value", "mean")
    ).reset_index()

    # Segment baselines per quarter
    seg_qtr_avg = grouped.groupby(["Segment", "Reference Quarter"])[["Bookings_ACV", "Pipeline_ACV"]].mean().reset_index()
    seg_qtr_avg.rename(columns={"Bookings_ACV": "Bookings_Baseline", "Pipeline_ACV": "Pipeline_Baseline"}, inplace=True)

    merged = pd.merge(grouped, seg_qtr_avg, on=["Segment", "Reference Quarter"], how="left")

    for metric, baseline in [("Bookings_ACV", "Bookings_Baseline"), ("Pipeline_ACV", "Pipeline_Baseline")]:
        merged[f"{metric}_Delta"] = ((merged[metric] - merged[baseline]) / merged[baseline]).round(2)

    # Heatmaps (flipped, red→green)
    for metric in ["Bookings_ACV_Delta", "Pipeline_ACV_Delta"]:
        heat = merged.pivot(index="Reference Quarter", columns="Opportunity Owner", values=metric)
        fig = px.imshow(
            heat,
            text_auto=".1%",
            color_continuous_scale="RdYlGn",
            origin="lower",
            height=700,
            title=f"{metric.replace('_Delta','')} % Delta vs Segment Avg",
            labels=dict(x="Seller", y="Quarter", color="% Δ vs Segment Avg")
        )
        st.plotly_chart(fig, use_container_width=True)

    # Trend charts by seller
    for metric in ["Bookings_ACV", "Pipeline_ACV"]:
        st.subheader(f"{metric} over Time (Colored by Seller)")
        fig = px.bar(
            merged,
            x="Reference Quarter", y=metric,
            color="Opportunity Owner",
            barmode="group",
            title=f"{metric} per Seller per Quarter"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Scatter Plot: one dot per seller
    st.subheader("🔍 Bookings vs Pipeline (1 Bubble per Seller)")
    agg = merged.groupby("Opportunity Owner").agg(
        Bookings_ACV=("Bookings_ACV", "sum"),
        Pipeline_ACV=("Pipeline_ACV", "sum"),
        Avg_Deal_Size=("Avg_Deal_Size", "mean")
    ).reset_index()

    fig = px.scatter(
        agg,
        x="Pipeline_ACV",
        y="Bookings_ACV",
        size="Avg_Deal_Size",
        color="Opportunity Owner",
        title="Bookings vs Pipeline (Bubble = Avg Deal Size)",
        labels=dict(Pipeline_ACV="Pipeline ACV", Bookings_ACV="Bookings ACV")
    )
    st.plotly_chart(fig, use_container_width=True)
