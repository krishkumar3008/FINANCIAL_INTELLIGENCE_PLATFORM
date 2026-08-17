from src.analytics.cashflow_kpis import (
    classify_capital_allocation,
    compute_capex_intensity,
    compute_cfo_quality_score,
    compute_fcf_conversion_rate,
    compute_free_cash_flow,
)


def test_fcf_normal():
    assert compute_free_cash_flow(150.0, -50.0) == 100.0
    assert compute_free_cash_flow(100.0, 50.0) == 150.0
    assert compute_free_cash_flow(-50.0, -100.0) == -150.0


def test_cfo_quality_score():
    # Normal case: High Quality (>1.0)
    ratios = [1.2, 1.1, 1.3, 1.4, 1.05]
    avg, label = compute_cfo_quality_score(ratios)
    assert label == "High Quality"
    assert abs(avg - 1.21) < 1e-4

    # Normal case: Moderate (0.5 - 1.0)
    ratios = [0.8, 0.7, 0.9, 0.6, 0.75]
    avg, label = compute_cfo_quality_score(ratios)
    assert label == "Moderate"
    assert abs(avg - 0.75) < 1e-4

    # Normal case: Accrual Risk (<0.5)
    ratios = [0.4, 0.3, 0.2, 0.45, 0.35]
    avg, label = compute_cfo_quality_score(ratios)
    assert label == "Accrual Risk"
    assert abs(avg - 0.34) < 1e-4


def test_cfo_quality_score_edge_cases():
    # Less than 5 years of ratios
    assert compute_cfo_quality_score([1.2, 1.1, 1.3, 1.4]) == (None, None)
    # Ratios containing None
    assert compute_cfo_quality_score([1.2, 1.1, None, 1.4, 1.05]) == (None, None)
    # Empty list
    assert compute_cfo_quality_score([]) == (None, None)


def test_capex_intensity():
    # Asset Light (<3%)
    pct, label = compute_capex_intensity(-20.0, 1000.0)
    assert pct == 2.0
    assert label == "Asset Light"

    # Moderate (3% - 8%)
    pct, label = compute_capex_intensity(-50.0, 1000.0)
    assert pct == 5.0
    assert label == "Moderate"

    # Capital Intensive (>8%)
    pct, label = compute_capex_intensity(-120.0, 1000.0)
    assert pct == 12.0
    assert label == "Capital Intensive"


def test_capex_intensity_zero_sales():
    assert compute_capex_intensity(-50.0, 0.0) == (None, None)


def test_fcf_conversion_rate():
    assert compute_fcf_conversion_rate(100.0, 200.0) == 50.0
    assert compute_fcf_conversion_rate(100.0, 0.0) is None


def test_classify_capital_allocation():
    # (+,-,-) and cfo_pat_avg > 1.0 => Shareholder Returns
    assert (
        classify_capital_allocation(100.0, -50.0, -30.0, cfo_pat_avg=1.2)
        == "Shareholder Returns"
    )
    # (+,-,-) and cfo_pat_avg <= 1.0 => Reinvestor
    assert (
        classify_capital_allocation(100.0, -50.0, -30.0, cfo_pat_avg=0.8)
        == "Reinvestor"
    )
    assert classify_capital_allocation(100.0, -50.0, -30.0) == "Reinvestor"

    # (+,+,-) => Liquidating Assets
    assert classify_capital_allocation(100.0, 50.0, -30.0) == "Liquidating Assets"

    # (-,+,+) => Distress Signal
    assert classify_capital_allocation(-100.0, 50.0, 30.0) == "Distress Signal"

    # (-,-,+) => Growth Funded by Debt
    assert classify_capital_allocation(-100.0, -50.0, 30.0) == "Growth Funded by Debt"

    # (+,+,+) => Cash Accumulator
    assert classify_capital_allocation(100.0, 50.0, 30.0) == "Cash Accumulator"

    # (-,-,-) => Pre-Revenue
    assert classify_capital_allocation(-100.0, -50.0, -30.0) == "Pre-Revenue"

    # (+,-,+) => Mixed
    assert classify_capital_allocation(100.0, -50.0, 30.0) == "Mixed"
