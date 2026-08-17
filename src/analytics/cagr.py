

def compute_cagr(
    start_val: float | None, end_val: float | None, n: int
) -> tuple[float | None, str | None]:
    """
    Computes CAGR: ((end / start) ** (1 / n) - 1) * 100

    Handles all 6 CAGR edge cases:
    1. Positive + Positive: compute normally, returns (cagr, None)
    2. Positive + Negative/Zero: return (None, "DECLINE_TO_LOSS")
    3. Negative + Positive: return (None, "TURNAROUND")
    4. Negative + Negative/Zero: return (None, "BOTH_NEGATIVE")
    5. Zero base: return (None, "ZERO_BASE")
    6. Less than n years (or missing values): return (None, "INSUFFICIENT")
    """
    if start_val is None or end_val is None or n <= 0:
        return None, "INSUFFICIENT"

    if start_val == 0:
        return None, "ZERO_BASE"

    if start_val > 0:
        if end_val > 0:
            cagr = ((end_val / start_val) ** (1 / n) - 1) * 100
            return cagr, None
        else:
            return None, "DECLINE_TO_LOSS"
    else:
        # start_val < 0
        if end_val > 0:
            return None, "TURNAROUND"
        else:
            return None, "BOTH_NEGATIVE"
