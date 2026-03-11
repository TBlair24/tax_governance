import streamlit as st
import pandas as pd
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title = "URA Data Governance Dashboard",
    page_icon  = "🏛️",
    layout     = "wide",
)


@st.cache_data
def load_summary():
    path = "outputs/pipeline_summary.json"
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

@st.cache_data
def load_raw():
    return pd.read_csv("data/raw/tax_returns.csv")

@st.cache_data
def load_clean():
    return pd.read_csv("data/processed/tax_returns_clean.csv")

st.sidebar.title("🏛️ URA Data Governance")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate", [
    "📊 Overview",
    "🔍 Issue Explorer",
    "📈 Dimension Scores",
    "🧹 Before vs After",
    "🔗 Lineage",
])

summary = load_summary()

if summary is None:
    st.error("No pipeline results found. Run `python src/pipeline.py` first.")
    st.stop()

dq     = summary["dq_results"]
issues = pd.DataFrame(dq["issues"])
clean  = summary["cleaning_summary"]

if page == "📊 Overview":
    st.title("📊 Data Quality Overview")
    st.caption(f"Last pipeline run: {summary['pipeline_run']}")
    st.markdown("---")

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)

    score = dq["overall_dq_score"]
    col1.metric("Overall DQ Score",  f"{score}%")
    col2.metric("Total Issues",       dq["total_issues"])
    col3.metric("HIGH Severity",      dq["severity_summary"]["HIGH"])
    col4.metric("Rows Retained",      f"{clean['retention_pct']}%")

    st.markdown("---")
    st.subheader("Quality Dimension Scores")

    dim_df = pd.DataFrame({
        "Dimension": list(dq["dimension_scores"].keys()),
        "Score":     list(dq["dimension_scores"].values()),
    })

    # Colour each bar based on score
    def bar_color(score):
        if score >= 95: return "🟢"
        if score >= 80: return "🟡"
        return "🔴"

    for _, row in dim_df.iterrows():
        icon = bar_color(row["Score"])
        col_a, col_b, col_c = st.columns([3, 6, 1])
        col_a.markdown(f"**{row['Dimension']}**")
        col_b.progress(row["Score"] / 100)
        col_c.markdown(f"{icon} {row['Score']}%")

    st.markdown("---")
    st.subheader("Issues by Severity")

    sev = dq["severity_summary"]
    c1, c2, c3 = st.columns(3)

    c1.error(f"🔴 HIGH — {sev['HIGH']} issues")
    c2.warning(f"🟡 MEDIUM — {sev['MEDIUM']} issues")
    c3.success(f"🟢 LOW — {sev['LOW']} issues")

elif page == "🔍 Issue Explorer":
    st.title("🔍 Issue Explorer")
    st.markdown("---")

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        dim_filter = st.multiselect(
            "Filter by Dimension",
            options = issues["dimension"].unique().tolist(),
            default = issues["dimension"].unique().tolist(),
        )
    with col2:
        sev_filter = st.multiselect(
            "Filter by Severity",
            options = ["HIGH", "MEDIUM", "LOW"],
            default = ["HIGH", "MEDIUM", "LOW"],
        )

    filtered = issues[
        issues["dimension"].isin(dim_filter) &
        issues["severity"].isin(sev_filter)
    ].copy()

    st.markdown(f"**Showing {len(filtered)} of {len(issues)} issues**")
    st.markdown("---")

    if filtered.empty:
        st.success("No issues match your current filters.")
    else:
        for _, row in filtered.iterrows():
            # Color the severity label
            if row["severity"] == "HIGH":
                sev_display = "🔴 HIGH"
            elif row["severity"] == "MEDIUM":
                sev_display = "🟡 MEDIUM"
            else:
                sev_display = "🟢 LOW"

            with st.expander(f"{sev_display}  |  {row['dimension']}  |  {row['field']}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Affected Rows", f"{row['affected_rows']:,}")
                c2.metric("Total Rows",    f"{row['total_rows']:,}")
                c3.metric("Pass Rate",     f"{row['pass_rate']}%")
                st.markdown(f"**Issue:** {row['description']}")

