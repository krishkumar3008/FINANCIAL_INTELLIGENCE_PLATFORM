import random

from src.database import get_db_connection


def run_manual_review():
    print("=== Day 06: Data Quality Manual Review ===")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch all loaded companies
    cursor.execute("SELECT id, company_name FROM companies;")
    companies = cursor.fetchall()
    print(f"Total companies loaded: {len(companies)}")

    # 2. Pick 5 random companies for detailed review
    print("\n--- Reviewing 5 Random Companies ---")
    random.seed(42)  # for reproducibility
    sampled_companies = random.sample(companies, 5)

    for comp in sampled_companies:
        comp_id = comp["id"]
        name = comp["company_name"]
        print(f"\nCompany: {name} ({comp_id})")

        # P&L year coverage (excluding 9999 placeholder for TTM)
        cursor.execute(
            "SELECT year FROM profitandloss WHERE company_id = ? AND year != 9999 ORDER BY year;",
            (comp_id,),
        )
        pl_years = [row["year"] for row in cursor.fetchall()]

        # Balance Sheet year coverage
        cursor.execute(
            "SELECT year FROM balancesheet WHERE company_id = ? AND year != 9999 ORDER BY year;",
            (comp_id,),
        )
        bs_years = [row["year"] for row in cursor.fetchall()]

        # Cash Flow year coverage
        cursor.execute(
            "SELECT year FROM cashflow WHERE company_id = ? AND year != 9999 ORDER BY year;",
            (comp_id,),
        )
        cf_years = [row["year"] for row in cursor.fetchall()]

        # Stock prices date range
        cursor.execute(
            "SELECT MIN(date), MAX(date), COUNT(*) FROM stock_prices WHERE company_id = ?;",
            (comp_id,),
        )
        min_date, max_date, price_count = cursor.fetchone()

        print(f"  P&L Financial Years ({len(pl_years)}): {pl_years}")
        print(f"  Balance Sheet Financial Years ({len(bs_years)}): {bs_years}")
        print(f"  Cash Flow Financial Years ({len(cf_years)}): {cf_years}")
        print(
            f"  Stock Price Date Range: {min_date} to {max_date} ({price_count} price points)"
        )

    # 3. Companies with < 5 years of financial data in P&L
    print("\n--- Companies with < 5 Years of Data in P&L ---")
    cursor.execute("""
        SELECT company_id, COUNT(year) as yr_count 
        FROM profitandloss 
        WHERE year != 9999 
        GROUP BY company_id 
        HAVING yr_count < 5;
    """)
    under_represented = cursor.fetchall()
    if len(under_represented) == 0:
        print("All companies have at least 5 years of financial data.")
    else:
        print(
            f"Found {len(under_represented)} companies with less than 5 years of data:"
        )
        for row in under_represented:
            print(f"  - {row['company_id']}: {row['yr_count']} years")

    # 4. Overall Year Coverage Summary
    print("\n--- Overall Financial Year Coverage Summary (P&L) ---")
    cursor.execute("""
        SELECT year, COUNT(company_id) as comp_count 
        FROM profitandloss 
        GROUP BY year 
        ORDER BY year;
    """)
    year_summary = cursor.fetchall()
    for row in year_summary:
        yr_label = "TTM" if row["year"] == 9999 else str(row["year"])
        print(f"  Year {yr_label}: {row['comp_count']} companies")

    conn.close()


if __name__ == "__main__":
    run_manual_review()
