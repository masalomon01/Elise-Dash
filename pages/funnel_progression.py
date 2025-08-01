import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data

def render():
    st.header("🔁 Funnel Progression Analysis")
    df = load_data()
    df = df[df["Type"] == "New"].copy()

    with st.sidebar:
        st.subheader("🔍 Filters")
        owners = st.multiselect("Opportunity Owner", df["Opportunity Owner"].dropna().unique())
        segments = st.multiselect("Segment", df["Segment"].dropna().unique())
        sources = st.multiselect("Source", df["Source"].dropna().unique())
        inbound = st.multiselect("Inbound Type", df["Inbound Type"].dropna().unique())
        created_qtrs = st.multiselect("Created Quarter", df["Created Quarter"].dropna().astype(str).unique())
        close_qtrs = st.multiselect("Close Quarter", df["Close Quarter"].dropna().astype(str).unique())
        bands = st.multiselect("Deal Size Band", df["Deal Size Band"].dropna().unique())

    if owners: df = df[df["Opportunity Owner"].isin(owners)]
    if segments: df = df[df["Segment"].isin(segments)]
    if sources: df = df[df["Source"].isin(sources)]
    if inbound: df = df[df["Inbound Type"].isin(inbound)]
    if created_qtrs: df = df[df["Created Quarter"].astype(str).isin(created_qtrs)]
    if close_qtrs: df = df[df["Close Quarter"].astype(str).isin(close_qtrs)]
    if bands: df = df[df["Deal Size Band"].isin(bands)]

    # -------------------------
    # 📊 PG SCORECARD (COUNTS)
    # -------------------------
    st.subheader("📊 PG Scorecard (Heatmap of Stage Counts)")
    stages_pg = {
        "SQL": "SQL Datestamp",
        "SAL": "SAL Datestamp",
        "SQO": "SQO Datestamp",
        "Closed Won": "Close Date"
    }

    pg_data = []
    for stage_name, stage_col in stages_pg.items():
        if stage_name == "Closed Won":
            temp_df = df[df["Funnel Stage Reached"] == "4 - Closed Won"].copy()
        else:
            temp_df = df[df[stage_col].notna()].copy()
        temp_df["Close Quarter"] = temp_df["Close Quarter"].astype(str)
        count_by_qtr = temp_df.groupby("Close Quarter").size().reset_index(name="Count")
        count_by_qtr["Stage"] = stage_name
        pg_data.append(count_by_qtr)

    df_pg = pd.concat(pg_data)
    df_pg["Stage"] = pd.Categorical(df_pg["Stage"], categories=["SQL", "SAL", "SQO", "Closed Won"], ordered=True)
    heatmap_pg = df_pg.pivot(index="Stage", columns="Close Quarter", values="Count").fillna(0)

    fig_pg = px.imshow(
        heatmap_pg,
        text_auto=True,
        color_continuous_scale="blues",
        labels=dict(x="Close Quarter", y="Stage", color="Count"),
        title="PG Scorecard – Stage Counts by Close Quarter"
    )
    st.plotly_chart(fig_pg, use_container_width=True)

    # -------------------------
    # 📈 PG CONVERSION SCORECARD
    # -------------------------
    st.subheader("📈 PG Conversion Rate Scorecard")
    try:
        sql = heatmap_pg.loc["SQL"]
        sal = heatmap_pg.loc["SAL"]
        sqo = heatmap_pg.loc["SQO"]
        won = heatmap_pg.loc["Closed Won"]

        sal_rate = sal / sql
        sqo_rate = sqo / sal
        won_rate = won / sqo

        df_conv = pd.DataFrame({
            "SAL→SQL": sal_rate,
            "SQO→SAL": sqo_rate,
            "Closed Won→SQO": won_rate
        }).T

        fig_conv = px.imshow(
            df_conv,
            text_auto=".1%",
            color_continuous_scale="greens",
            labels=dict(x="Close Quarter", y="Conversion Step", color="Conversion %"),
            title="PG Conversion Rate Scorecard"
        )
        st.plotly_chart(fig_conv, use_container_width=True)
    except Exception as e:
        st.warning(f"Unable to compute conversion rate scorecard: {e}")

    # -------------------------
    # 📊 FUNNEL TOTALS
    # -------------------------
    st.subheader("📊 Funnel Totals (All Opportunities)")
    funnel = {
        "SQL": df["SQL Datestamp"].notna().sum(),
        "SAL": df["SAL Datestamp"].notna().sum(),
        "SQO": df["SQO Datestamp"].notna().sum(),
        "Closed Won": (df["Funnel Stage Reached"] == "4 - Closed Won").sum()
    }
    df_funnel = pd.DataFrame({"Stage": list(funnel.keys()), "Opportunities": list(funnel.values())})
    df_funnel["Conversion Rate"] = df_funnel["Opportunities"].div(df_funnel["Opportunities"].shift(1)).fillna(1).map("{:.1%}".format)
    st.plotly_chart(px.bar(df_funnel, x="Stage", y="Opportunities", text="Opportunities", title="Funnel Stage Totals"))
    st.dataframe(df_funnel)

    # -------------------------
    # 📊 CONVERSION HEATMAPS
    # -------------------------
    stage_pairs = [
        ("SQL Datestamp", "SAL Datestamp", "SQL→SAL"),
        ("SAL Datestamp", "SQO Datestamp", "SAL→SQO"),
        ("SQO Datestamp", "Funnel Stage Reached", "SQO→Closed Won")
    ]

    for group_type, label in [("Created Quarter", "Created"), ("Close Quarter", "Close")]:
        st.subheader(f"📊 Conversion % Heatmap by {label} Quarter")
        data = []

        for from_col, to_col, stage_label in stage_pairs:
            from_df = df[df[from_col].notna()].copy()
            from_df[group_type] = from_df[group_type].astype(str)
            total_from = from_df.groupby(group_type).size()

            if to_col == "Funnel Stage Reached":
                to_df = df[df["Funnel Stage Reached"] == "4 - Closed Won"].copy()
            else:
                to_df = df[df[to_col].notna()].copy()
            to_df[group_type] = to_df[group_type].astype(str)
            total_to = to_df.groupby(group_type).size()

            conversion = (total_to / total_from).replace([float("inf"), -float("inf")], None)
            for qtr, val in conversion.items():
                data.append({"Quarter": qtr, "Stage": stage_label, "Conversion": val})

        if data:
            df_heat = pd.DataFrame(data).pivot(index="Stage", columns="Quarter", values="Conversion")
            fig = px.imshow(
                df_heat,
                text_auto=".1%",
                color_continuous_scale="blues" if label == "Created" else "greens",
                title=f"Conversion % by {label} Quarter",
                labels=dict(x=f"{label} Quarter", y="Stage", color="Conversion %")
            )
            st.plotly_chart(fig, use_container_width=True)
