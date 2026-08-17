import os

from src.analytics.ratios import (
    compute_asset_turnover,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_net_debt,
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_return_on_assets,
    compute_return_on_capital_employed,
    compute_return_on_equity,
    get_icr_label,
    is_high_leverage,
    is_icr_at_risk,
)


def test_npm_normal():
    assert compute_net_profit_margin(15.0, 100.0) == 15.0
    assert compute_net_profit_margin(-5.0, 50.0) == -10.0


def test_npm_zero_sales():
    assert compute_net_profit_margin(15.0, 0.0) is None


def test_opm_normal():
    assert compute_operating_profit_margin(20.0, 100.0) == 20.0


def test_opm_zero_sales():
    assert compute_operating_profit_margin(20.0, 0.0) is None


def test_opm_cross_check_mismatch():
    # Remove existing log to test output
    log_path = "output/ratio_edge_cases.log"
    if os.path.exists(log_path):
        os.remove(log_path)

    val = compute_operating_profit_margin(
        20.0, 100.0, reported_opm=15.0, company_id="TESTCO", year=2024
    )
    assert val == 20.0
    assert os.path.exists(log_path)
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "[OPM_MISMATCH]" in content
    assert "TESTCO" in content
    assert "2024" in content


def test_roe_normal():
    assert compute_return_on_equity(20.0, 10.0, 90.0) == 20.0


def test_roe_negative_or_zero_equity():
    assert compute_return_on_equity(20.0, 0.0, 0.0) is None
    assert compute_return_on_equity(20.0, 10.0, -20.0) is None


def test_roce_normal():
    # EBIT = PBT + Interest = 150 + 10 = 160
    # Capital Employed = equity + reserves + borrowings = 50 + 450 + 300 = 800
    # ROCE = 160 / 800 * 100 = 20%
    assert compute_return_on_capital_employed(150.0, 10.0, 50.0, 450.0, 300.0) == 20.0


def test_roce_negative_or_zero_capital():
    assert compute_return_on_capital_employed(150.0, 10.0, -10.0, -10.0, 10.0) is None


def test_roa_normal():
    assert compute_return_on_assets(10.0, 100.0) == 10.0


def test_roa_zero_assets():
    assert compute_return_on_assets(10.0, 0.0) is None


def test_debt_to_equity_normal():
    assert compute_debt_to_equity(100.0, 50.0, 150.0) == 0.5
    assert compute_debt_to_equity(0.0, 50.0, 150.0) == 0.0


def test_debt_to_equity_zero_equity():
    assert compute_debt_to_equity(100.0, 0.0, 0.0) is None


def test_high_leverage_flag():
    # D/E > 5 and not Financials => True
    assert is_high_leverage(6.0, "Industrials") is True
    # D/E > 5 and Financials => False
    assert is_high_leverage(6.0, "Financials") is False
    # D/E <= 5 and not Financials => False
    assert is_high_leverage(4.0, "Industrials") is False
    # D/E is None => False
    assert is_high_leverage(None, "Industrials") is False


def test_interest_coverage_normal():
    # (OP + Other Income) / Interest = (150 + 50) / 10 = 20.0
    assert compute_interest_coverage(150.0, 50.0, 10.0) == 20.0


def test_interest_coverage_debt_free():
    assert compute_interest_coverage(150.0, 50.0, 0.0) is None
    assert get_icr_label(0.0) == "Debt Free"
    assert get_icr_label(10.0) is None


def test_icr_at_risk():
    assert is_icr_at_risk(1.2) is True
    assert is_icr_at_risk(2.0) is False
    assert is_icr_at_risk(None) is False


def test_net_debt():
    assert compute_net_debt(100.0, 30.0) == 70.0
    assert compute_net_debt(0.0, 50.0) == -50.0


def test_asset_turnover():
    assert compute_asset_turnover(200.0, 100.0) == 2.0
    assert compute_asset_turnover(200.0, 0.0) is None
