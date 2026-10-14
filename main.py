"""Worker entrypoint: polls the jobs table and runs the pipeline. Run with `python main.py`."""
import logging
import os
import time

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

import db  # noqa: E402  (after load_dotenv)
from pipeline import run_job  # noqa: E402


def main() -> None:
    interval = float(os.getenv("POLL_INTERVAL_SEC", "5"))
    logging.info("Worker started; polling every %.0fs", interval)
    while True:
        job = db.claim_job()
        if job is None:
            time.sleep(interval)
            continue
        run_job(job)


if __name__ == "__main__":
    main()
