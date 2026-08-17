import pandas as pd

from src.etl.validator import validate_data


# Create minimal valid dataframes to pass to validator
def get_valid_mock_dfs():
    companies = pd.DataFrame(
        [
            {
                "id": "ABB",
                "company_name": "ABB India Ltd",
                "website": "https://www.abb.co.in",
                "nse_profile": "https://www.nseindia.com/get-quotes/equity?symbol=ABB",
                "bse_profile": "https://www.bseindia.com/stock-share-price/abb-india-ltd/abb/500002/",
                "face_value": 2.0,
                "book_value": 300.0,
                "roce_percentage": 25.0,
                "roe_percentage": 20.0,
                "company_logo": "logo.png",
                "chart_link": "chart.png",
                "about_company": "about ABB",
            }
        ]
    )

    pl = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "year": 2021,
                "sales": 1000.0,
                "expenses": 800.0,
                "operating_profit": 200.0,
                "opm_percentage": 20.0,
                "other_income": 10.0,
                "interest": 5.0,
                "depreciation": 15.0,
                "profit_before_tax": 190.0,
                "tax_percentage": 25.0,
                "net_profit": 142.5,
                "eps": 6.7,
                "dividend_payout": 30.0,
            },
            {
                "id": 2,
                "company_id": "ABB",
                "year": 2022,
                "sales": 1100.0,
                "expenses": 850.0,
                "operating_profit": 250.0,
                "opm_percentage": 22.73,
                "other_income": 15.0,
                "interest": 4.0,
                "depreciation": 16.0,
                "profit_before_tax": 245.0,
                "tax_percentage": 25.0,
                "net_profit": 183.75,
                "eps": 8.6,
                "dividend_payout": 30.0,
            },
            {
                "id": 3,
                "company_id": "ABB",
                "year": 2023,
                "sales": 1200.0,
                "expenses": 900.0,
                "operating_profit": 300.0,
                "opm_percentage": 25.00,
                "other_income": 20.0,
                "interest": 3.0,
                "depreciation": 17.0,
                "profit_before_tax": 300.0,
                "tax_percentage": 25.0,
                "net_profit": 225.0,
                "eps": 10.6,
                "dividend_payout": 30.0,
            },
            {
                "id": 4,
                "company_id": "ABB",
                "year": 2024,
                "sales": 1300.0,
                "expenses": 950.0,
                "operating_profit": 350.0,
                "opm_percentage": 26.92,
                "other_income": 25.0,
                "interest": 2.0,
                "depreciation": 18.0,
                "profit_before_tax": 355.0,
                "tax_percentage": 25.0,
                "net_profit": 266.25,
                "eps": 12.5,
                "dividend_payout": 30.0,
            },
            {
                "id": 5,
                "company_id": "ABB",
                "year": 2025,
                "sales": 1400.0,
                "expenses": 1000.0,
                "operating_profit": 400.0,
                "opm_percentage": 28.57,
                "other_income": 30.0,
                "interest": 1.0,
                "depreciation": 19.0,
                "profit_before_tax": 410.0,
                "tax_percentage": 25.0,
                "net_profit": 307.5,
                "eps": 14.5,
                "dividend_payout": 30.0,
            },
        ]
    )

    bs = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "year": 2021,
                "equity_capital": 50.0,
                "reserves": 950.0,
                "borrowings": 100.0,
                "other_liabilities": 200.0,
                "total_liabilities": 1300.0,  # equity + res + borrow + other_liab = 50+950+100+200 = 1300
                "fixed_assets": 500.0,
                "cwip": 50.0,
                "investments": 150.0,
                "other_asset": 600.0,
                "total_assets": 1300.0,
            }
        ]
    )

    cf = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "year": 2021,
                "operating_activity": 200.0,
                "investing_activity": -100.0,
                "financing_activity": -50.0,
                "net_cash_flow": 50.0,
            }
        ]
    )

    analysis = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "compounded_sales_growth": "15%",
                "compounded_profit_growth": "20%",
                "stock_price_cagr": "25%",
                "roe": "18%",
            }
        ]
    )

    docs = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "Year": 2021,
                "Annual_Report": "https://www.abb.co.in/report2021.pdf",
            }
        ]
    )

    pros = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "pros": "Good growth",
                "cons": "High valuation",
            }
        ]
    )

    sectors = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "broad_sector": "Industrials",
                "sub_sector": "Heavy Electrical Equipment",
                "index_weight_pct": 1.2,
                "market_cap_category": "Large Cap",
            }
        ]
    )

    prices = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "date": "2024-01-01",
                "open_price": 3000.0,
                "high_price": 3050.0,
                "low_price": 2980.0,
                "close_price": 3020.0,
                "volume": 10000,
                "adjusted_close": 3020.0,
            }
        ]
    )

    ratios = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "year": 2021,
                "net_profit_margin_pct": 14.25,
                "operating_profit_margin_pct": 20.0,
                "return_on_equity_pct": 20.0,
                "debt_to_equity": 0.1,
                "interest_coverage": 40.0,  # EBIT / Interest = 200 / 5 = 40.0
                "asset_turnover": 0.77,
                "free_cash_flow_cr": 100.0,
                "capex_cr": 50.0,
                "earnings_per_share": 6.7,
                "book_value_per_share": 300.0,
                "dividend_payout_ratio_pct": 30.0,
                "total_debt_cr": 100.0,
                "cash_from_operations_cr": 200.0,
            }
        ]
    )

    peers = pd.DataFrame(
        [
            {
                "id": 1,
                "peer_group_name": "Capital Goods",
                "company_id": "ABB",
                "is_benchmark": 1,
            }
        ]
    )

    market_cap = pd.DataFrame(
        [
            {
                "id": 1,
                "company_id": "ABB",
                "year": 2021,
                "market_cap_crore": 60000.0,
                "enterprise_value_crore": 60100.0,
                "pe_ratio": 90.0,
                "pb_ratio": 15.0,
                "ev_ebitda": 45.0,
                "dividend_yield_pct": 0.5,
            }
        ]
    )

    return (
        companies,
        pl,
        bs,
        cf,
        analysis,
        docs,
        pros,
        sectors,
        prices,
        ratios,
        peers,
        market_cap,
    )


