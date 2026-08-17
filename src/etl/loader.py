import os

import pandas as pd

from src.database import get_db_connection, init_db
from src.etl.normaliser import normalize_ticker, normalize_year
from src.etl.validator import validate_data

# Define source file paths
DATA_DIR = "Dataset"
SUPPORTING_DIR = os.path.join(DATA_DIR, "supporting datasets")

FILES = {
    "companies": (os.path.join(DATA_DIR, "companies.xlsx"), 1),  # (path, header_row)
    "sectors": (os.path.join(SUPPORTING_DIR, "sectors.xlsx"), 0),
    "profitandloss": (os.path.join(DATA_DIR, "profitandloss.xlsx"), 1),
    "balancesheet": (os.path.join(DATA_DIR, "balancesheet.xlsx"), 1),
    "cashflow": (os.path.join(DATA_DIR, "cashflow.xlsx"), 1),
    "financial_ratios": (os.path.join(SUPPORTING_DIR, "financial_ratios.xlsx"), 0),
    "market_cap": (os.path.join(SUPPORTING_DIR, "market_cap.xlsx"), 0),
    "analysis": (os.path.join(DATA_DIR, "analysis.xlsx"), 1),
    "documents": (os.path.join(DATA_DIR, "documents.xlsx"), 1),
    "prosandcons": (os.path.join(DATA_DIR, "prosandcons.xlsx"), 1),
    "peer_groups": (os.path.join(SUPPORTING_DIR, "peer_groups.xlsx"), 0),
    "stock_prices": (os.path.join(SUPPORTING_DIR, "stock_prices.xlsx"), 0),
}


def load_excel_file(table_name: str) -> pd.DataFrame:
    """
    Loads an Excel file and returns a DataFrame.
    """
    file_path, header_row = FILES[table_name]
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_excel(file_path, header=header_row)


