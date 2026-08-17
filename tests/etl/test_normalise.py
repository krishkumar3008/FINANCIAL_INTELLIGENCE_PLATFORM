import pytest

from src.etl.normaliser import normalize_year

# ----------------------------------------------------
# 20 UNIT TESTS FOR normalize_year()
# ----------------------------------------------------


def test_norm_year_int():
    assert normalize_year(2021) == 2021


def test_norm_year_float():
    assert normalize_year(2021.0) == 2021


def test_norm_year_str_int():
    assert normalize_year("2021") == 2021


def test_norm_year_str_float():
    assert normalize_year("2021.0") == 2021


def test_norm_year_fy_prefix():
    assert normalize_year("FY2021") == 2021


def test_norm_year_fy_space():
    assert normalize_year("FY 2021") == 2021


def test_norm_year_fy_short():
    assert normalize_year("FY21") == 2021


def test_norm_year_fy_short_space():
    assert normalize_year("FY 21") == 2021


def test_norm_year_range_dash():
    assert normalize_year("2021-22") == 2022


def test_norm_year_range_long_dash():
    assert normalize_year("2021-2022") == 2022


def test_norm_year_range_slash():
    assert normalize_year("2021/22") == 2022


def test_norm_year_dec_2012():
    assert normalize_year("Dec 2012") == 2012


def test_norm_year_mar_2014():
    assert normalize_year("Mar 2014") == 2014


def test_norm_year_march_15():
    assert normalize_year("March 15") == 2015


def test_norm_year_dec_dash_12():
    assert normalize_year("Dec-12") == 2012


def test_norm_year_ttm():
    assert normalize_year("TTM") == 9999


def test_norm_year_audited():
    assert normalize_year("2021 (A)") == 2021


def test_norm_year_estimated():
    assert normalize_year("2021 (E)") == 2021


def test_norm_year_invalid_none():
    with pytest.raises(ValueError):
        normalize_year(None)


def test_norm_year_invalid_out_of_range():
    with pytest.raises(ValueError):
        normalize_year(1850)