elif page == "📈 Dimension Scores":
    st.title("📈 Dimension Scores")
    st.markdown("---")

    descriptions = {
        "Completeness":        "Required fields must not be null or empty.",
        "Validity":            "Values must conform to permitted formats and ranges.",
        "Consistency":         "Related fields must be logically coherent with each other.",
        "Uniqueness":          "No duplicate records on primary key fields.",
        "Timeliness":          "Dates must fall within acceptable windows.",
        "Referential Integrity": "Foreign keys must point to existing records.",
    }

    for dim, score in dq["dimension_scores"].items():
        st.markdown(f"### {dim}")
        st.markdown(f"*{descriptions[dim]}*")

        col1, col2 = st.columns([4, 1])
        with col1:
            st.progress(score / 100)
        with col2:
            if score >= 95:
                st.success(f"{score}%")
            elif score >= 80:
                st.warning(f"{score}%")
            else:
                st.error(f"{score}%")

        # Show issues for this dimension
        dim_issues = issues[issues["dimension"] == dim]
        if dim_issues.empty:
            st.caption("✅ No issues detected in this dimension.")
        else:
            for _, row in dim_issues.iterrows():
                st.caption(
                    f"⚠️ **{row['field']}** — {row['description']} "
                    f"({row['affected_rows']:,} rows affected)"
                )

        st.markdown("---")


elif page == "🧹 Before vs After":
    st.title("🧹 Before vs After Cleaning")
    st.markdown("---")

    raw   = load_raw()
    clean_df = load_clean()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Raw Rows",       f"{clean['rows_before']:,}")
    col2.metric("Clean Rows",     f"{clean['rows_after']:,}")
    col3.metric("Rows Removed",   f"{clean['rows_removed']:,}")
    col4.metric("Retention Rate", f"{clean['retention_pct']}%")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🔢 Missing Values", "📋 Raw Sample", "✅ Clean Sample"])

    with tab1:
        st.subheader("Missing Values per Column")
        st.markdown("Comparing null counts before and after cleaning.")

        miss_raw   = raw.isna().sum().rename("Raw (nulls)")
        miss_clean = clean_df.isna().sum().rename("Clean (nulls)")
        comparison = pd.concat([miss_raw, miss_clean], axis=1)
        comparison["Resolved"] = comparison["Raw (nulls)"] - comparison["Clean (nulls)"]

        st.dataframe(comparison, use_container_width=True)

    with tab2:
        st.subheader("Raw Data Sample")
        st.caption("First 100 rows of the raw dataset — quality issues included.")

        # Highlight problematic rows
        st.dataframe(raw.head(100), use_container_width=True)

        st.markdown("**Quick stats on raw data:**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Null TINs",          raw["tin"].isna().sum())
        c2.metric("Negative Amounts",   int((raw["amount_due_ugx"] < 0).sum()))
        c3.metric("Non-UGX Currency",   int((raw["currency"] != "UGX").sum()))

    with tab3:
        st.subheader("Clean Data Sample")
        st.caption("First 100 rows after all quality checks applied.")

        st.dataframe(clean_df.head(100), use_container_width=True)

        st.markdown("**Quick stats on clean data:**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Null TINs",          clean_df["tin"].isna().sum())
        c2.metric("Negative Amounts",   int((clean_df["amount_due_ugx"] < 0).sum()))
        c3.metric("Non-UGX Currency",   int((clean_df["currency"] != "UGX").sum()))

elif page == "🔗 Lineage":
    st.title("🔗 Data Lineage")
    st.markdown("---")

    lineage = summary["lineage"]
    nodes   = {n["id"]: n for n in lineage["nodes"]}
    edges   = lineage["edges"]

    # Pipeline flow
    st.subheader("Pipeline Flow")
    st.markdown("How data moves through the governance pipeline.")
    st.markdown("")

    for edge in edges:
        source = nodes.get(edge["from"], {})
        target = nodes.get(edge["to"],   {})

        source_name = source.get("label", edge["from"])
        target_name = target.get("label", edge["to"])
        source_rows = source.get("rows",  "?")
        target_rows = target.get("rows",  "?")

        col1, col2, col3 = st.columns([3, 2, 3])

        with col1:
            st.info(f"📁 **{source_name}**\n\n{source_rows:,} rows")
        with col2:
            st.markdown("")
            st.markdown("")
            st.markdown(f"➡️ **{edge['label']}**")
            st.caption(edge["operation"])
        with col3:
            st.success(f"📁 **{target_name}**\n\n{target_rows:,} rows")

    st.markdown("---")

    # Dataset catalogue
    st.subheader("Dataset Catalogue")
    st.markdown("All datasets registered in this pipeline run.")
    st.markdown("")

    for node in lineage["nodes"]:
        with st.expander(f"📁 {node['label']}  —  {node['rows']:,} rows  ({node['type']})"):
            st.markdown(f"**Dataset ID:** `{node['id']}`")
            st.markdown(f"**Source Type:** `{node['type']}`")
            st.markdown(f"**Row Count:** {node['rows']:,}")