"""Streamlit dashboard for the Employee Data Analyzer."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Employee Data Analyzer", page_icon="👥", layout="wide")

st.title("👥 Employee Data Analyzer")
st.caption("Upload an employee CSV to explore workforce trends and retention.")


@st.cache_data
def load_and_clean(file_bytes: bytes) -> tuple[pd.DataFrame, int, int]:
    from io import BytesIO

    df = pd.read_csv(BytesIO(file_bytes))
    df.columns = df.columns.astype(str).str.strip()
    original_rows = len(df)
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip().replace("", pd.NA)
    df = df.drop_duplicates().copy()
    duplicates_removed = original_rows - len(df)
    for col in df.select_dtypes(include=np.number).columns:
        if df[col].isna().any():
            median = df[col].median()
            df[col] = df[col].fillna(median) if pd.notna(median) else df[col].fillna(0)
    for col in df.select_dtypes(include=["object", "string", "category"]).columns:
        if df[col].isna().any():
            modes = df[col].mode(dropna=True)
            df[col] = df[col].fillna(modes.iloc[0] if not modes.empty else "Unknown")
    return df, original_rows, duplicates_removed


uploaded = st.file_uploader("Employee CSV file", type=["csv"])
if uploaded is None:
    st.info("Choose Employee.csv above to start. Your file is processed in this app session.")
    st.stop()

try:
    df, original_rows, duplicates_removed = load_and_clean(uploaded.getvalue())
except Exception as exc:
    st.error(f"CSV could not be read: {exc}")
    st.stop()

if df.empty:
    st.warning("The CSV has no employee records.")
    st.stop()

st.sidebar.header("Filters")
filtered = df.copy()
categorical = list(filtered.select_dtypes(include=["object", "string", "category"]).columns)
for col in categorical:
    options = sorted(filtered[col].dropna().astype(str).unique().tolist())
    selected = st.sidebar.multiselect(col, options, default=options, key=f"filter_{col}")
    filtered = filtered[filtered[col].astype(str).isin(selected)]

if filtered.empty:
    st.warning("These filters leave no rows. Select at least one value for each filter.")
    st.stop()

left_count = stayed_count = None
if "LeaveOrNot" in filtered.columns:
    target = pd.to_numeric(filtered["LeaveOrNot"], errors="coerce")
    left_count = int((target == 1).sum())
    stayed_count = int((target == 0).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Employees", f"{len(filtered):,}")
c2.metric("Duplicate rows removed", f"{duplicates_removed:,}")
c3.metric("Stayed", f"{stayed_count:,}" if stayed_count is not None else "Column unavailable")
c4.metric("Left", f"{left_count:,}" if left_count is not None else "Column unavailable")

overview, charts, data, details = st.tabs(["Overview", "Charts", "Data", "Analysis"])

with overview:
    st.subheader("Workforce overview")
    numeric = list(filtered.select_dtypes(include=np.number).columns)
    if numeric:
        metric_cols = st.columns(min(4, len(numeric)))
        for i, col in enumerate(numeric[:4]):
            metric_cols[i].metric(f"Average {col}", f"{filtered[col].mean():,.2f}")
    if "LeaveOrNot" in filtered.columns:
        status = filtered["LeaveOrNot"].map({0: "Stayed", 1: "Left"}).fillna("Other")
        counts = status.value_counts().rename_axis("Status").reset_index(name="Employees")
        st.plotly_chart(px.pie(counts, names="Status", values="Employees", hole=0.45,
                               title="Stayed vs. left"), use_container_width=True)
        if len(filtered):
            st.write(f"Leaving rate: **{(left_count / len(filtered) * 100):.1f}%**")
    else:
        st.caption("Add a LeaveOrNot column (0 = stayed, 1 = left) for retention metrics.")

with charts:
    st.subheader("Explore a column")
    columns = filtered.columns.tolist()
    chosen = st.selectbox("Column to chart", columns)
    if pd.api.types.is_numeric_dtype(filtered[chosen]) and filtered[chosen].nunique() > 12:
        chart_df = filtered[[chosen]].dropna()
        st.plotly_chart(px.histogram(chart_df, x=chosen, title=f"Distribution of {chosen}"),
                        use_container_width=True)
    else:
        counts = filtered[chosen].astype(str).value_counts().rename_axis(chosen).reset_index(name="Employees")
        st.plotly_chart(px.bar(counts, x=chosen, y="Employees", title=f"Employees by {chosen}"),
                        use_container_width=True)
    if "LeaveOrNot" in filtered.columns and chosen != "LeaveOrNot":
        st.subheader(f"Leaving rate by {chosen}")
        rate = filtered.groupby(chosen, dropna=False)["LeaveOrNot"].mean().mul(100).reset_index(name="Leaving rate (%)")
        st.plotly_chart(px.bar(rate, x=chosen, y="Leaving rate (%)"), use_container_width=True)

with data:
    st.subheader("Cleaned employee records")
    st.caption(f"Started with {original_rows:,} rows; removed {duplicates_removed:,} duplicates.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button("Download filtered CSV", filtered.to_csv(index=False).encode("utf-8-sig"),
                       file_name="employee_data_cleaned.csv", mime="text/csv")

with details:
    st.subheader("Summary statistics")
    if numeric:
        st.dataframe(filtered[numeric].describe().T.round(2), use_container_width=True)
        if len(numeric) > 1:
            st.plotly_chart(px.imshow(filtered[numeric].corr(), text_auto=".2f", aspect="auto",
                                      color_continuous_scale="RdBu_r", title="Numeric correlations"),
                            use_container_width=True)
    for col in categorical:
        with st.expander(f"Counts for {col}"):
            st.dataframe(filtered[col].value_counts(dropna=False).rename("Employees").to_frame(),
                         use_container_width=True)
