"""PyInstaller entry point for the Curriculum Curator backend.

This script is the target for PyInstaller when building the desktop app.
It starts the FastAPI server via uvicorn with LOCAL_MODE enabled.
"""

import argparse
import multiprocessing
import os
import sys
import tempfile

import uvicorn


def main() -> None:
    multiprocessing.freeze_support()

    # When running as a frozen PyInstaller binary, set up temp directory
    if getattr(sys, "frozen", False):
        os.environ.setdefault("TMPDIR", tempfile.gettempdir())

    parser = argparse.ArgumentParser(description="Curriculum Curator API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()

    # Ensure LOCAL_MODE is set for desktop usage
    os.environ["LOCAL_MODE"] = "true"

    uvicorn.run("app.main:app", host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
