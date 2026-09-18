#!/usr/bin/env python3
"""
HTTP wrapper that lets the Alert-client cron run as a Serverless Container.

Scaleway Serverless Containers require an HTTP listener (port 8080) so that a
CRON trigger can invoke the container. On each HTTP request we run
main.main() (the sync logic) exactly once and reply with an HTTP status;
a non-zero return code is mapped to HTTP 500 so a failed run is visible in
the trigger/logs.

All log output produced by main.py during the run is captured and returned in
the HTTP response body for easy diagnosis.
"""
import contextlib
import io
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import main

logger = logging.getLogger("alert-container")


class _Buffer:
    def __init__(self):
        self.buf = io.StringIO()

    def write(self, data):
        self.buf.write(data)

    def flush(self):
        pass


def run_sync():
    """Run main.main() and return (rc, captured_logs)."""
    captured = _Buffer()
    handler = logging.StreamHandler(captured)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root = logging.getLogger()
    root.addHandler(handler)
    rc = -1
    try:
        with contextlib.redirect_stdout(captured), \
             contextlib.redirect_stderr(captured):
            try:
                rc = main.main()
            except SystemExit as exc:  # main() calls exit(1) on failure
                rc = int(exc.code or 0)
    except Exception as exc:  # noqa: BLE001 - report and surface as 500
        captured.buf.write("UNCAUGHT EXCEPTION: %r\n" % (exc,))
        rc = -1
    finally:
        root.removeHandler(handler)
    if rc is None:  # main() returns None on success
        rc = 0
    return rc, captured.buf.getvalue()


class SyncHandler(BaseHTTPRequestHandler):
    def _run(self):
        rc, logs = run_sync()
        logger.info("sync finished rc=%s", rc)
        body = ("rc=%s\n%s" % (rc, logs)).encode()
        code = 200 if rc == 0 else 500
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = _run
    do_POST = _run

    def log_message(self, *args):  # silence default request logging
        logger.debug("request: %s", args)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    logger.info("starting alert-container http listener on port %s", port)
    HTTPServer(("0.0.0.0", port), SyncHandler).serve_forever()
