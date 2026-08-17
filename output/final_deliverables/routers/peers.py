import pandas as pd
from fastapi import APIRouter, HTTPException

from src.database import get_db_connection

router = APIRouter()


@router.get(
    "/peers/{group_name}",
    summary="Get companies in a peer group with 10 KPI percentile ranks",
)
def get_peer_group_details(group_name: str):
    """
    Returns all companies in a peer group with percentile ranks for 10 metrics.
    Returns HTTP 404 for unknown peer group.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT peer_group_name FROM peer_groups WHERE LOWER(peer_group_name) = LOWER(?);",
            (group_name,),
        )
        g_row = cur.fetchone()
        if not g_row:
            raise HTTPException(
                status_code=404, detail=f"Peer group '{group_name}' not found."
            )

        exact_gname = g_row[0]

        # Fetch peer percentiles
        query = """
        SELECT pp.company_id, c.company_name, pp.peer_group_name, pp.metric, pp.value, pp.percentile_rank
        FROM peer_percentiles pp
        JOIN companies c ON pp.company_id = c.id
        WHERE LOWER(pp.peer_group_name) = LOWER(?)
        ORDER BY pp.company_id, pp.metric;
        """
        df = pd.read_sql(query, conn, params=(exact_gname,))
        if df.empty:
            # If peer_percentiles table does not have records, build from peer_groups
            q_pg = """
            SELECT pg.company_id, c.company_name, pg.peer_group_name, pg.is_benchmark
            FROM peer_groups pg
            JOIN companies c ON pg.company_id = c.id
            WHERE LOWER(pg.peer_group_name) = LOWER(?)
            ORDER BY pg.company_id;
            """
            df_pg = pd.read_sql(q_pg, conn, params=(exact_gname,))
            rows = df_pg.to_dict(orient="records")
            return rows

        # Group metrics by company_id
        companies_map = {}
        for _, row in df.iterrows():
            cid = row["company_id"]
            if cid not in companies_map:
                companies_map[cid] = {
                    "company_id": cid,
                    "company_name": row["company_name"],
                    "peer_group_name": exact_gname,
                    "metrics": {},
                }
            companies_map[cid]["metrics"][row["metric"]] = {
                "value": row["value"],
                "percentile_rank": row["percentile_rank"],
            }

        return list(companies_map.values())
    finally:
        conn.close()


@router.get(
    "/companies/{ticker}/peers/compare", summary="Get radar chart comparison data"
)
def compare_company_peers(ticker: str):
    """
    Returns 8-axis radar comparison metrics: target company values, peer group average, and benchmark company.
    Returns HTTP 404 if ticker not found.
    """
    t_upper = ticker.upper()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM companies WHERE id = ?;", (t_upper,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=404, detail=f"Company '{ticker}' not found."
            )

        # Get peer group for ticker
        cur.execute(
            "SELECT peer_group_name, is_benchmark FROM peer_groups WHERE company_id = ?;",
            (t_upper,),
        )
        pg_row = cur.fetchone()
        pg_name = pg_row["peer_group_name"] if pg_row else None

        # Load radar metrics for company and peer group
        from src.analytics.radar import RADAR_METRICS, prepare_radar_data

        scaled_df, peer_map = prepare_radar_data()

        comp_match = scaled_df[scaled_df["company_id"] == t_upper]
        if comp_match.empty:
            raise HTTPException(
                status_code=404, detail=f"Radar data for company '{ticker}' not found."
            )

        comp_data = comp_match.iloc[0]

        axes = [m[1] for m in RADAR_METRICS]
        axis_cols = [f"{m[0]}_scaled" for m in RADAR_METRICS]

        company_scores = [
            round(float(comp_data.get(col, 50.0)), 2) for col in axis_cols
        ]

        # Peer group average
        if pg_name:
            peer_df = scaled_df[scaled_df["peer_group_name"] == pg_name]
            peer_avg = [round(float(peer_df[col].mean()), 2) for col in axis_cols]

            # Benchmark company in peer group
            bm_comp = peer_df[
                peer_df["company_id"].isin(
                    [
                        r["company_id"]
                        for r in cur.execute(
                            "SELECT company_id FROM peer_groups WHERE peer_group_name = ? AND is_benchmark = 1;",
                            (pg_name,),
                        ).fetchall()
                    ]
                )
            ]
            if not bm_comp.empty:
                bm_scores = [
                    round(float(bm_comp.iloc[0].get(col, 50.0)), 2) for col in axis_cols
                ]
                bm_name = bm_comp.iloc[0]["company_id"]
            else:
                bm_scores = peer_avg
                bm_name = f"{pg_name} Avg"
        else:
            peer_avg = company_scores
            bm_scores = company_scores
            bm_name = t_upper

        return {
            "company_id": t_upper,
            "peer_group_name": pg_name or "Unassigned",
            "benchmark_company_id": bm_name,
            "axes": axes,
            "company_scores": company_scores,
            "peer_group_average_scores": peer_avg,
            "benchmark_scores": bm_scores,
        }
    finally:
        conn.close()
