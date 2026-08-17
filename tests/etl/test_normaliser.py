import pytest

from src.etl.normaliser import normalize_ticker, normalize_year

# ----------------------------------------------------
# 20+ UNIT TESTS FOR normalize_year
# ----------------------------------------------------


def test_normalize_year_int():
    assert normalize_year(2021) == 2021


def test_normalize_year_float():
    assert normalize_year(2021.0) == 2021


def test_normalize_year_str_int():
    assert normalize_year("2021") == 2021


def test_normalize_year_str_float():
    assert normalize_year("2021.0") == 2021


def test_normalize_year_fy_prefix():
    assert normalize_year("FY2021") == 2021


def test_normalize_year_fy_prefix_space():
    assert normalize_year("FY 2021") == 2021


def test_normalize_year_fy_prefix_short():
    assert normalize_year("FY21") == 2021


def test_normalize_year_fy_prefix_short_space():
    assert normalize_year("FY 21") == 2021


def test_normalize_year_range_dash_short():
    assert normalize_year("2021-22") == 2022


def test_normalize_year_range_dash_long():
    assert normalize_year("2021-2022") == 2022


def test_normalize_year_range_dash_short_2digit():
    assert normalize_year("21-22") == 2022


def test_normalize_year_range_slash_short():
    assert normalize_year("2021/22") == 2022


def test_normalize_year_month_year_dec():
    assert normalize_year("Dec 2012") == 2012


def test_normalize_year_month_year_mar():
    assert normalize_year("Mar 2014") == 2014


def test_normalize_year_month_year_full():
    assert normalize_year("March 15") == 2015


def test_normalize_year_month_year_dash():
    assert normalize_year("Dec-12") == 2012


def test_normalize_year_month_year_case():
    assert normalize_year("dec 2012") == 2012


def test_normalize_year_ttm_upper():
    assert normalize_year("TTM") == 9999


def test_normalize_year_ttm_lower():
    assert normalize_year("ttm") == 9999


def test_normalize_year_suffix_audited():
    assert normalize_year("2021 (A)") == 2021


def test_normalize_year_suffix_estimated():
    assert normalize_year("2021 (E)") == 2021


def test_normalize_year_suffix_projected():
    assert normalize_year("2021 (Proj)") == 2021


def test_normalize_year_invalid_none():
    with pytest.raises(ValueError):
        normalize_year(None)


def test_normalize_year_invalid_empty():
    with pytest.raises(ValueError):
        normalize_year("")


def test_normalize_year_invalid_out_of_range():
    with pytest.raises(ValueError):
        normalize_year(1899)
    with pytest.raises(ValueError):
        normalize_year(2101)


def test_normalize_year_invalid_format():
    with pytest.raises(ValueError):
        normalize_year("abcd")


# ----------------------------------------------------
# 15+ UNIT TESTS FOR normalize_ticker
# ----------------------------------------------------


def test_normalize_ticker_simple():
    assert normalize_ticker("ABB") == "ABB"


def test_normalize_ticker_lowercase():
    assert normalize_ticker("abb") == "ABB"


def test_normalize_ticker_whitespace():
    assert normalize_ticker("   ABB   ") == "ABB"


def test_normalize_ticker_suffix_ns():
    assert normalize_ticker("ABB.NS") == "ABB"


def test_normalize_ticker_suffix_bo():
    assert normalize_ticker("ABB.BO") == "ABB"


def test_normalize_ticker_suffix_ns_slash():
    assert normalize_ticker("ABB/NS") == "ABB"


def test_normalize_ticker_suffix_bo_slash():
    assert normalize_ticker("ABB/BO") == "ABB"


def test_normalize_ticker_numeric():
    assert normalize_ticker("500002") == "500002"


def test_normalize_ticker_hyphen():
    assert normalize_ticker("M-M") == "M-M"


def test_normalize_ticker_ampersand():
    assert normalize_ticker("L&T") == "L&T"


def test_normalize_ticker_complex_lowercase():
    assert normalize_ticker("adaniensol.ns") == "ADANIENSOL"


def test_normalize_ticker_invalid_none():
    with pytest.raises(ValueError):
        normalize_ticker(None)


def test_normalize_ticker_invalid_empty():
    with pytest.raises(ValueError):
        normalize_ticker("")


def test_normalize_ticker_invalid_whitespace():
    with pytest.raises(ValueError):
        normalize_ticker("   ")


def test_normalize_ticker_invalid_chars():
    with pytest.raises(ValueError):
        normalize_ticker("ABB$")


def test_normalize_ticker_invalid_dot_middle():
    with pytest.raises(ValueError):
        normalize_ticker("A.B.C")
