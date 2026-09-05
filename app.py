"""One launcher: python app.py [web|desktop|gradio|export]."""
import argparse
import functools
import http.server
import os
from pathlib import Path
import subprocess
import sys
import webbrowser

ROOT = Path(__file__).resolve().parent

class WebHandler(http.server.SimpleHTTPRequestHandler):
    # Windows registry MIME mappings can incorrectly mark .mjs as text/plain.
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.mjs': 'text/javascript', '.js': 'text/javascript',
                      '.wasm': 'application/wasm', '.onnx': 'application/octet-stream'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", nargs="?", default="web", choices=["web", "desktop", "gradio", "export"])
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args, extra = parser.parse_known_args()
    if args.mode == "web":
        if extra:
            parser.error(f"Unknown web options: {' '.join(extra)}")
        handler = functools.partial(WebHandler, directory=str(ROOT / "docs"))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            url = f"http://localhost:{server.server_port}"
            print(f"ShuttleBot: {url} (Ctrl+C to stop)", flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    else:
        script = {"desktop": "realtime_detect.py", "gradio": "webapp/app.py", "export": "scripts/export_browser_model.py"}[args.mode]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        raise SystemExit(subprocess.call([sys.executable, str(ROOT / script), *extra], cwd=ROOT, env=env))

if __name__ == "__main__":
    main()
