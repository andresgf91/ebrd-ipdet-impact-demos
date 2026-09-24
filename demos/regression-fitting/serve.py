#!/usr/bin/env python3
"""Serve this folder on Railway's PORT. Stdlib only."""

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def main() -> None:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"serving regression-fitting on {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
