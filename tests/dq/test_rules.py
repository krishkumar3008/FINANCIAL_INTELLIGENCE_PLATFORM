import pandas as pd

from src.etl.validator import validate_data


def make_empty_dfs():
    comps = pd.DataFrame(
        [
            {
                "id": "TCS",
                "company_name": "Tata Consultancy Services",
                "website": "https://tcs.com",
            }
        ]
    )
    pl = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "TCS",
                "year": 2024,
                "sales": 1000.0,
                "operating_profit": 200.0,
                "opm_percentage": 20.0,
                "profit_before_tax": 200.0,
                "tax_percentage": 25.0,
                "net_profit": 150.0,
                "dividend_payout": 50.0,
                "eps": 10.0,
            }
        ]
    )
    bs = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "TCS",
                "year": 2024,
                "total_assets": 1000.0,
                "total_liabilities": 1000.0,
                "equity_capital": 100.0,
                "reserves": 400.0,
            }
        ]
    )
    cf = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "TCS",
                "year": 2024,
                "operating_activity": 200.0,
                "investing_activity": -50.0,
                "financing_activity": -50.0,
                "net_cash_flow": 100.0,
            }
        ]
    )
    analysis = pd.DataFrame([{"id": 1, "company_id": "TCS"}])
    docs = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "TCS",
                "year": 2024,
                "Annual_Report": "https://tcs.com/report.pdf",
            }
        ]
    )
    pros = pd.DataFrame([{"id": 1, "company_id": "TCS"}])
    sectors = pd.DataFrame([{"id": 1, "company_id": "TCS", "broad_sector": "IT"}])
    prices = pd.DataFrame([{"id": 1, "company_id": "TCS", "date": "2024-01-01"}])
    ratios = pd.DataFrame(
        [{"id": 1, "company_id": "TCS", "year": 2024, "interest_coverage": 20.0}]
    )
    peers = pd.DataFrame([{"id": 1, "company_id": "TCS"}])
    mcap = pd.DataFrame([{"id": 1, "company_id": "TCS", "year": 2024}])
    return comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap


def test_dq01_primary_key():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    comps = pd.concat([comps, comps], ignore_index=True)
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-01" and r["severity"] == "CRITICAL"
        for _, r in res.iterrows()
    )


def test_dq02_composite_key():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    pl = pd.concat([pl, pl], ignore_index=True)
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-02" and r["severity"] == "CRITICAL"
        for _, r in res.iterrows()
    )


def test_dq03_foreign_key():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    pl = pd.DataFrame([{"id": 2, "company_id": "INVALID_COMP", "year": 2024}])
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-03" and r["severity"] == "CRITICAL"
        for _, r in res.iterrows()
    )


def test_dq04_bs_balance():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    bs.loc[0, "total_assets"] = 2000.0  # Mismatch with liabilities 1000.0
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-04" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq05_opm_cross_check():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    pl.loc[0, "opm_percentage"] = 50.0  # Mismatch with 200/1000 = 20%
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-05" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq06_positive_sales():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    pl.loc[0, "sales"] = 0.0
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-06" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq07_net_cash_flow():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    cf.loc[0, "net_cash_flow"] = 500.0  # Mismatch with 200 - 50 - 50 = 100
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-07" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq08_tax_rate():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    pl.loc[0, "tax_percentage"] = 120.0
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-08" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq09_dividend_cap():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    pl.loc[0, "dividend_payout"] = 150.0
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-09" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq10_url_format():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    comps.loc[0, "website"] = "invalid_url_string"
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-10" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq11_eps_sign():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    pl.loc[0, "eps"] = -10.0  # Positive net profit but negative EPS
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-11" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq12_ticker_validity():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    comps.loc[0, "id"] = "TCS$123"
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-12" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq13_icr_cross_check():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    pl.loc[0, "interest"] = 10.0  # calc icr = 200/10 = 20
    ratios.loc[0, "interest_coverage"] = 2.0  # Mismatch with reported 2.0
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-13" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )


def test_dq14_positive_assets():
    comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap = (
        make_empty_dfs()
    )
    bs.loc[0, "total_assets"] = -100.0
    res = validate_data(
        comps, pl, bs, cf, analysis, docs, pros, sectors, prices, ratios, peers, mcap
    )
    assert any(
        r["rule_id"] == "DQ-14" and r["severity"] == "WARNING"
        for _, r in res.iterrows()
    )
