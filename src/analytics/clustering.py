import os
import sqlite3

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def load_company_data(
    db_path: str = "nifty100.db", intel_path: str = "output/cashflow_intelligence.xlsx"
) -> pd.DataFrame:
    """
    Loads latest year financial metrics and sector info for all 92 companies.
    """
    conn = sqlite3.connect(db_path)

    # Query companies + sectors
    query_comp = """
    SELECT c.id as company_id, c.company_name, c.roe_percentage, c.roce_percentage, s.broad_sector, s.sub_sector
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    """
    df_comp = pd.read_sql(query_comp, conn)

    # Query latest ratios per company (excluding TTM year 9999)
    query_ratios = """
    SELECT company_id, year, return_on_equity_pct, debt_to_equity, revenue_cagr_5yr, pat_cagr_5yr,
           operating_profit_margin_pct, net_profit_margin_pct, interest_coverage, asset_turnover
    FROM financial_ratios
    WHERE year != 9999
    ORDER BY company_id, year ASC
    """
    df_ratios_all = pd.read_sql(query_ratios, conn)

    # Get latest year for each company
    df_ratios_latest = df_ratios_all.groupby("company_id").last().reset_index()

    conn.close()

    # Load cashflow intelligence for fcf_cagr_5yr
    df_intel = (
        pd.read_excel(intel_path) if os.path.exists(intel_path) else pd.DataFrame()
    )

    # Merge datasets
    df = df_comp.merge(df_ratios_latest, on="company_id", how="left")
    if not df_intel.empty and "fcf_cagr_5yr" in df_intel.columns:
        df = df.merge(
            df_intel[["company_id", "fcf_cagr_5yr"]], on="company_id", how="left"
        )
    else:
        df["fcf_cagr_5yr"] = np.nan

    # Fallback roe_percentage if return_on_equity_pct is null
    df["return_on_equity_pct"] = df["return_on_equity_pct"].fillna(df["roe_percentage"])

    return df