def run_etl():
    print("Starting ETL Data Foundation Pipeline...")

    # 1. Initialize Database
    db_path = "nifty100.db"
    init_db(db_path)

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # 2. Ingest Excel sheets into raw DataFrames
    raw_dfs: dict[str, pd.DataFrame] = {}
    for table_name in FILES:
        print(f"Reading source file for table '{table_name}'...")
        raw_dfs[table_name] = load_excel_file(table_name)

    # 3. Clean and Normalise Data
    cleaned_dfs: dict[str, pd.DataFrame] = {}

    # First: Companies (dimension table)
    comp_df = raw_dfs["companies"].copy()
    # Normalize ID/Ticker
    comp_df["id"] = comp_df["id"].apply(normalize_ticker)
    # Deduplicate companies on id (keep first)
    comp_df = comp_df.drop_duplicates(subset=["id"], keep="first")
    cleaned_dfs["companies"] = comp_df

    valid_company_ids = set(comp_df["id"].tolist())
    print(f"Loaded {len(valid_company_ids)} valid company tickers.")

    # Process other tables
    for table_name, df_raw in raw_dfs.items():
        if table_name == "companies":
            continue

        df = df_raw.copy()

        # Normalize ticker
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].apply(normalize_ticker)
            # Filter rows with company_id present in companies
            df = df[df["company_id"].isin(valid_company_ids)]

        # Normalize year if present
        # Note: documents has capital 'Year'
        if "year" in df.columns:
            df["year"] = df["year"].apply(normalize_year)
        elif "Year" in df.columns:
            df["year"] = df["Year"].apply(normalize_year)
            df = df.drop(columns=["Year"])

        # Rename other columns if needed
        if table_name == "documents" and "Annual_Report" in df.columns:
            df = df.rename(columns={"Annual_Report": "annual_report"})

        # Deduplicate on natural primary/composite keys
        if table_name in [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
            "documents",
        ]:
            df = df.drop_duplicates(subset=["company_id", "year"], keep="first")
        elif table_name in ["sectors", "analysis", "prosandcons", "peer_groups"]:
            df = df.drop_duplicates(subset=["company_id"], keep="first")
        elif table_name == "stock_prices":
            df = df.drop_duplicates(subset=["company_id", "date"], keep="first")

        cleaned_dfs[table_name] = df

    # 4. Run Schema Validator (16 DQ Rules) on raw/cleaned datasets
    print("Running Data Quality validation rules...")
    validation_failures = validate_data(
        cleaned_dfs["companies"],
        cleaned_dfs["profitandloss"],
        cleaned_dfs["balancesheet"],
        cleaned_dfs["cashflow"],
        cleaned_dfs["analysis"],
        cleaned_dfs["documents"],
        cleaned_dfs["prosandcons"],
        cleaned_dfs["sectors"],
        cleaned_dfs["stock_prices"],
        cleaned_dfs["financial_ratios"],
        cleaned_dfs["peer_groups"],
        cleaned_dfs["market_cap"],
    )

    # Save validation failures report
    val_fail_path = os.path.join("output", "validation_failures.csv")
    validation_failures.to_csv(val_fail_path, index=False)
    print(f"Validation failures written to: {val_fail_path}")
    print(f"Total DQ rule violations found: {len(validation_failures)}")

    # Check if there are any CRITICAL violations remaining in the cleaned datasets
    critical_failures = validation_failures[
        validation_failures["severity"] == "CRITICAL"
    ]
    if len(critical_failures) > 0:
        print(
            f"CRITICAL validation failures found ({len(critical_failures)}). Loading aborted."
        )
        print(critical_failures.head(10))
        raise ValueError(
            "CRITICAL DQ violations must be resolved before loading database."
        )

    # 5. Load Cleaned Data into SQLite database
    conn = get_db_connection(db_path)
    audit_records = []

    try:
        # Load tables in correct dependency order (companies first)
        load_order = [
            "companies",
            "sectors",
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
            "analysis",
            "documents",
            "prosandcons",
            "peer_groups",
            "stock_prices",
        ]

        for table_name in load_order:
            df = cleaned_dfs[table_name]
            raw_count = len(raw_dfs[table_name])

            # Remove 'id' column from df so SQLite generates auto-incrementing PK
            # except for 'companies' where the ticker is the primary key 'id'
            if table_name != "companies" and "id" in df.columns:
                df_to_insert = df.drop(columns=["id"])
            else:
                df_to_insert = df

            # Perform bulk insert
            df_to_insert.to_sql(table_name, conn, if_exists="append", index=False)

            loaded_count = len(df)
            rejected_count = raw_count - loaded_count

            print(
                f"Loaded table '{table_name}': {loaded_count} rows inserted (original={raw_count}, filtered={rejected_count})."
            )

            audit_records.append(
                {
                    "table_name": table_name,
                    "source_file": FILES[table_name][0],
                    "original_rows": raw_count,
                    "loaded_rows": loaded_count,
                    "rejected_rows": rejected_count,
                    "critical_rejections": 0,  # zero critical failures in loaded data
                    "warning_rejections": rejected_count,
                    "status": "SUCCESS",
                }
            )

        conn.commit()
        print("Data loaded to SQLite database successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Error loading data: {e}")
        raise e
    finally:
        conn.close()

    # Write load audit CSV
    audit_df = pd.DataFrame(audit_records)
    audit_path = os.path.join("output", "load_audit.csv")
    audit_df.to_csv(audit_path, index=False)
    print(f"Load audit written to: {audit_path}")

    # 6. Verify row counts and foreign keys
    conn = get_db_connection(db_path)
    try:
        # Check companies count
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM companies;")
        comp_count = c.fetchone()[0]
        print(
            f"Verification: SELECT COUNT(*) FROM companies = {comp_count} (Expected: 92)"
        )

        # Check foreign key check
        c.execute("PRAGMA foreign_key_check;")
        fk_check = c.fetchall()
        print(
            f"Verification: PRAGMA foreign_key_check returned {len(fk_check)} rows (Expected: 0)"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    run_etl()
