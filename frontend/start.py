#!/usr/bin/env python3
import argparse
import os
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

DEFAULT_PORT = 5500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve the library frontend")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("FRONTEND_PORT", DEFAULT_PORT)),
        help=f"port to listen on (default {DEFAULT_PORT}, env FRONTEND_PORT)",
    )
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    handler = partial(SimpleHTTPRequestHandler, directory=root)
    server = HTTPServer(("127.0.0.1", args.port), handler)

    print(f"Serving frontend | http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
