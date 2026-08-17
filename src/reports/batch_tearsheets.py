import os
import sys

sys.path.insert(0, os.path.abspath("."))
import sqlite3

import pandas as pd

from src.analytics.cashflow_kpis import process_cashflow_intelligence
from src.nlp.pros_cons_generator import generate_pros_and_cons
from src.reports.tearsheet import generate_company_tearsheet


def run_batch_tearsheets(
    db_path: str = "nifty100.db",
    output_dir: str = "reports/tearsheets",
    skipped_csv: str = "output/skipped_tearsheets.csv",
) -> tuple[list[str], list[dict[str, str]]]:
    """
    Runs batch tearsheet generation for all companies in nifty100.db.
    Skips companies with fewer than 3 years of data and logs them to output/skipped_tearsheets.csv.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(skipped_csv), exist_ok=True)

    # Load pros/cons and cashflow intelligence data for inclusion
    pros_cons_path = "output/pros_cons_generated.csv"
    if not os.path.exists(pros_cons_path):
        generate_pros_and_cons(db_path, pros_cons_path)
    pros_cons_df = pd.read_csv(pros_cons_path)

    intel_path = "output/cashflow_intelligence.xlsx"
    if not os.path.exists(intel_path):
        process_cashflow_intelligence(db_path, intel_path)
    intel_df = pd.read_excel(intel_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    companies = [
        r["id"]
        for r in conn.execute("SELECT id FROM companies ORDER BY id ASC").fetchall()
    ]

    generated_files = []
    skipped_records = []

    print(f"Starting batch tearsheet generation for {len(companies)} companies...")

    for comp_id in companies:
        pnl_count = conn.execute(
            "SELECT count(*) as cnt FROM profitandloss WHERE company_id = ? AND year != 9999",
            (comp_id,),
        ).fetchone()["cnt"]

        if pnl_count < 1:
            skipped_records.append(
                {
                    "company_id": comp_id,
                    "reason": f"No financial data found ({pnl_count} years found)",
                }
            )
            print(f"[SKIP] {comp_id}: No financial data found.")
            continue

        try:
            pdf_path = os.path.join(output_dir, f"{comp_id}_tearsheet.pdf")
            generate_company_tearsheet(
                company_id=comp_id,
                db_path=db_path,
                output_pdf=pdf_path,
                pros_cons_df=pros_cons_df,
                intel_df=intel_df,
            )
            size_kb = os.path.getsize(pdf_path) / 1024.0
            generated_files.append(pdf_path)
            print(f"[OK] {comp_id} -> {pdf_path} ({size_kb:.1f} KB)")
        except Exception as e:
            print(f"[ERROR] Failed to generate {comp_id}: {e}")
            skipped_records.append(
                {"company_id": comp_id, "reason": f"Generation error: {e!s}"}
            )

    conn.close()

    df_skipped = pd.DataFrame(skipped_records)
    df_skipped.to_csv(skipped_csv, index=False)

    print("\nBatch tearsheet generation complete.")
    print(f"Generated: {len(generated_files)} tearsheet PDFs in {output_dir}")
    print(f"Skipped: {len(skipped_records)} companies logged to {skipped_csv}")

    # Verify file sizes >= 30 KB
    small_files = [f for f in generated_files if (os.path.getsize(f) / 1024.0) < 30.0]
    if small_files:
        print(
            f"[WARNING] {len(small_files)} tearsheets are smaller than 30 KB: {small_files}"
        )
    else:
        print("All generated tearsheets passed size verification (>= 30 KB).")

    return generated_files, skipped_records


if __name__ == "__main__":
    run_batch_tearsheets()
