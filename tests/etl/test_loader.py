import pytest

from src.database import get_db_connection
from src.etl.loader import load_excel_file


def test_load_companies_file():
    df = load_excel_file("companies")
    assert not df.empty
    assert len(df) >= 90
    assert any(
        "id" in col.lower() or "ticker" in col.lower() or "company" in col.lower()
        for col in df.columns
    )


def test_load_sectors_file():
    df = load_excel_file("sectors")
    assert not df.empty
    assert len(df) >= 90


def test_load_pnl_file():
    df = load_excel_file("profitandloss")
    assert not df.empty
    assert len(df) >= 1000


def test_load_balancesheet_file():
    df = load_excel_file("balancesheet")
    assert not df.empty
    assert len(df) >= 1000


def test_load_cashflow_file():
    df = load_excel_file("cashflow")
    assert not df.empty
    assert len(df) >= 1000


def test_load_ratios_file():
    df = load_excel_file("financial_ratios")
    assert not df.empty
    assert len(df) >= 1000


def test_load_market_cap_file():
    df = load_excel_file("market_cap")
    assert not df.empty


def test_load_peer_groups_file():
    df = load_excel_file("peer_groups")
    assert not df.empty


def test_load_invalid_table_raises_keyerror():
    with pytest.raises(KeyError):
        load_excel_file("non_existent_table")


def test_db_companies_count():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM companies;")
        count = cur.fetchone()[0]
        assert count == 92
    finally:
        conn.close()
