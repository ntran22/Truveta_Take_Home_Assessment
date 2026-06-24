import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from streamlit_theme import st_theme

# ============================================================
# Page Config
# ============================================================

st.set_page_config(
    page_title="Cascade Regional Health | Value-Based Care Dashboard",
    layout="wide"
)

# ============================================================
# Theme
# ============================================================

theme = st_theme()

if theme and theme.get("base") == "dark":
    bg_color = "#0E1117"
    text_color = "#FAFAFA"
    sidebar_bg = "#1E1E1E"
    tab_bg = "#262730"
    plot_bg = "#0E1117"
else:
    bg_color = "#FFFFFF"
    text_color = "#000000"
    sidebar_bg = "#F7F9FB"
    tab_bg = "#F7F9FB"
    plot_bg = "#FFFFFF"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}

    h1, h2, h3 {{
        color: #2C2FAB;
    }}

    div[data-testid="stMetricValue"] {{
        color: #00C3B5;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
        border-right: 1px solid #E5E7EB;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: {tab_bg};
        border-radius: 10px 10px 0px 0px;
        padding: 10px 18px;
        color: #2C2FAB;
        font-weight: 600;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: #00C3B5;
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# Title
# ============================================================

st.markdown(
    """
    <h1 style='text-align: center;'>Cascade Regional Health</h1>
    <h3 style='text-align: center; color:#19A4AE;'>Value-Based Care Performance Dashboard</h3>
    <br>
    """,
    unsafe_allow_html=True
)

# ============================================================
# Load Data
# ============================================================

# pt_df = pd.read_csv("data/patient.csv")
# combined_df = pd.read_csv("data/combined_table.csv")

BASE_DIR = Path(__file__).parent

pt_df = pd.read_csv(BASE_DIR / "data" / "patient.csv")
combined_df = pd.read_csv(BASE_DIR / "data" / "combined_table.csv")

# ============================================================
# Data Cleaning
# ============================================================

date_cols = ["StartDate", "EndDate", "BillingDate", "BirthDate", "OnsetDate"]

for col in date_cols:
    if col in combined_df.columns:
        combined_df[col] = pd.to_datetime(combined_df[col], errors="coerce")

pt_df["BirthDate"] = pd.to_datetime(pt_df["BirthDate"], errors="coerce")
combined_df["Amount"] = pd.to_numeric(combined_df["Amount"], errors="coerce").fillna(0)

# Use original EncounterType values directly
combined_df["EncounterCategory"] = (
    combined_df["EncounterType"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
)

# Remove only truly blank encounter types
combined_df = combined_df[
    combined_df["EncounterCategory"].notna()
    & (combined_df["EncounterCategory"].astype(str).str.strip() != "")
].copy()

# Create StartDateYear if missing
if "StartDateYear" not in combined_df.columns:
    combined_df["StartDateYear"] = combined_df["StartDate"].dt.year


# ============================================================
# Sidebar Filters
# ============================================================

st.sidebar.markdown("## Encounter Date Filters")

min_start = combined_df["StartDate"].min().date()
max_start = combined_df["StartDate"].max().date()

start_date_filter = st.sidebar.date_input(
    "Min Start Date",
    value=min_start,
    min_value=min_start,
    max_value=max_start
)

end_date_filter = st.sidebar.date_input(
    "Max Start Date",
    value=max_start,
    min_value=min_start,
    max_value=max_start
)

filtered_df = combined_df[
    (combined_df["StartDate"].dt.date >= start_date_filter) &
    (combined_df["StartDate"].dt.date <= end_date_filter)
].copy()
# EncounterType filter — shows ALL original EncounterType options
st.sidebar.markdown("## Encounter Type Filters")

encounter_type_options = sorted(
    combined_df["EncounterCategory"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

selected_encounter_types = st.sidebar.multiselect(
    "Encounter Type",
    options=encounter_type_options,
    default=encounter_type_options
)

st.markdown("""
<style>

/* Selected multiselect chips */
span[data-baseweb="tag"] {
    background-color: #00C3B5 !important;
    border-color: #00C3B5 !important;
}

/* Chip text */
span[data-baseweb="tag"] span {
    color: white !important;
}

/* X button */
span[data-baseweb="tag"] svg {
    color: white !important;
    fill: white !important;
}

/* Hover state */
span[data-baseweb="tag"]:hover {
    background-color: #00C3B5 !important;
}

</style>
""", unsafe_allow_html=True)


filtered_df = filtered_df[
    filtered_df["EncounterCategory"].isin(selected_encounter_types)
].copy()

filtered_pt_df = pt_df[
    pt_df["PatientId"].isin(filtered_df["PatientId"].unique())
].copy()


# ============================================================
# Helper Metrics
# ============================================================

total_patients = filtered_df["PatientId"].nunique()
total_billed = filtered_df["Amount"].sum()

years_observed = max(filtered_df["StartDateYear"].nunique(), 1)

pmpy = total_billed / total_patients / years_observed if total_patients else 0

# ============================================================
# Sidebar Summary
# ============================================================

st.sidebar.markdown("---")
st.sidebar.metric("Total Patients with at Least 1 Encounter", f"{total_patients:,}")
st.sidebar.metric("Total Billed", f"${total_billed:,.0f}")
st.sidebar.metric("PMPY", f"${pmpy:,.0f}")

# ============================================================
# Tabs
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Executive Overview",
    "Population Health",
    "Cost & Utilization",
    "Care Management Opportunities"
])

st.markdown("""
<style>

/* Active tab underline */
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #2C2FAB !important;
    height: 3px !important;
}

/* Alternative selector for newer Streamlit versions */
button[role="tab"][aria-selected="true"] {
    border-bottom: 3px solid #2C2FAB !important;
}

/* Optional: active tab background */
.stTabs [aria-selected="true"] {
    background-color: #00C3B5 !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# Executive Overview
# ============================================================

with tab1:
    st.header("Executive Overview")

    st.markdown("""
    This section provides a high-level view of the patient population, total billed amount,
    normalized annual spending, and encounter type mix.
    """)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Patients with at Least 1 Encounter", f"{total_patients:,}")
    col2.metric("Total Billed", f"${total_billed:,.0f}")
    col3.metric("PMPY", f"${pmpy:,.0f}")

    st.caption("PMPY = total billed amount divided by unique patients with an encounter and number of observed years.*")

    st.subheader("PMPY by Encounter Type")

    pmpy_encounter = (
        filtered_df.groupby("EncounterCategory",dropna=False)
        .agg(
            TotalBilled=("Amount", "sum"),
            Patients=("PatientId", "nunique")
        )
        .reset_index()
    )

    pmpy_encounter["PMPY"] = (
        pmpy_encounter["TotalBilled"] /
        pmpy_encounter["Patients"] /
        years_observed
    )

    st.dataframe(pmpy_encounter, use_container_width=True)

    fig = px.bar(
        pmpy_encounter,
        x="EncounterCategory",
        y="PMPY",
        text="PMPY",  # <-- add this
        title="PMPY by Encounter Type",
        labels={
            "EncounterCategory": "Encounter Type",
            "PMPY": "PMPY ($)"
        },
        color_discrete_sequence=["#00C3B5"]
    )
    
    fig.update_traces(
        texttemplate='$%{y:,.0f}',
        textposition='outside'
    )
    
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Encounter Type Distribution")

    encounter_distribution = (
        filtered_df.groupby("EncounterCategory", dropna=False)
        .agg(Encounters=("EncounterId", "nunique"))
        .reset_index()
    )

    encounter_distribution["Percent"] = (
        encounter_distribution["Encounters"] /
        encounter_distribution["Encounters"].sum() * 100
    )

    st.dataframe(encounter_distribution, use_container_width=True)

    fig = px.bar(
        encounter_distribution,
        x="EncounterCategory",
        y="Percent",
        text="Percent",
        title="Encounter Type Distribution",
        labels={
            "EncounterCategory": "Encounter Type",
            "Percent": "Percent of Encounters (%)"
        },
        color_discrete_sequence=["#19A4AE"]
    )
    
    fig.update_traces(
        texttemplate='%{y:.1f}%',
        textposition='outside'
    )
    
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    
    st.subheader("PMPY Trend Over Time")
    
    pmpy_trend = (
        filtered_df.groupby("StartDateYearMonth")
        .agg(
            TotalBilled=("Amount", "sum"),
            Patients=("PatientId", "nunique")
        )
        .reset_index()
        .sort_values("StartDateYearMonth")
    )
    
    pmpy_trend["PMPY"] = (
    pmpy_trend["TotalBilled"] /
    pmpy_trend["Patients"]
) * 12
    
    pmpy_trend["PMPY"] = (
        pmpy_trend["TotalBilled"] /
        pmpy_trend["Patients"]
    )
    
    fig = px.line(
        pmpy_trend,
        x="StartDateYearMonth",
        y="PMPY",
        markers=True,
        title="PMPY Trend by Month",
        labels={
            "StartDateYearMonth": "Year-Month",
            "PMPY": "PMPY ($)"
        }
    )
    
    fig.update_traces(
        line_color="#2C2FAB",
        marker_color="#2C2FAB",
        hovertemplate="<b>%{x}</b><br>PMPY: $%{y:,.0f}<extra></extra>"
    )
    
    fig.update_layout(
        height=500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB",
        xaxis_title="Month",
        yaxis_title="PMPY ($)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("\* PMPY values are estimated using patients with at least one recorded encounter during the measurement period. In a production value-based care setting, PMPY would typically be calculated using the total attributed or enrolled population.")

# ============================================================
# Population Health
# ============================================================

with tab2:
    st.header("Population Health")

    st.subheader("Chronic Condition Burden")

    chronic_burden = (
        filtered_df.groupby("PatientId")
        .agg(
            UniqueConditionGroups=("ConditionGroup", "nunique")
        )
        .reset_index()
    )

    avg_condition_burden = chronic_burden["UniqueConditionGroups"].mean()

    col1, col2 = st.columns(2)
    col1.metric("Average Condition Groups per Patient", f"{avg_condition_burden:.2f}")
    col2.metric("Patients with 2+ Condition Groups", f"{(chronic_burden['UniqueConditionGroups'] >= 2).sum():,}")

    chronic_burden_distribution = (
        chronic_burden
        .groupby("UniqueConditionGroups")
        .agg(Patients=("PatientId", "nunique"))
        .reset_index()
        .sort_values("UniqueConditionGroups")
    )

    fig = px.bar(
        chronic_burden_distribution,
        x="UniqueConditionGroups",
        y="Patients",
        text="Patients",
        title="Distribution of Chronic Condition Burden",
        labels={
            "UniqueConditionGroups": "Number of Unique Condition Groups",
            "Patients": "Number of Patients"
        },
        color_discrete_sequence=["#00C3B5"]
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        height=500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB",
        xaxis=dict(dtick=1),
        yaxis_range=[
            0,
            chronic_burden_distribution["Patients"].max() * 1.15
        ],
        uniformtext_minsize=10,
        uniformtext_mode="hide"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Filter out "No diagnosis recorded" for this tab only
    population_health_df = filtered_df[
        filtered_df["ConditionGroup"].fillna("").str.strip() != "No diagnosis recorded"
    ].copy()

    st.subheader("Top Diagnosis Groups")

    top_diagnosis = (
        population_health_df.groupby(["CodeGrouper", "ConditionGroup"], dropna=False)
        .agg(
            Patients=("PatientId", "nunique"),
            Encounters=("EncounterId", "nunique")
        )
        .reset_index()
        .sort_values("Patients", ascending=False)
    )

    st.dataframe(top_diagnosis, use_container_width=True)

    st.subheader("Condition Prevalence")

    condition_prevalence = (
        population_health_df.groupby("ConditionGroup", dropna=False)
        .agg(Patients=("PatientId", "nunique"))
        .reset_index()
        .sort_values("Patients", ascending=False)
    )

    condition_prevalence["PrevalencePercent"] = (
        condition_prevalence["Patients"] / total_patients * 100
        if total_patients else 0
    )

    condition_prevalence["PrevalenceLabel"] = (
        condition_prevalence["PrevalencePercent"].round(1).astype(str) + "%"
    )

    st.dataframe(condition_prevalence, use_container_width=True)

    fig = px.bar(
        condition_prevalence,
        x="ConditionGroup",
        y="PrevalencePercent",
        text="PrevalenceLabel",
        title="Condition Prevalence by Condition Group",
        labels={
            "ConditionGroup": "Condition Group",
            "PrevalencePercent": "Patient Prevalence (%)"
        },
        color_discrete_sequence=["#00C3B5"]
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        height=550,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB",
        xaxis_tickangle=-45,
        yaxis_range=[
            0,
            condition_prevalence["PrevalencePercent"].max() * 1.15
        ],
        uniformtext_minsize=10,
        uniformtext_mode="hide"
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Cost & Utilization
# ============================================================

with tab3:
    st.header("Cost & Utilization")

    st.subheader("PMPY by Condition Group")

    pmpy_condition = (
        filtered_df.groupby("ConditionGroup", dropna=False)
        .agg(
            TotalBilled=("Amount", "sum"),
            Patients=("PatientId", "nunique")
        )
        .reset_index()
        .sort_values("TotalBilled", ascending=False)
    )

    pmpy_condition["PMPY"] = (
        pmpy_condition["TotalBilled"] /
        pmpy_condition["Patients"] /
        years_observed
    )

    st.dataframe(pmpy_condition, use_container_width=True)

    fig = px.bar(
        pmpy_condition,
        x="ConditionGroup",
        y="PMPY",
        text="PMPY",
        title="PMPY by Condition Group",
        labels={
            "ConditionGroup": "Condition Group",
            "PMPY": "PMPY ($)"
        },
        color_discrete_sequence=["#00C3B5"]
    )
    
    fig.update_traces(
        texttemplate='$%{y:,.0f}',
        textposition='outside'
    )
    
    fig.update_layout(
        height=550,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB",
        xaxis_tickangle=-45,
        yaxis_range=[
            0,
            pmpy_condition["PMPY"].max() * 1.15
        ]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("PMPY by Census Region")

    pmpy_region = (
        filtered_df.groupby("CensusRegion", dropna=False)
        .agg(
            TotalBilled=("Amount", "sum"),
            Patients=("PatientId", "nunique")
        )
        .reset_index()
        .sort_values("TotalBilled", ascending=False)
    )

    pmpy_region["PMPY"] = (
        pmpy_region["TotalBilled"] /
        pmpy_region["Patients"] /
        years_observed
    )

    st.dataframe(pmpy_region, use_container_width=True)

    fig = px.bar(
        pmpy_region,
        x="CensusRegion",
        y="PMPY",
        text="PMPY",
        title="PMPY by Census Region",
        labels={
            "CensusRegion": "Census Region",
            "PMPY": "PMPY ($)"
        },
        color_discrete_sequence=["#19A4AE"]
    )
    
    fig.update_traces(
        texttemplate='$%{y:,.0f}',
        textposition='outside'
    )
    
    fig.update_layout(
        height=550,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB",
        yaxis_range=[
            0,
            pmpy_region["PMPY"].max() * 1.15
        ]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Monthly Billing Trends")

    st.markdown("""
    This chart displays billed amounts by encounter start month.
    
    To maintain consistency across the dashboard, the trend is filtered using the selected
    **Encounter Start Date** range rather than billing date. As a result, billed amounts are
    attributed to the month in which the encounter occurred, allowing all metrics and visualizations
    to align to the same measurement period.
    """)
    
    monthly_billing = (
        filtered_df.groupby("StartDateYearMonth", dropna=False)
        .agg(
            TotalBilled=("Amount", "sum")
        )
        .reset_index()
        .sort_values("StartDateYearMonth")
    )
    
    fig = px.line(
        monthly_billing,
        x="StartDateYearMonth",
        y="TotalBilled",
        markers=True,
        title="Monthly Billing Trends by Encounter Start Month",
        labels={
            "StartDateYearMonth": "Encounter Start Month",
            "TotalBilled": "Total Billed ($)"
        }
    )
    
    fig.update_traces(
        line_color="#2C2FAB",
        marker_color="#2C2FAB",
        hovertemplate="<b>%{x}</b><br>Total Billed: $%{y:,.0f}<extra></extra>"
    )
    
    fig.update_layout(
        height=500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB",
        xaxis_title="Encounter Start Month",
        yaxis_title="Total Billed ($)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Inpatient vs Outpatient Utilization")

    st.markdown("""
    This visualization summarizes utilization across encounter settings.
    
    **Encounter Percent** is calculated as:
    
    **Encounter Type Encounters ÷ Total Encounters × 100**
    
    This metric represents the proportion of all encounters attributed to each encounter type
    within the selected date range and encounter filters.
    """)
    
    utilization = (
        filtered_df.groupby("EncounterCategory", dropna=False)
        .agg(
            Encounters=("EncounterId", "nunique"),
            Patients=("PatientId", "nunique"),
            TotalBilled=("Amount", "sum")
        )
        .reset_index()
    )
    
    utilization["EncounterPercent"] = (
        utilization["Encounters"] /
        utilization["Encounters"].sum() * 100
    )
    
    st.dataframe(utilization, use_container_width=True)
    
    fig = px.bar(
        utilization,
        x="EncounterCategory",
        y="Encounters",
        text="Encounters",
        title="Inpatient vs Outpatient Utilization",
        labels={
            "EncounterCategory": "Encounter Type",
            "Encounters": "Number of Encounters"
        },
        color_discrete_sequence=["#00C3B5"]
    )
    
    fig.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Encounters: %{y:,.0f}<br>"
            "Percent of Encounters: %{customdata[0]:.1f}%<extra></extra>"
        ),
        customdata=utilization[["EncounterPercent"]]
    )
    
    fig.update_layout(
        height=550,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color="#2C2FAB",
        yaxis_range=[
            0,
            utilization["Encounters"].max() * 1.15
        ]
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(
        "Encounter Percent = Number of encounters for an encounter type divided by total encounters within the filtered population."
    )

# ============================================================
# Care Management Opportunities
# ============================================================

with tab4:
    st.header("Care Management Opportunities")

    st.markdown("""
    This section identifies patients who may benefit from targeted care management interventions and serves as a **proxy for identifying potential care gaps and high-risk populations commonly addressed through HEDIS and value-based care programs**.\*

    **High-Cost Patients**
    
    * Patients whose total billed amounts are at or above the 90th percentile of the filtered patient population.
    * These patients may represent individuals with complex medical needs, multiple chronic conditions, or frequent healthcare utilization.
    
    **Super Utilizers**
    
    * Patients whose encounter volume is at or above the 90th percentile of the filtered patient population.
    * Frequent utilization may indicate unmet care needs, fragmented care coordination, or opportunities for proactive intervention.
    
    **High-Cost & Super Utilizer Overlap**
    
    * Patients who meet both criteria: high total billed amounts and high encounter utilization.
    * These patients often represent a disproportionately high share of healthcare resource use and may benefit from intensive care management, care coordination, and chronic disease support programs.
    """)

    patient_summary = (
        filtered_df.groupby("PatientId")
        .agg(
            TotalBilled=("Amount", "sum"),
            Encounters=("EncounterId", "nunique"),
            ConditionGroups=("ConditionGroup", "nunique")
        )
        .reset_index()
    )

    high_cost_threshold = patient_summary["TotalBilled"].quantile(0.90)
    super_utilizer_threshold = patient_summary["Encounters"].quantile(0.90)

    patient_summary["HighCostPatient"] = patient_summary["TotalBilled"] >= high_cost_threshold
    patient_summary["SuperUtilizer"] = patient_summary["Encounters"] >= super_utilizer_threshold
    patient_summary["HighCostAndSuperUtilizer"] = (
        patient_summary["HighCostPatient"] &
        patient_summary["SuperUtilizer"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("High-Cost Patients", f"{patient_summary['HighCostPatient'].sum():,}")
    col2.metric("Super Utilizers", f"{patient_summary['SuperUtilizer'].sum():,}")
    col3.metric(
        "High-Cost & Super Utilizer Overlap",
        f"{patient_summary['HighCostAndSuperUtilizer'].sum():,}"
    )

    st.caption(
        f"Current thresholds: \n- High-cost patients ≥ ${high_cost_threshold:,.0f} \n- Super utilizers ≥ {super_utilizer_threshold:.0f} encounters."
    )
    
    
    # Overall Patient Population Pie Chart
    patient_summary["CareManagementSegment"] = np.select(
        [
            patient_summary["HighCostAndSuperUtilizer"],
            patient_summary["SuperUtilizer"] & ~patient_summary["HighCostPatient"],
            patient_summary["HighCostPatient"] & ~patient_summary["SuperUtilizer"]
        ],
        [
            "High-Cost & Super Utilizer Overlap",
            "Super Utilizers Only",
            "High-Cost Patients Only"
        ],
        default="All Other Patients"
    )

    population_pie = (
        patient_summary
        .groupby("CareManagementSegment", dropna=False)
        .agg(Patients=("PatientId", "nunique"))
        .reset_index()
    )

    st.subheader("Overall Patient Population by Care Management Segment")

    fig = px.pie(
        population_pie,
        names="CareManagementSegment",
        values="Patients",
        title="Overall Encounter Patient Population: High-Cost and Super Utilizer Segments",
        color="CareManagementSegment",
        color_discrete_map={
            "High-Cost & Super Utilizer Overlap": "#2C2FAB",
            "Super Utilizers Only": "#00C3B5",
            "High-Cost Patients Only": "#19A4AE",
            "All Other Patients": "#D9DEE8"
        },
        hole=0.35
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Patients: %{value:,}<br>Percent: %{percent}<extra></extra>"
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=600,
        title_font_color="#2C2FAB",
        legend_title_text="Patient Segment"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(population_pie, use_container_width=True)
    

    st.subheader("High-Cost Patients")

    high_cost_patients = patient_summary[
        patient_summary["HighCostPatient"]
    ].sort_values("TotalBilled", ascending=False)

    st.dataframe(high_cost_patients, use_container_width=True)

    st.subheader("Super Utilizers")

    super_utilizers = patient_summary[
        patient_summary["SuperUtilizer"]
    ].sort_values("Encounters", ascending=False)

    st.dataframe(super_utilizers, use_container_width=True)

    st.subheader("High-Cost & Super Utilizer Overlap")

    overlap = patient_summary[
        patient_summary["HighCostAndSuperUtilizer"]
    ].sort_values(["TotalBilled", "Encounters"], ascending=False)

    st.dataframe(overlap, use_container_width=True)
    
    st.caption("""
    **\*Important Note**
    \n• These measures are intended as proxy indicators of potential care gaps and population health opportunities and are not official HEDIS measures.
    \n• Calculating formal HEDIS care gap metrics would require additional data elements not available in this dataset, such as member enrollment, payer attribution, laboratory results, pharmacy claims, and quality measure specifications.
    """)