def test_validator_valid_data():
    dfs = get_valid_mock_dfs()
    failures = validate_data(*dfs)
    assert len(failures) == 0 or (
        len(failures) > 0 and not (failures["severity"] == "CRITICAL").any()
    )


def test_validator_dq01_duplicate_pk():
    dfs = list(get_valid_mock_dfs())
    # Create duplicate pk in companies
    dfs[0] = pd.DataFrame(
        [{"id": "ABB", "company_name": "ABB 1"}, {"id": "ABB", "company_name": "ABB 2"}]
    )

    failures = validate_data(*dfs)
    dq01_fails = failures[failures["rule_id"] == "DQ-01"]
    assert len(dq01_fails) > 0
    assert dq01_fails.iloc[0]["severity"] == "CRITICAL"


def test_validator_dq02_duplicate_composite_pk():
    dfs = list(get_valid_mock_dfs())
    # Create composite duplicate in profitandloss: same company, same year
    pl_dup = dfs[1].copy()
    pl_dup.loc[1, "year"] = 2021  # Row 1 year changes from 2022 to 2021
    dfs[1] = pl_dup

    failures = validate_data(*dfs)
    dq02_fails = failures[failures["rule_id"] == "DQ-02"]
    assert len(dq02_fails) > 0
    assert dq02_fails.iloc[0]["severity"] == "CRITICAL"


def test_validator_dq03_fk_integrity():
    dfs = list(get_valid_mock_dfs())
    # Child table has company_id not in companies
    pl_fk = dfs[1].copy()
    pl_fk.loc[0, "company_id"] = "MISSING_CO"
    dfs[1] = pl_fk

    failures = validate_data(*dfs)
    dq03_fails = failures[failures["rule_id"] == "DQ-03"]
    assert len(dq03_fails) > 0
    assert dq03_fails.iloc[0]["severity"] == "CRITICAL"


