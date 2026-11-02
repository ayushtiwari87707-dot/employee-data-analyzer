"""
Employee Data Analyzer (combined version)

Merges main.py (console summary + stayed/left chart) with
analysis.py / employee_data_analysis.py (full cleaning, comparison tables,
and chart generation). The two analysis files were identical, so they
are represented once here.

Expected columns in Employee.csv:
Education, JoiningYear, City, PaymentTier, Age, Gender, EverBenched,
ExperienceInCurrentDomain, LeaveOrNot
"""

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

CSV_PATH = Path("Employee.csv")
OUTPUT_DIR = Path("employee_analysis_output")
SHOW_PLOTS = True  # Set to False to only save charts without opening windows

TEXT_TYPES = ["object", "string", "category"]


# ----------------------------------------------------------------------------
# Loading and cleaning
# ----------------------------------------------------------------------------
def load_and_clean(path: Path) -> pd.DataFrame:
    """Load the CSV, normalize text, remove duplicates, and fill missing values."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    original_rows = len(df)

    # Standardize text so values such as " Pune " and "Pune" match.
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace("", pd.NA)

    # Remove duplicate rows
    df = df.drop_duplicates().copy()
    duplicates_removed = original_rows - len(df)

    # Numeric columns -> median (robust to extreme values)
    for col in df.select_dtypes(include=np.number).columns:
        if df[col].isna().any():
            median_value = np.nanmedian(df[col].to_numpy(dtype=float))
            df[col] = df[col].fillna(median_value)

    # Text columns -> most common value
    for col in df.select_dtypes(include=TEXT_TYPES).columns:
        if df[col].isna().any():
            modes = df[col].mode(dropna=True)
            df[col] = df[col].fillna(modes.iloc[0] if not modes.empty else "Unknown")

    print("EMPLOYEE DATA ANALYZER")
    print("----------------------")
    print(f"Original records: {original_rows:,}")
    print(f"Duplicate rows removed: {duplicates_removed:,}")
    print(f"Total records after cleaning: {len(df):,}")
    return df


# ----------------------------------------------------------------------------
# Console summary (from main.py)
# ----------------------------------------------------------------------------
def print_console_summary(df: pd.DataFrame) -> None:
    print("\nCLEANED DATASET SUMMARY")
    print("-----------------------")
    print(f"Rows: {len(df):,} | Columns: {len(df.columns)}")
    print("\nMissing values after cleaning:\n", df.isna().sum().to_string())
    print("\nNumeric summary:\n", df.describe(include=[np.number]).round(2).to_string())

    print("\nAVERAGE INFORMATION")
    print("-------------------")
    if "Age" in df.columns:
        print("Average age:", round(df["Age"].mean(), 2))
    if "ExperienceInCurrentDomain" in df.columns:
        print("Average experience in current domain:",
              round(df["ExperienceInCurrentDomain"].mean(), 2))

    if "City" in df.columns:
        print("\nEMPLOYEES BY CITY")
        print("-----------------")
        print(df["City"].value_counts())

    if "Education" in df.columns:
        print("\nEMPLOYEES BY EDUCATION")
        print("----------------------")
        print(df["Education"].value_counts())

    if "LeaveOrNot" in df.columns:
        left_count = int((df["LeaveOrNot"] == 1).sum())
        stayed_count = int((df["LeaveOrNot"] == 0).sum())
        print("\nEMPLOYEE LEAVING SUMMARY")
        print("------------------------")
        print("Employees who left:", left_count)
        print("Employees who stayed:", stayed_count)
        if len(df) > 0:
            print("Leaving percentage:", round(left_count / len(df) * 100, 2), "%")


def plot_stayed_vs_left(df: pd.DataFrame) -> None:
    """Bar chart of employees who stayed vs. left (from main.py)."""
    if "LeaveOrNot" not in df.columns:
        return
    OUTPUT_DIR.mkdir(exist_ok=True)
    left_count = int((df["LeaveOrNot"] == 1).sum())
    stayed_count = int((df["LeaveOrNot"] == 0).sum())

    plt.figure(figsize=(6, 5))
    plt.bar(["Stayed", "Left"], [stayed_count, left_count], color=["skyblue", "orange"])
    plt.title("Employees Who Stayed and Left")
    plt.xlabel("Employee Status")
    plt.ylabel("Number of Employees")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "employees_stayed_vs_left.png", dpi=160)
    if SHOW_PLOTS:
        plt.show()
    plt.close()


# ----------------------------------------------------------------------------
# Comparison tables (from analysis.py)
# ----------------------------------------------------------------------------
def save_comparison_tables(df: pd.DataFrame) -> None:
    """Save pairwise categorical comparisons and numeric summaries."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    categorical = list(df.select_dtypes(include=TEXT_TYPES).columns)
    numeric = list(df.select_dtypes(include=np.number).columns)

    # Every pair of category fields: counts and row percentages
    with (OUTPUT_DIR / "categorical_comparisons.txt").open("w", encoding="utf-8") as report:
        for left, right in itertools.combinations(categorical, 2):
            report.write(f"\n{'=' * 72}\n{left} compared with {right}\n")
            report.write(pd.crosstab(df[left], df[right]).to_string())
            report.write("\n\nRow percentages:\n")
            report.write(
                pd.crosstab(df[left], df[right], normalize="index").mul(100).round(1).to_string()
            )
            report.write("\n")

    # Every numeric measure grouped by every category
    with (OUTPUT_DIR / "numeric_by_category.txt").open("w", encoding="utf-8") as report:
        for category in categorical:
            for measure in numeric:
                report.write(f"\n{measure} by {category}\n")
                grouped = df.groupby(category, dropna=False)[measure].agg(
                    ["count", "mean", "median", "min", "max"]
                )
                report.write(grouped.round(2).to_string())
                report.write("\n")

    if numeric:
        df[numeric].describe().round(2).to_csv(OUTPUT_DIR / "numeric_summary.csv")
        df[numeric].corr().round(3).to_csv(OUTPUT_DIR / "numeric_correlations.csv")


