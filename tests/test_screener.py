import pandas as pd

from src.screener.engine import (
    apply_screener_filter,
    calculate_composite_score,
    get_screener_universe,
    load_screener_config,
    winsorise_and_scale,
)


def test_load_screener_config():
    config = load_screener_config()
    assert "presets" in config
    assert "quality_compounder" in config["presets"]
    assert "value_pick" in config["presets"]
    assert "growth_accelerator" in config["presets"]
    assert "dividend_champion" in config["presets"]
    assert "debt_free_blue_chip" in config["presets"]
    assert "turnaround_watch" in config["presets"]


def test_winsorise_and_scale():
    s = pd.Series([1, 2, 3, 4, 5, 100, -50])
    scaled = winsorise_and_scale(s, p_low=10, p_high=90, invert=False)
    assert len(scaled) == len(s)
    assert scaled.min() >= 0.0
    assert scaled.max() <= 100.0

    # Test inverse scaling
    scaled_inv = winsorise_and_scale(s, p_low=10, p_high=90, invert=True)
    # The smallest original value should get the highest scaled score
    assert scaled_inv.iloc[-1] > scaled_inv.iloc[5]


def test_screener_universe_loading():
    df = get_screener_universe()
    assert len(df) == 92
    assert "company_id" in df.columns
    assert "return_on_equity_pct" in df.columns
    assert "debt_to_equity" in df.columns
    assert "free_cash_flow_cr" in df.columns
    assert "sales" in df.columns


def test_composite_score_calculation():
    df = get_screener_universe()
    df_scored = calculate_composite_score(df)
    assert "composite_quality_score" in df_scored.columns
    assert "sector_relative_composite_score" in df_scored.columns
    assert df_scored["composite_quality_score"].between(0, 100).all()
    assert df_scored["sector_relative_composite_score"].between(0, 100).all()


def test_de_financials_skip_rule():
    config = load_screener_config()
    df = get_screener_universe()
    df_scored = calculate_composite_score(df)

    # Filter with D/E < 1.0
    filtered = apply_screener_filter(df_scored, "quality_compounder", config)
    fin_companies = filtered[filtered["broad_sector"] == "Financials"]
    # Financial companies should be present even if their D/E > 1.0
    assert len(fin_companies) > 0


def test_icr_infinity_rule():
    config = load_screener_config()
    df = get_screener_universe()
    df_scored = calculate_composite_score(df)

    # Filter with high ICR threshold
    custom_config = {
        "presets": {"icr_test": {"filters": {"interest_coverage_min": 100.0}}}
    }
    filtered = apply_screener_filter(df_scored, "icr_test", custom_config)
    # Debt Free companies (icr_label == 'Debt Free' or interest == 0 or debt_to_equity == 0) must pass
    debt_free_in_result = filtered[
        (filtered["icr_label"] == "Debt Free")
        | (filtered["interest"] == 0)
        | (filtered["debt_to_equity"] == 0)
    ]
    assert len(debt_free_in_result) > 0


def test_all_6_presets_return_between_5_and_50_companies():
    config = load_screener_config()
    df = get_screener_universe()
    df_scored = calculate_composite_score(df)

    preset_keys = [
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ]

    for key in preset_keys:
        res = apply_screener_filter(df_scored, key, config)
        count = len(res)
        assert (
            5 <= count <= 50
        ), f"Preset '{key}' returned {count} companies, which is outside the 5–50 range!"
