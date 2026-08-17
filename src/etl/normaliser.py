import re
from typing import Any


def normalize_year(year_val: Any) -> int:
    """
    Normalizes a year value to a standard 4-digit financial year integer.
    Supports:
      - Integers/Floats: 2021, 2021.0 -> 2021
      - Strings: "2021", "2021.0" -> 2021
      - Prefixed strings: "FY2021", "FY 2021", "FY21", "FY 21" -> 2021
      - Fiscal range strings: "2021-22", "2021-2022", "21-22", "2021/22" -> 2022 (end year)
      - Month-Year strings: "Dec 2012", "Mar 2014", "March 15", "Dec-12" -> 2012, 2014, 2015, 2012
      - "TTM" -> 9999 (placeholder for Trailing Twelve Months)
    Raises ValueError for invalid inputs.
    """
    if year_val is None:
        raise ValueError("Year value cannot be None")

    # If already integer (and within reasonable range)
    if isinstance(year_val, int):
        if 1900 <= year_val <= 2100 or year_val == 9999:
            return year_val
        raise ValueError(f"Year {year_val} out of valid range (1900-2100)")

    # If float (like 2021.0)
    if isinstance(year_val, float):
        if year_val.is_integer():
            int_val = int(year_val)
            if 1900 <= int_val <= 2100 or int_val == 9999:
                return int_val
            raise ValueError(f"Year {int_val} out of valid range (1900-2100)")
        raise ValueError(f"Year float {year_val} is not an integer representation")

    # If it is a string
    val_str = str(year_val).strip()
    if not val_str:
        raise ValueError("Year string cannot be empty")

    # Case: TTM
    if val_str.upper() == "TTM":
        return 9999

    # Remove any projection suffixes like "(A)", "(E)", "(Proj)", etc.
    val_str = re.sub(r"\s*\(.*?\)", "", val_str).strip()

    # Match FY prefixes like "FY2021", "FY 2021", "FY21", "FY 21"
    fy_match = re.match(r"^FY\s*(\d{2,4})$", val_str, re.IGNORECASE)
    if fy_match:
        digits = fy_match.group(1)
        if len(digits) == 2:
            return 2000 + int(digits)
        elif len(digits) == 4:
            return int(digits)
        raise ValueError(f"Invalid FY suffix length in: {val_str}")

    # Match range years like "2021-22", "2021-2022", "21-22", "2021/22"
    range_match = re.match(r"^(\d{2,4})[-/](\d{2,4})$", val_str)
    if range_match:
        start_digits = range_match.group(1)
        end_digits = range_match.group(2)
        if len(end_digits) == 2:
            # e.g. "2021-22" -> ending in 2022
            # determine prefix from start
            prefix = "20"
            if len(start_digits) == 4:
                prefix = start_digits[:2]
            return int(prefix + end_digits)
        elif len(end_digits) == 4:
            return int(end_digits)
        raise ValueError(f"Invalid range end year length in: {val_str}")

    # Match month-year formats like "Dec 2012", "Mar 2014", "March 15", "Dec-12", "Mar 2023 15", "Mar 2016 9m"
    month_pattern = r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[- ]?(\d{4}|\d{2})(?:\s+.*)?$"
    month_match = re.match(month_pattern, val_str, re.IGNORECASE)
    if month_match:
        year_part = month_match.group(2)
        if len(year_part) == 2:
            return 2000 + int(year_part)
        elif len(year_part) == 4:
            return int(year_part)

    # Match simple 4-digit or 2-digit years
    digit_match = re.match(r"^(\d{2,4})(?:\.0+)?$", val_str)
    if digit_match:
        digits = digit_match.group(1)
        if len(digits) == 4:
            val_int = int(digits)
            if 1900 <= val_int <= 2100:
                return val_int
        elif len(digits) == 2:
            return 2000 + int(digits)

    raise ValueError(f"Unable to parse/normalize year: {year_val}")


def normalize_ticker(ticker_val: Any) -> str:
    """
    Normalizes stock tickers:
      - Strips exchange suffixes like '.NS', '.BO', '/NS', '/BO'
      - Converts to uppercase
      - Strips whitespace
    Raises ValueError for empty or invalid tickers.
    """
    if ticker_val is None:
        raise ValueError("Ticker value cannot be None")

    val_str = str(ticker_val).strip()
    if not val_str:
        raise ValueError("Ticker string cannot be empty")

    # Convert to uppercase
    val_str = val_str.upper()

    # Strip common exchange suffixes
    val_str = re.sub(r"\.(NS|BO)$", "", val_str)
    val_str = re.sub(r"/(NS|BO)$", "", val_str)

    # Verify the ticker contains only alphanumeric characters (e.g. no special characters except maybe & or -)
    if not re.match(r"^[A-Z0-9&-]+$", val_str):
        raise ValueError(f"Ticker contains invalid characters: {ticker_val}")

    return val_str
