
from src.analytics.peer import (
    compute_peer_percentiles,
    get_company_peer_percentiles,
    load_peer_groups,
    save_peer_percentiles_to_db,
)
from src.database import get_db_connection


def test_load_peer_groups():
    df = load_peer_groups()
    assert len(df) == 56
    assert "peer_group_name" in df.columns
    assert "company_id" in df.columns
    assert "is_benchmark" in df.columns
    assert df["peer_group_name"].nunique() == 11


def test_compute_peer_percentiles():
    df_pct = compute_peer_percentiles()
    assert not df_pct.empty
    assert set(df_pct.columns) == {
        "company_id",
        "peer_group_name",
        "metric",
        "value",
        "percentile_rank",
        "year",
    }
    # 56 companies * 10 metrics = 560 percentile records
    assert len(df_pct) == 560


def test_it_services_highest_roe_has_highest_rank():
    """Verify peer rankings: within IT Services peer group, company with highest ROE has highest percentile rank."""
    df_pct = compute_peer_percentiles()
    it_roe = df_pct[
        (df_pct["peer_group_name"] == "IT Services") & (df_pct["metric"] == "ROE")
    ]

    # Sort by value descending
    sorted_roe = it_roe.sort_values(by="value", ascending=False)
    top_company = sorted_roe.iloc[0]

    assert top_company["company_id"] == "TCS"
    assert top_company["percentile_rank"] == 1.0


def test_de_inverse_ranking():
    """Verify D/E ranking: lower D/E yields higher percentile rank."""
    df_pct = compute_peer_percentiles()
    fmcg_de = df_pct[
        (df_pct["peer_group_name"] == "FMCG") & (df_pct["metric"] == "D/E")
    ]

    # Company with lowest D/E should have percentile_rank == 1.0
    sorted_de = fmcg_de.sort_values(by="value", ascending=True)
    best_company = sorted_de.iloc[0]
    assert best_company["percentile_rank"] == 1.0


def test_unassigned_company_message():
    """For companies not in any peer group: return message 'No peer group assigned' — do not raise an error."""
    res = get_company_peer_percentiles("ABB")
    assert isinstance(res, str)
    assert res == "No peer group assigned"


def test_sqlite_persistence():
    df_pct = compute_peer_percentiles()
    save_peer_percentiles_to_db(df_pct)

    conn = get_db_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM peer_percentiles WHERE year = 2024"
        ).fetchone()[0]
        assert count == 560
    finally:
        conn.close()
