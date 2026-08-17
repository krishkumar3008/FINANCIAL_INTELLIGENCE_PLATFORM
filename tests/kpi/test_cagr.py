from src.analytics.cagr import compute_cagr


def test_cagr_normal_positive_positive():
    # start = 100, end = 200, n = 5
    # CAGR = ((200/100)**0.2 - 1) * 100 = 14.8698...
    cagr, flag = compute_cagr(100.0, 200.0, 5)
    assert flag is None
    assert cagr is not None
    assert abs(cagr - 14.86983) < 1e-4


def test_cagr_normal_flat():
    cagr, flag = compute_cagr(100.0, 100.0, 3)
    assert flag is None
    assert cagr == 0.0


def test_cagr_decline_to_loss_negative():
    cagr, flag = compute_cagr(100.0, -10.0, 5)
    assert cagr is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_decline_to_loss_zero():
    cagr, flag = compute_cagr(100.0, 0.0, 5)
    assert cagr is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_turnaround():
    cagr, flag = compute_cagr(-50.0, 100.0, 5)
    assert cagr is None
    assert flag == "TURNAROUND"


def test_cagr_both_negative():
    cagr, flag = compute_cagr(-50.0, -100.0, 5)
    assert cagr is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_both_negative_zero():
    cagr, flag = compute_cagr(-50.0, 0.0, 5)
    assert cagr is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_zero_base():
    cagr, flag = compute_cagr(0.0, 100.0, 5)
    assert cagr is None
    assert flag == "ZERO_BASE"


def test_cagr_insufficient_start_none():
    cagr, flag = compute_cagr(None, 100.0, 5)
    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_cagr_insufficient_end_none():
    cagr, flag = compute_cagr(100.0, None, 5)
    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_cagr_insufficient_invalid_n():
    cagr, flag = compute_cagr(100.0, 200.0, 0)
    assert cagr is None
    assert flag == "INSUFFICIENT"

    cagr, flag = compute_cagr(100.0, 200.0, -3)
    assert cagr is None
    assert flag == "INSUFFICIENT"
