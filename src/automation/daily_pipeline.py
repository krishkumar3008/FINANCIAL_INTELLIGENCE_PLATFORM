import argparse
import datetime
import logging
import os
import sys
import time

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.database import get_db_connection
from src.etl.live_updater import fetch_and_update_prices

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("daily_pipeline")


def is_market_day(target_date: datetime.date = None) -> bool:
    """Returns True if the date is a weekday (Monday-Friday)."""
    if target_date is None:
        target_date = datetime.date.today()
    # 0 = Monday, 4 = Friday, 5 = Saturday, 6 = Sunday
    return target_date.weekday() < 5


def get_next_scheduled_run_time(hour: int = 16, minute: int = 0) -> datetime.datetime:
    """
    Calculates the next scheduled run datetime (defaults to 16:00 IST Monday-Friday).
    """
    now = datetime.datetime.now()
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If today is a weekday and target time hasn't passed today:
    if candidate > now and is_market_day(candidate.date()):
        return candidate

    # Otherwise, step forward day by day until next weekday 16:00
    candidate = candidate + datetime.timedelta(days=1)
    while not is_market_day(candidate.date()):
        candidate = candidate + datetime.timedelta(days=1)

    return candidate


def run_daily_market_close_pipeline(
    db_path: str = "nifty100.db",
    force: bool = False,
    run_type: str = "AUTO_MARKET_CLOSE"
) -> dict:
    """
    Executes the full automated daily pipeline:
    1. Validates market day (unless force=True).
    2. Records execution start in scheduler_run_log.
    3. Downloads latest daily prices via Yahoo Finance and updates SQLite stock_prices.
    4. Computes next-day ML predictions for all constituent companies.
    5. Saves predictions to daily_predictions table.
    6. Updates scheduler_run_log with execution summary and duration.
    """
    start_time = time.time()
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    today = now_dt.date()

    if not is_market_day(today) and not force:
        logger.info(f"Skipping daily pipeline for {today}: Market is closed on weekends (use --force to override).")
        return {
            "status": "SKIPPED_WEEKEND",
            "message": f"Market closed on weekend ({today.strftime('%A')}). No pipeline run required.",
            "run_timestamp": now_str
        }

    conn = get_db_connection(db_path)
    log_id = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scheduler_run_log (run_timestamp, run_type, status, records_updated, predictions_generated, duration_seconds)
            VALUES (?, ?, 'RUNNING', 0, 0, 0.0)
            """,
            (now_str, run_type)
        )
        conn.commit()
        log_id = cursor.lastrowid
    except Exception as e:
        logger.error(f"Failed to record pipeline start in database: {e}")
    finally:
        conn.close()

    logger.info(f"=== Starting Daily Market Close Pipeline ({now_str}) [Type: {run_type}] ===")

    try:
        # Step 1: Ingest latest stock prices (from last 15 days up to today)
        start_date = (today - datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        logger.info(f"Step 1/2: Fetching market prices from {start_date}...")
        records_updated = fetch_and_update_prices(db_path=db_path, start_date=start_date)
        logger.info(f"Market prices updated: {records_updated} price rows synced.")

        # Step 2: Batch generate and save predictions for all constituent companies
        logger.info("Step 2/2: Training models and computing next-day market forecasts...")
        try:
            from src.analytics.predictor import batch_generate_and_save_predictions
            pred_summary = batch_generate_and_save_predictions(db_path=db_path)
        except Exception as pred_err:
            logger.warning(f"batch_generate_and_save_predictions could not complete: {pred_err}")
            pred_summary = {"saved_count": 0}
        predictions_saved = pred_summary.get("saved_count", 0)

        duration = round(time.time() - start_time, 2)
        logger.info(f"=== Daily Pipeline Complete in {duration}s! Generated {predictions_saved} predictions. ===")

        # Update log to SUCCESS
        if log_id:
            conn = get_db_connection(db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE scheduler_run_log
                    SET status='SUCCESS', records_updated=?, predictions_generated=?, duration_seconds=?
                    WHERE id=?
                    """,
                    (records_updated, predictions_saved, duration, log_id)
                )
                conn.commit()
            finally:
                conn.close()

        return {
            "status": "SUCCESS",
            "run_timestamp": now_str,
            "records_updated": records_updated,
            "predictions_generated": predictions_saved,
            "duration_seconds": duration,
            "next_scheduled_run": get_next_scheduled_run_time().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        err_msg = str(e)
        logger.error(f"Daily pipeline execution failed: {err_msg}", exc_info=True)

        if log_id:
            conn = get_db_connection(db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE scheduler_run_log
                    SET status='FAILED', error_message=?, duration_seconds=?
                    WHERE id=?
                    """,
                    (err_msg, duration, log_id)
                )
                conn.commit()
            finally:
                conn.close()

        return {
            "status": "FAILED",
            "run_timestamp": now_str,
            "error_message": err_msg,
            "duration_seconds": duration
        }


def get_scheduler_status(db_path: str = "nifty100.db") -> dict:
    """
    Returns the current status of the daily pipeline, latest run metadata,
    and next scheduled execution time.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        last_log = cursor.execute(
            """
            SELECT * FROM scheduler_run_log
            ORDER BY id DESC LIMIT 1
            """
        ).fetchone()

        pred_stats = cursor.execute(
            """
            SELECT MAX(prediction_date) as latest_date, COUNT(*) as cnt
            FROM daily_predictions
            """
        ).fetchone()

        last_run = dict(last_log) if last_log else None
        latest_pred_date = pred_stats["latest_date"] if pred_stats else None
        total_cached = pred_stats["cnt"] if pred_stats else 0

        next_run = get_next_scheduled_run_time()

        return {
            "is_market_day_today": is_market_day(),
            "latest_prediction_date": latest_pred_date,
            "total_cached_predictions": total_cached,
            "last_run": last_run,
            "next_scheduled_run": next_run.strftime("%Y-%m-%d %H:%M:%S"),
            "schedule_window": "16:00 IST (Monday - Friday)"
        }
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Nifty 100 Automated Daily Pipeline")
    parser.add_argument("--now", action="store_true", help="Execute the pipeline immediately")
    parser.add_argument("--force", action="store_true", help="Force pipeline execution even on weekends/holidays")
    parser.add_argument("--status", action="store_true", help="Print current scheduler status")
    args = parser.parse_args()

    if args.status:
        status = get_scheduler_status()
        print("\n=== NIFTY 100 AUTOMATION STATUS ===")
        for k, v in status.items():
            print(f"  {k}: {v}")
        print("===================================\n")
        return

    if args.now or args.force:
        result = run_daily_market_close_pipeline(force=args.force, run_type="MANUAL_CLI")
        print("\n=== PIPELINE EXECUTION RESULT ===")
        for k, v in result.items():
            print(f"  {k}: {v}")
        print("=================================\n")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
