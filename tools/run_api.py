#!/usr/bin/env python3
"""Run the non-production ST Score Restore `/api/v1` server."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.durable_job_store import (  # noqa: E402
    DurableStoreError,
    SQLiteJobStore,
)
from st_score_restore.http_api import ApiV1  # noqa: E402
from st_score_restore.http_server import create_server  # noqa: E402
from st_score_restore.job_api_types import JobApiConfig, JobApiError  # noqa: E402
from st_score_restore.job_service import RestorationJobService  # noqa: E402
from st_score_restore.job_store import InMemoryJobStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--retention-seconds", type=int, default=86_400)
    parser.add_argument(
        "--data-dir",
        type=Path,
        help=(
            "Opt in to the durable local SQLite/blob store. Omit this option "
            "to retain the in-memory test/demo store."
        ),
    )
    parser.add_argument(
        "--worker-lease-seconds",
        type=int,
        default=300,
        help="Local durable queue lease length (5-3600 seconds).",
    )
    args = parser.parse_args()

    client_key = os.environ.get("ST_SCORE_CLIENT_API_KEY", "")
    reviewer_key = os.environ.get("ST_SCORE_REVIEWER_API_KEY", "")
    try:
        config = JobApiConfig(
            client_api_key=client_key,
            reviewer_api_key=reviewer_key,
            retention_seconds=args.retention_seconds,
        )
        store = (
            SQLiteJobStore(
                args.data_dir,
                worker_lease_seconds=args.worker_lease_seconds,
            )
            if args.data_dir is not None
            else InMemoryJobStore()
        )
    except (JobApiError, DurableStoreError) as error:
        print(error.message, file=sys.stderr)
        return 2

    service = RestorationJobService(store, config)
    api = ApiV1(service, config)
    server, worker = create_server(args.host, args.port, api, service)
    worker.start()
    storage_label = "durable-local" if args.data_dir is not None else "in-memory"
    print(
        f"ST Score Restore non-production API listening on "
        f"http://{args.host}:{args.port} ({storage_label})",
        file=sys.stderr,
    )
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        worker.stop()
        close = getattr(store, "close", None)
        if callable(close):
            close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
