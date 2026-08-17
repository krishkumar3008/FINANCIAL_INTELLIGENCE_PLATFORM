import logging
import os

# Setup a logger for ratio engine warnings/anomalies
logger = logging.getLogger("ratio_engine")


def compute_net_profit_margin(net_profit: float, sales: float) -> float | None:
    """
    Net Profit Margin: net_profit / sales * 100
    Returns None if sales == 0.
    """
    if sales == 0:
        return None
    return (net_profit / sales) * 100


def compute_operating_profit_margin(
    operating_profit: float,
    sales: float,
    reported_opm: float | None = None,
    company_id: str | None = None,
    year: int | None = None,
) -> float | None:
    """
    Operating Profit Margin: operating_profit / sales * 100
    Returns None if sales == 0.
    Cross-checks against reported OPM if provided and logs if difference > 1%.
    """
    if sales == 0:
        return None
    computed_opm = (operating_profit / sales) * 100

    if reported_opm is not None:
        diff = abs(computed_opm - reported_opm)
        if diff > 1.0:
            msg = f"OPM cross-check mismatch for {company_id or 'unknown'} in {year or 'unknown'}: computed={computed_opm:.2f}%, reported={reported_opm:.2f}%, diff={diff:.2f}%"
            # Append to log file
            os.makedirs("output", exist_ok=True)
            with open("output/ratio_edge_cases.log", "a", encoding="utf-8") as f:
                f.write(f"[OPM_MISMATCH] {msg}\n")
            logger.warning(msg)

    return computed_opm


def compute_return_on_equity(
    net_profit: float, equity_capital: float, reserves: float
) -> float | None:
    """
    Return on Equity (ROE): net_profit / (equity_capital + reserves) * 100
    Returns None if equity_capital + reserves <= 0.
    """
    equity = equity_capital + reserves
    if equity <= 0:
        return None
    return (net_profit / equity) * 100


def compute_return_on_capital_employed(
    profit_before_tax: float,
    interest: float,
    equity_capital: float,
    reserves: float,
    borrowings: float,
) -> float | None:
    """
    Return on Capital Employed (ROCE): EBIT / (equity + reserves + borrowings) * 100
    where EBIT = profit_before_tax + interest
    Returns None if capital employed (equity + reserves + borrowings) <= 0.
    """
    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        return None
    ebit = profit_before_tax + interest
    return (ebit / capital_employed) * 100


def compute_return_on_assets(net_profit: float, total_assets: float) -> float | None:
    """
    Return on Assets (ROA): net_profit / total_assets * 100
    Returns None if total_assets == 0.
    """
    if total_assets == 0:
        return None
    return (net_profit / total_assets) * 100


def compute_debt_to_equity(
    borrowings: float, equity_capital: float, reserves: float
) -> float | None:
    """
    Debt-to-Equity (D/E): borrowings / (equity_capital + reserves)
    Returns 0.0 if borrowings == 0.
    Returns None if equity_capital + reserves <= 0.
    """
    if borrowings == 0:
        return 0.0
    equity = equity_capital + reserves
    if equity <= 0:
        return None
    return borrowings / equity


def is_high_leverage(
    debt_to_equity: float | None, broad_sector: str | None
) -> bool:
    """
    Add D/E flag: if D/E > 5 and company is NOT in Financials sector — high_leverage_flag = True.
    """
    if debt_to_equity is None:
        return False
    if broad_sector == "Financials":
        return False
    return debt_to_equity > 5.0


def compute_interest_coverage(
    operating_profit: float, other_income: float, interest: float
) -> float | None:
    """
    Interest Coverage Ratio (ICR): (operating_profit + other_income) / interest
    Returns None if interest == 0.
    """
    if interest == 0:
        return None
    return (operating_profit + other_income) / interest


def get_icr_label(interest: float) -> str | None:
    """
    For ICR = None (debt-free companies where interest = 0) — store display label 'Debt Free' in icr_label.
    """
    if interest == 0:
        return "Debt Free"
    return None


def is_icr_at_risk(interest_coverage: float | None) -> bool:
    """
    Add ICR warning flag: if ICR < 1.5 — company is at risk of not covering interest payments.
    """
    if interest_coverage is None:
        return False
    return interest_coverage < 1.5


def compute_net_debt(borrowings: float, investments: float) -> float:
    """
    Net Debt: borrowings - investments (using investments as liquid asset proxy).
    """
    return borrowings - investments


def compute_asset_turnover(sales: float, total_assets: float) -> float | None:
    """
    Asset Turnover: sales / total_assets
    Returns None if total_assets == 0.
    """
    if total_assets == 0:
        return None
    return sales / total_assets
