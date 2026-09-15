import argparse
import datetime
import logging
import os
import sys
import threading
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.automation.daily_pipeline import (
    run_daily_market_close_pipeline,
    is_market_day,
    get_next_scheduled_run_time
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("scheduler_daemon")

_scheduler_thread = None
_stop_event = threading.Event()
_last_run_date = None


def scheduler_worker_loop(db_path: str = "nifty100.db", target_hour: int = 16, target_minute: int = 0):
    """
    Continuous background loop that wakes up periodically, checks if the target time
    (16:00 IST on Monday-Friday) has arrived, and triggers the automated pipeline.
    """
    global _last_run_date
    logger.info(f"Daily Scheduler Daemon active. Target window: {target_hour:02d}:{target_minute:02d} IST (Mon-Fri).")

    while not _stop_event.is_set():
        try:
            now = datetime.datetime.now()
            today = now.date()

            # Check if today is a weekday and current time is at or past target_hour:target_minute
            is_target_time = (now.hour == target_hour and now.minute >= target_minute) or (now.hour > target_hour)
            
            if is_market_day(today) and is_target_time:
                if _last_run_date != today:
                    logger.info(f"Market close window reached for {today}. Launching daily pipeline...")
                    result = run_daily_market_close_pipeline(db_path=db_path, run_type="AUTO_DAEMON")
                    if result.get("status") == "SUCCESS":
                        _last_run_date = today
                        logger.info(f"Daily pipeline finished successfully for {today}. Next run scheduled for next weekday.")
                    else:
                        logger.warning(f"Daily pipeline returned status: {result.get('status')}")

            # Sleep in intervals of 30 seconds to allow clean shutdown
            for _ in range(30):
                if _stop_event.is_set():
                    break
                time.sleep(1)

        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            time.sleep(30)

    logger.info("Scheduler worker loop gracefully stopped.")


def start_background_scheduler(db_path: str = "nifty100.db", target_hour: int = 16, target_minute: int = 0) -> threading.Thread:
    """
    Starts the scheduler loop in a background daemon thread.
    Safe to call during application startup (FastAPI or Streamlit).
    """
    global _scheduler_thread, _stop_event
    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        logger.info("Background scheduler thread is already running.")
        return _scheduler_thread

    _stop_event.clear()
    _scheduler_thread = threading.Thread(
        target=scheduler_worker_loop,
        args=(db_path, target_hour, target_minute),
        name="Nifty100_Daily_Scheduler_Thread",
        daemon=True
    )
    _scheduler_thread.start()
    logger.info(f"Spawned background scheduler daemon thread: {_scheduler_thread.name}")
    return _scheduler_thread


def stop_background_scheduler():
    """Signals the scheduler daemon to stop."""
    global _stop_event
    _stop_event.set()
    logger.info("Signaled background scheduler to stop.")


def main():
    parser = argparse.ArgumentParser(description="Nifty 100 Market Close Scheduler Daemon")
    parser.add_argument("--daemon", action="store_true", help="Run the continuous scheduler process")
    parser.add_argument("--hour", type=int, default=16, help="Target trigger hour in 24h format (default 16)")
    parser.add_argument("--minute", type=int, default=0, help="Target trigger minute (default 0)")
    args = parser.parse_args()

    if args.daemon:
        logger.info(f"Starting standalone scheduler daemon on PID {os.getpid()}...")
        try:
            scheduler_worker_loop(target_hour=args.hour, target_minute=args.minute)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal. Exiting daemon.")
    else:
        next_run = get_next_scheduled_run_time(args.hour, args.minute)
        print(f"\nTarget Run Time: {args.hour:02d}:{args.minute:02d} IST (Monday - Friday)")
        print(f"Next Scheduled Run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print("To launch the background daemon, pass: --daemon\n")


if __name__ == "__main__":
    main()
