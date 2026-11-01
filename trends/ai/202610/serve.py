"""Serve the report and allowlisted October newsletters on loopback only."""

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
NEWSLETTERS = HERE.parents[2] / "newsletters" / HERE.parent.name  # trends/<주제>/YYYYMM


class ReportHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path.startswith("/source/"):
            name = path.removeprefix("/source/")
            allowed = json.loads((HERE / "corpus.json").read_text(encoding="utf-8"))["files"]
            if name not in allowed:
                self.send_error(404, "Newsletter not in this report")
                return
            try:
                content = (NEWSLETTERS / name).read_bytes()
            except FileNotFoundError:
                self.send_error(404, "Newsletter file not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404, "Directory listing disabled")
        return None


def main():
    parser = argparse.ArgumentParser(description="Run the October AI trend report locally.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    handler = partial(ReportHandler, directory=str(HERE))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as error:
        raise SystemExit(f"Cannot open port {args.port}: {error}\nTry --port 8766.") from error
    print(f"AI SIGNAL: http://127.0.0.1:{args.port}", flush=True)
    print("Press Ctrl+C to stop. No installation required.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
