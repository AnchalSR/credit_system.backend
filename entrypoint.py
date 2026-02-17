#!/usr/bin/env python
"""
Entrypoint: waits for PostgreSQL, runs migrations, then exec's the CMD.
"""

import socket
import sys
import os
import time
import subprocess


def wait_for_postgres(host, port, timeout=30):
    """Block until PostgreSQL accepts connections."""
    print(f"Waiting for PostgreSQL at {host}:{port}...", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, int(port)))
            s.close()
            print("PostgreSQL is ready!", flush=True)
            return True
        except (socket.error, ConnectionRefusedError, OSError):
            time.sleep(1)
    print("Timed out waiting for PostgreSQL!", flush=True)
    return False


if __name__ == "__main__":
    db_host = os.environ.get("DB_HOST", "db")
    db_port = os.environ.get("DB_PORT", "5432")

    if not wait_for_postgres(db_host, db_port):
        sys.exit(1)

    print("Running migrations...", flush=True)
    result = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
    )
    if result.returncode != 0:
        print("Migration failed!", flush=True)
        sys.exit(1)

    # CMD args are passed after the entrypoint script name
    cmd_args = sys.argv[1:]
    if cmd_args:
        print(f"Starting: {' '.join(cmd_args)}", flush=True)
        os.execvp(cmd_args[0], cmd_args)
    else:
        print("No command provided, exiting.", flush=True)