def run_clustering_and_profiling(
    db_path: str = "nifty100.db",
    intel_path: str = "output/cashflow_intelligence.xlsx",
    output_labels_csv: str = "output/cluster_labels.csv",
    elbow_plot_path: str = "reports/elbow_plot.png",
    heatmap_path: str = "reports/correlation_heatmap.png",
    outlier_csv: str = "output/outlier_report.csv",
    portfolio_stats_csv: str = "output/portfolio_stats.csv",
):
    """
    Executes KMeans clustering, cluster profiling, correlation heatmap, outlier detection, and portfolio statistics.
    """
    os.makedirs(os.path.dirname(output_labels_csv), exist_ok=True)
    os.makedirs(os.path.dirname(elbow_plot_path), exist_ok=True)

    df = load_company_data(db_path, intel_path)

    feature_cols = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    # 1. Missing Value Imputation with Sector Median
    df_features = df[["company_id", "broad_sector"] + feature_cols].copy()
    for col in feature_cols:
        # Groupby sector median
        sector_medians = df_features.groupby("broad_sector")[col].transform("median")
        df_features[col] = df_features[col].fillna(sector_medians)
        # Global median fallback if sector median is NaN
        df_features[col] = df_features[col].fillna(df_features[col].median())

    X = df_features[feature_cols].values

    # 2. StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Elbow Plot (k=2 to 10)
    inertias = []
    k_range = range(2, 11)
    for k in k_range:
        kmeans_k = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans_k.fit(X_scaled)
        inertias.append(kmeans_k.inertia_)

    plt.figure(figsize=(7, 4), dpi=150)
    plt.plot(k_range, inertias, "bo-", linewidth=2, markersize=7)
    plt.axvline(x=5, color="r", linestyle="--", label="k=5 Selected")
    plt.title("KMeans Elbow Plot (Inertia vs k)", fontsize=12, fontweight="bold")
    plt.xlabel("Number of Clusters (k)", fontsize=10)
    plt.ylabel("Inertia (WCSS)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(elbow_plot_path)
    plt.close()
    print(f"[OK] Saved elbow plot to {elbow_plot_path}")

    # 4. Fit KMeans k=5
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_ids = kmeans.fit_predict(X_scaled)
    df_features["cluster_id"] = cluster_ids

    # Calculate distance from assigned centroid
    centroids = kmeans.cluster_centers_
    distances = [
        np.linalg.norm(X_scaled[i] - centroids[cluster_ids[i]])
        for i in range(len(cluster_ids))
    ]
    df_features["distance_from_centroid"] = distances

    # 5. Profile Clusters to Assign Descriptive Names
    profile = df_features.groupby("cluster_id")[feature_cols].agg(["mean", "median"])
    print("\nCluster Financial Profiles (Medians):")
    medians = df_features.groupby("cluster_id")[feature_cols].median()
    print(medians)

    # Map clusters to descriptive names based on their profiles
    name_map = {}
    for cid in range(5):
        c_roe = medians.loc[cid, "return_on_equity_pct"]
        c_de = medians.loc[cid, "debt_to_equity"]
        c_rev_growth = medians.loc[cid, "revenue_cagr_5yr"]
        c_opm = medians.loc[cid, "operating_profit_margin_pct"]

        if c_roe > 20 and c_opm > 20 and c_de < 0.5:
            name_map[cid] = "High-Quality Compounders"
        elif c_rev_growth > 12 and c_roe > 12:
            name_map[cid] = "Emerging Growth"
        elif c_de > 1.0 or c_roe < 8:
            name_map[cid] = "Distressed or Turnaround"
        elif c_opm > 15 and c_de < 0.8:
            name_map[cid] = "Defensive Dividend Payers"
        else:
            name_map[cid] = "Value Cyclicals"

    # Ensure all 5 names are assigned uniquely if duplicates occur
    default_names = [
        "High-Quality Compounders",
        "Defensive Dividend Payers",
        "Value Cyclicals",
        "Distressed or Turnaround",
        "Emerging Growth",
    ]
    assigned_names = set(name_map.values())

    if len(name_map) < 5 or len(assigned_names) < 5:
        # Sort cluster IDs by ROE descending
        sorted_cids = medians.sort_values(
            by="return_on_equity_pct", ascending=False
        ).index.tolist()
        name_map = {
            sorted_cids[0]: "High-Quality Compounders",
            sorted_cids[1]: "Emerging Growth",
            sorted_cids[2]: "Defensive Dividend Payers",
            sorted_cids[3]: "Value Cyclicals",
            sorted_cids[4]: "Distressed or Turnaround",
        }

    df_features["cluster_name"] = df_features["cluster_id"].map(name_map)

    # Save output/cluster_labels.csv
    df_output = df_features[
        ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    ].sort_values("company_id")
    df_output.to_csv(output_labels_csv, index=False)
    print(
        f"[OK] Saved cluster labels ({len(df_output)} records) to {output_labels_csv}"
    )

    # 6. Correlation Heatmap across 10 KPIs
    kpi_cols_10 = [
        "return_on_equity_pct",
        "roce_percentage",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "fcf_cagr_5yr",
    ]

    df_kpis = df[kpi_cols_10].copy()
    for col in kpi_cols_10:
        df_kpis[col] = df_kpis[col].fillna(df_kpis[col].median())

    corr_matrix = df_kpis.corr(method="pearson")

    plt.figure(figsize=(9, 7), dpi=150)
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        linewidths=0.5,
    )
    plt.title(
        "Pearson Correlation Heatmap of 10 Core Financial KPIs",
        fontsize=12,
        fontweight="bold",
        pad=10,
    )
    plt.tight_layout()
    plt.savefig(heatmap_path)
    plt.close()
    print(f"[OK] Saved correlation heatmap to {heatmap_path}")

    # 7. Outlier Detection (Z-score > 3 per broad_sector)
    outlier_records = []
    for sector, grp in df.groupby("broad_sector"):
        for col in kpi_cols_10:
            series = grp[col].dropna()
            if len(series) > 2 and series.std() > 0:
                z_scores = (series - series.mean()) / series.std()
                outliers = z_scores[z_scores.abs() > 3]
                for idx, z_val in outliers.items():
                    comp_id = grp.loc[idx, "company_id"]
                    val = grp.loc[idx, col]
                    outlier_records.append(
                        {
                            "company_id": comp_id,
                            "broad_sector": sector,
                            "metric": col,
                            "value": val,
                            "z_score": round(z_val, 2),
                        }
                    )

    df_outliers = pd.DataFrame(outlier_records)
    if df_outliers.empty:
        df_outliers = pd.DataFrame(
            columns=["company_id", "broad_sector", "metric", "value", "z_score"]
        )
    df_outliers.to_csv(outlier_csv, index=False)
    print(
        f"[OK] Saved outlier report ({len(df_outliers)} flagged records) to {outlier_csv}"
    )

    # 8. Portfolio Statistics (P10, P25, P50, P75, P90, Mean, Std)
    stats_data = []
    for col in kpi_cols_10:
        s = df[col].dropna()
        stats_data.append(
            {
                "metric": col,
                "P10": round(s.quantile(0.10), 2),
                "P25": round(s.quantile(0.25), 2),
                "P50": round(s.quantile(0.50), 2),
                "P75": round(s.quantile(0.75), 2),
                "P90": round(s.quantile(0.90), 2),
                "Mean": round(s.mean(), 2),
                "Std": round(s.std(), 2),
            }
        )

    df_stats = pd.DataFrame(stats_data)
    df_stats.to_csv(portfolio_stats_csv, index=False)
    print(f"[OK] Saved portfolio stats to {portfolio_stats_csv}")

    return df_output, df_stats


if __name__ == "__main__":
    run_clustering_and_profiling()