# ----------------------------------------------------------------------------
# Visualizations (from analysis.py)
# ----------------------------------------------------------------------------
def create_visualizations(df: pd.DataFrame) -> None:
    """Create plots for distributions and comparisons among fields."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    categorical = list(df.select_dtypes(include=TEXT_TYPES).columns)
    numeric = list(df.select_dtypes(include=np.number).columns)

    # Distribution of each categorical field
    for col in categorical:
        counts = df[col].value_counts().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(9, max(4, 0.45 * len(counts))))
        counts.plot(kind="barh", ax=ax, color="#2878B5")
        ax.set(title=f"Employee count by {col}", xlabel="Employees", ylabel=col)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"distribution_{col}.png", dpi=160)
        plt.close(fig)

    # Box plots: each numeric field across each categorical field
    for category in categorical:
        if df[category].nunique() > 15:  # skip unreadable plots
            continue
        for measure in numeric:
            fig, ax = plt.subplots(figsize=(9, 5))
            sns.boxplot(data=df, x=category, y=measure, color="#70B7A5", ax=ax)
            ax.set(title=f"{measure} across {category}")
            ax.tick_params(axis="x", rotation=25)
            fig.tight_layout()
            fig.savefig(OUTPUT_DIR / f"compare_{measure}_by_{category}.png", dpi=160)
            plt.close(fig)

    # Scatter plot for every numeric pair
    for x_col, y_col in itertools.combinations(numeric, 2):
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.scatterplot(data=df, x=x_col, y=y_col, alpha=0.35, s=24, color="#2878B5", ax=ax)
        ax.set_title(f"{y_col} compared with {x_col}")
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"scatter_{x_col}_vs_{y_col}.png", dpi=150)
        plt.close(fig)

    # Correlation heatmap
    if len(numeric) > 1:
        fig, ax = plt.subplots(figsize=(9, 7))
        sns.heatmap(df[numeric].corr(), annot=True, cmap="vlag", center=0, fmt=".2f", ax=ax)
        ax.set_title("Correlation between numeric fields")
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "numeric_correlation_heatmap.png", dpi=170)
        plt.close(fig)

    # Leaving rate by each category
    target = "LeaveOrNot"
    if target in df.columns:
        for category in categorical:
            if category == target or df[category].nunique() > 15:
                continue
            rates = df.groupby(category, observed=False)[target].mean().sort_values(ascending=False) * 100
            fig, ax = plt.subplots(figsize=(9, 5))
            rates.plot(kind="bar", color="#E07A5F", ax=ax)
            ax.set(title=f"Leaving rate by {category}",
                   ylabel="Employees who left (%)", xlabel=category)
            ax.tick_params(axis="x", rotation=25)
            fig.tight_layout()
            fig.savefig(OUTPUT_DIR / f"leaving_rate_by_{category}.png", dpi=160)
            plt.close(fig)


# ----------------------------------------------------------------------------
def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found: {CSV_PATH}. Update CSV_PATH at the top of the script."
        )

    df = load_and_clean(CSV_PATH)
    print_console_summary(df)
    save_comparison_tables(df)
    create_visualizations(df)
    plot_stayed_vs_left(df)

    print(f"\nAnalysis complete. Tables and charts are in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()