def test_validator_dq04_bs_balance():
    dfs = list(get_valid_mock_dfs())
    # Unbalance the balance sheet
    bs_unbalanced = dfs[2].copy()
    bs_unbalanced.loc[0, "total_assets"] = (
        5000.0  # Liabilities+Equity = 1300, Assets = 5000
    )
    dfs[2] = bs_unbalanced

    failures = validate_data(*dfs)
    dq04_fails = failures[failures["rule_id"] == "DQ-04"]
    assert len(dq04_fails) > 0
    assert dq04_fails.iloc[0]["severity"] == "WARNING"


def test_validator_dq05_opm_cross_check():
    dfs = list(get_valid_mock_dfs())
    # Mismatch OPM
    pl_mismatch = dfs[1].copy()
    pl_mismatch.loc[0, "opm_percentage"] = (
        99.0  # reported 99%, but calculated 200/1000 = 20%
    )
    dfs[1] = pl_mismatch

    failures = validate_data(*dfs)
    dq05_fails = failures[failures["rule_id"] == "DQ-05"]
    assert len(dq05_fails) > 0
    assert dq05_fails.iloc[0]["severity"] == "WARNING"


def test_validator_dq06_positive_sales():
    dfs = list(get_valid_mock_dfs())
    # Negative sales
    pl_neg = dfs[1].copy()
    pl_neg.loc[0, "sales"] = -100.0
    dfs[1] = pl_neg

    failures = validate_data(*dfs)
    dq06_fails = failures[failures["rule_id"] == "DQ-06"]
    assert len(dq06_fails) > 0
    assert dq06_fails.iloc[0]["severity"] == "WARNING"


def test_validator_dq07_net_cash_flow():
    dfs = list(get_valid_mock_dfs())
    # cash flow mismatch
    cf_mismatch = dfs[3].copy()
    cf_mismatch.loc[0, "net_cash_flow"] = 5000.0  # reported 5000, but sum is 50
    dfs[3] = cf_mismatch

    failures = validate_data(*dfs)
    dq07_fails = failures[failures["rule_id"] == "DQ-07"]
    assert len(dq07_fails) > 0
    assert dq07_fails.iloc[0]["severity"] == "WARNING"


def test_validator_dq10_invalid_url():
    dfs = list(get_valid_mock_dfs())
    # invalid url in website
    comp_url = dfs[0].copy()
    comp_url.loc[0, "website"] = "not_a_valid_url"
    dfs[0] = comp_url

    failures = validate_data(*dfs)
    dq10_fails = failures[failures["rule_id"] == "DQ-10"]
    assert len(dq10_fails) > 0
    assert dq10_fails.iloc[0]["severity"] == "WARNING"


def test_validator_dq11_eps_sign():
    dfs = list(get_valid_mock_dfs())
    # net_profit is positive, eps is negative
    pl_eps = dfs[1].copy()
    pl_eps.loc[0, "eps"] = -1.5
    dfs[1] = pl_eps

    failures = validate_data(*dfs)
    dq11_fails = failures[failures["rule_id"] == "DQ-11"]
    assert len(dq11_fails) > 0
    assert dq11_fails.iloc[0]["severity"] == "WARNING"


def test_validator_dq16_price_uniqueness():
    dfs = list(get_valid_mock_dfs())
    # duplicate price record
    prices_dup = dfs[8].copy()
    new_row = prices_dup.iloc[0].copy()
    new_row["id"] = 2
    dfs[8] = pd.concat([prices_dup, pd.DataFrame([new_row])], ignore_index=True)

    failures = validate_data(*dfs)
    dq16_fails = failures[failures["rule_id"] == "DQ-16"]
    assert len(dq16_fails) > 0
    assert dq16_fails.iloc[0]["severity"] == "CRITICAL"
