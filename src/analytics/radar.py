import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.database import get_db_connection
from src.screener.engine import (
    calculate_composite_score,
    get_screener_universe,
    winsorise_and_scale,
)

DEFAULT_DB_PATH = "nifty100.db"
OUTPUT_DIR = "reports/radar_charts"

RADAR_METRICS = [
    ("return_on_equity_pct", "ROE", False),
    ("roce_percentage", "ROCE", False),
    ("net_profit_margin_pct", "NPM", False),
    ("debt_to_equity", "D/E (Inv)", True),
    ("free_cash_flow_cr", "FCF Score", False),
    ("pat_cagr_5yr", "PAT CAGR 5Y", False),
    ("revenue_cagr_5yr", "Rev CAGR 5Y", False),
    ("composite_quality_score", "Composite", False),
]


def prepare_radar_data(
    db_path: str = DEFAULT_DB_PATH,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Fetches screener universe with composite scores and scales all 8 radar axes to 0 - 100 scale.
    Maps peer group membership for each company.
    """
    df_raw = get_screener_universe(db_path)
    df = calculate_composite_score(df_raw)

    # Load peer group mapping
    conn = get_db_connection(db_path)
    try:
        pg = pd.read_sql("SELECT company_id, peer_group_name FROM peer_groups", conn)
        peer_map = dict(zip(pg["company_id"], pg["peer_group_name"]))
    finally:
        conn.close()

    df["peer_group_name"] = df["company_id"].map(peer_map)

    # Scale 8 metrics to 0-100 score for uniform radar display
    scaled_df = df.copy()

    for col_name, label, is_inverse in RADAR_METRICS:
        if col_name == "composite_quality_score":
            scaled_df[f"{col_name}_scaled"] = df[col_name].fillna(50.0)
        elif col_name == "debt_to_equity":
            # Inverse: lower D/E yields higher score
            s = winsorise_and_scale(df[col_name], invert=True)
            # Set Financials to 100
            s = np.where(df["is_financial"], 100.0, s)
            scaled_df[f"{col_name}_scaled"] = s
        else:
            scaled_df[f"{col_name}_scaled"] = winsorise_and_scale(
                df[col_name], invert=False
            )

    return scaled_df, peer_map


def generate_all_radar_charts(
    output_dir: str = OUTPUT_DIR, db_path: str = DEFAULT_DB_PATH
) -> None:
    """
    Generates radar/polar chart PNG files in reports/radar_charts/ for all companies.
    Filename format: {company_id}_radar.png.
    - Companies in a peer group: filled polygon vs peer group average dashed overlay.
    - Companies without a peer group: filled polygon vs Nifty 100 universe average reference overlay.
    """
    os.makedirs(output_dir, exist_ok=True)
    df, peer_map = prepare_radar_data(db_path)

    labels = [label for _, label, _ in RADAR_METRICS]
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Close polygon

    # Calculate pre-computed average vectors for each peer group
    peer_group_avgs = {}
    for p_name, group in df.dropna(subset=["peer_group_name"]).groupby(
        "peer_group_name"
    ):
        avg_vals = [group[f"{col}_scaled"].mean() for col, _, _ in RADAR_METRICS]
        avg_vals += avg_vals[:1]
        peer_group_avgs[p_name] = avg_vals

    # Calculate pre-computed average vector for whole Nifty 100 universe
    universe_avg = [df[f"{col}_scaled"].mean() for col, _, _ in RADAR_METRICS]
    universe_avg += universe_avg[:1]

    print(f"Generating radar charts for {len(df)} companies in '{output_dir}'...")

    plt.ioff()  # Turn off interactive plotting

    for _, row in df.iterrows():
        cid = row["company_id"]
        cname = row["company_name"]
        pname = row.get("peer_group_name")

        comp_vals = [row[f"{col}_scaled"] for col, _, _ in RADAR_METRICS]
        comp_vals += comp_vals[:1]

        fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw=dict(polar=True))

        # Company polygon
        ax.plot(angles, comp_vals, color="#0052CC", linewidth=2, label=f"{cid}")
        ax.fill(angles, comp_vals, color="#0052CC", alpha=0.25)

        # Overlay reference polygon
        if pd.notna(pname) and pname in peer_group_avgs:
            ref_vals = peer_group_avgs[pname]
            ref_label = f"{pname} Avg"
            ref_color = "#FF5630"
        else:
            ref_vals = universe_avg
            ref_label = "Nifty 100 Universe Avg"
            ref_color = "#36B37E"

        ax.plot(
            angles,
            ref_vals,
            color=ref_color,
            linewidth=2,
            linestyle="--",
            label=ref_label,
        )

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=9, fontweight="bold")
        ax.set_rlim(0, 100)

        subtitle = (
            f"Peer Group: {pname}"
            if pd.notna(pname)
            else "No Peer Group Assigned (Nifty 100 Benchmark)"
        )
        plt.title(
            f"{cid} - {cname[:25]}\n{subtitle}", size=11, fontweight="bold", y=1.08
        )
        plt.legend(loc="upper right", bbox_to_anchor=(1.25, 1.12), fontsize=8)
        plt.tight_layout()

        filepath = os.path.join(output_dir, f"{cid}_radar.png")
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close(fig)

    print(f"Successfully generated all {len(df)} radar charts in {output_dir}/")


if __name__ == "__main__":
    generate_all_radar_charts()
