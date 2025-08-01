import streamlit as st
import pandas as pd
from data_loader import load_data

def render():
    st.header("🧑‍💼 Rep Scorecards")

    df = load_data()
    df = df[df["Opportunity Owner"].notna()].copy()

    df["Created Qtr"] = df["Created Date"].dt.to_period("Q").astype(str)
    df["Closed Qtr"] = df["Close Date"].dt.to_period("Q").astype(str)
    df["Reference Quarter"] = df["Created Qtr"].combine_first(df["Closed Qtr"])

    with st.sidebar:
        st.subheader("Filters")
        segments = st.multiselect("Segment", df["Segment"].dropna().unique())
        sources = st.multiselect("Source", df["Source"].dropna().unique())
        ref_qtrs = st.multiselect("Reference Quarter (Bookings)", df["Reference Quarter"].dropna().unique())
        created_qtrs = st.multiselect("Created Quarter (Pipeline)", df["Created Qtr"].dropna().unique())

    # Filter for Bookings
    df_bookings = df.copy()
    if segments: df_bookings = df_bookings[df_bookings["Segment"].isin(segments)]
    if sources: df_bookings = df_bookings[df_bookings["Source"].isin(sources)]
    if ref_qtrs: df_bookings = df_bookings[df_bookings["Reference Quarter"].isin(ref_qtrs)]

    # Filter for Pipeline
    df_pipeline = df.copy()
    if segments: df_pipeline = df_pipeline[df_pipeline["Segment"].isin(segments)]
    if sources: df_pipeline = df_pipeline[df_pipeline["Source"].isin(sources)]
    if created_qtrs: df_pipeline = df_pipeline[df_pipeline["Created Qtr"].isin(created_qtrs)]

    # Bookings & Win Rate
    grouped_all = df_bookings.groupby(["Opportunity Owner", "Segment"]).agg(
        Bookings_ACV=("Base Annual Contract Value", lambda x: x[df_bookings.loc[x.index, "Is_Won"]].sum()),
        Win_Count=("Is_Won", "sum"),
        Total_Count=("Is_Won", "count"),
        Win_Rate=("Is_Won", lambda x: x.sum() / x.count() if x.count() > 0 else 0),
        Avg_Deal_Size=("Base Annual Contract Value", lambda x: x[df_bookings.loc[x.index, "Is_Won"]].mean()),
        Deal_Velocity=("Deal Velocity (Days)", "mean")
    )

    # Pipeline metrics from Created Quarter filter
    grouped_pipe = df_pipeline.groupby(["Opportunity Owner", "Segment"]).agg(
        Total_Pipeline_Generated=("Created Date", "count"),
        Pipeline_Generated_ACV=("Base Annual Contract Value", "sum"),
        AE_Outbound_Pipeline_ACV=("Base Annual Contract Value", lambda x: x[df_pipeline.loc[x.index, "Source"] == "AE Outbound"].sum()),
        SDR_Outbound_Pipeline_ACV=("Base Annual Contract Value", lambda x: x[df_pipeline.loc[x.index, "Source"] == "SDR Outbound"].sum()),
        Marketing_Pipeline_ACV=("Base Annual Contract Value", lambda x: x[df_pipeline.loc[x.index, "Source"].str.contains("Marketing", na=False)].sum())
    )

    grouped = grouped_all.join(grouped_pipe, how="outer").reset_index()
    grouped.fillna(0, inplace=True)

    # Format columns
    grouped["Win Rate"] = (grouped["Win_Rate"] * 100).round(1)
    grouped["Bookings_ACV"] = grouped["Bookings_ACV"].round(0)
    grouped["Avg_Deal_Size"] = grouped["Avg_Deal_Size"].round(0)
    grouped["Pipeline_Generated_ACV"] = grouped["Pipeline_Generated_ACV"].round(0)
    grouped["Deal_Velocity"] = grouped["Deal_Velocity"].round(0).astype("Int64")
    grouped["AE_Outbound_Pipeline_ACV"] = grouped["AE_Outbound_Pipeline_ACV"].round(0)
    grouped["SDR_Outbound_Pipeline_ACV"] = grouped["SDR_Outbound_Pipeline_ACV"].round(0)
    grouped["Marketing_Pipeline_ACV"] = grouped["Marketing_Pipeline_ACV"].round(0)

    # -------------------------------
    # Simplified Scorecard + Styling
    # -------------------------------
    st.subheader("📊 Simplified Rep Scorecard")
    simplified = grouped[[
        "Opportunity Owner", "Segment", "Bookings_ACV", "Win Rate",
        "Total_Pipeline_Generated", "Pipeline_Generated_ACV"
    ]].copy()

    def style_pipeline(val):
        if val < 50000:
            return "background-color: lightcoral"
        elif val > 150000:
            return "background-color: lightgreen"
        else:
            return "background-color: khaki"

    def style_bookings(val):
        if val < 25000:
            return "background-color: lightcoral"
        elif val > 75000:
            return "background-color: lightgreen"
        else:
            return "background-color: khaki"

    def style_winrate(val):
        if val < 30:
            return "background-color: lightcoral"
        elif val > 50:
            return "background-color: lightgreen"
        return ""

    styled = simplified.style.format({
        "Bookings_ACV": "${:,.0f}",
        "Win Rate": "{:.1f}%",
        "Pipeline_Generated_ACV": "${:,.0f}"
    }).applymap(style_bookings, subset=["Bookings_ACV"]) \
      .applymap(style_pipeline, subset=["Pipeline_Generated_ACV"]) \
      .applymap(style_winrate, subset=["Win Rate"])

    st.dataframe(styled, use_container_width=True)

    # ------------------------
    # Detailed View
    # ------------------------
    st.subheader("📋 Detailed Scorecard")
    st.dataframe(grouped.style.format({
        "Bookings_ACV": "${:,.0f}",
        "Win Rate": "{:.1f}%",
        "Avg_Deal_Size": "${:,.0f}",
        "Pipeline_Generated_ACV": "${:,.0f}",
        "AE_Outbound_Pipeline_ACV": "${:,.0f}",
        "SDR_Outbound_Pipeline_ACV": "${:,.0f}",
        "Marketing_Pipeline_ACV": "${:,.0f}"
    }), use_container_width=True)
