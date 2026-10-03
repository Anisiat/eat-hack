"""
app.py - PopUpPick: run the whole Pop-up Pick workflow, then serve the website.

    python app.py                  rebuild data, run the model, open http://localhost:8000
    python app.py --no-rebuild     skip the data build and model, just serve the current outputs/
    python app.py --fetch-events   also pull fresh events from PredictHQ first (needs PREDICTHQ_TOKEN in .env)
    python app.py --port 8001      serve on another port
    python app.py --export site    write a static copy of the website to site/ (for Vercel or any static host)

The workflow, in order (each step reads the files the previous one wrote; see README "Pipeline"):
  1. scripts/get_raw_event_data.py        PredictHQ pull -> data/raw/events_raw.pkl      (only with --fetch-events)
  2. scripts/get_event_archetypes.py      events -> data/archetypes/events_archetypes.csv
  3. scripts/get_product_archetypes.py    brand sheet -> data/archetypes/products_archetypes.csv
  4. scripts/build_event_types.py         -> data/processed/event_types.csv
  5. scripts/build_brand_features.py      -> data/processed/brand_products.csv, brand_features.csv
  6. scripts/generate_popups.py           synthetic pop-up history -> data/synthetic/popups.csv, popup_brands.csv
  7. scripts/generate_watchhumans_data.py synthetic users and reviews -> data/synthetic/users.csv, reviews.csv
  8. python -m model.run                  the recommender -> outputs/*.json, outputs/scores.csv

The website (app/) reads outputs/ and data/processed/brand_products.csv and calculates nothing itself.
The server only serves files from app/, outputs/, data/processed/ and design/, and only listens on this machine.
"""
import argparse
import csv
import io
import json
import mimetypes
import shutil
import subprocess
import sys
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
SERVED = {"app": ROOT / "app", "outputs": OUTPUTS, "data/processed": ROOT / "data" / "processed",
          "design": ROOT / "design"}
STEPS = [
    ("Score events on archetypes", ["scripts/get_event_archetypes.py"]),
    ("Score products on archetypes", ["scripts/get_product_archetypes.py"]),
    ("Build event types", ["scripts/build_event_types.py"]),
    ("Build brand and product tables", ["scripts/build_brand_features.py"]),
    ("Generate synthetic pop-up history", ["scripts/generate_popups.py"]),
    ("Generate synthetic users and reviews", ["scripts/generate_watchhumans_data.py"]),
    ("Run the model", ["-m", "model.run"]),
]
REQUEST_FIELDS = ["brand", "product", "units", "event", "date", "popup_code"]
# what a static copy needs: the site, the model outputs it reads, and only the brand assets it shows
EXPORT_FILES = ["outputs/lineups.json", "outputs/event_audience.json", "outputs/impact.json",
                "outputs/month_plan.json", "outputs/scores.csv", "data/processed/brand_features.csv",
                "design/rgc-brand-reference/tokens.css", "design/rgc-brand-reference/assets/rgc-logo.png",
                "design/rgc-brand-reference/assets/star-3d.webp", "design/rgc-brand-reference/assets/chain.webp",
                "design/rgc-brand-reference/assets/favicon-32x32.png"]
EXPORT_MARKER = ".popuppick-export"


def export_static(dest):
    """Write a static copy of the website: same paths as the local server, index.html at the root.
    The request-list export still downloads a CSV; only the save to outputs/requests.csv needs the server."""
    dest = Path(dest).resolve()
    if dest == ROOT or ROOT in dest.parents and dest.parent != ROOT:
        raise SystemExit("Export to a new folder directly inside the repo, e.g. site/")
    if dest.exists():
        if not (dest / EXPORT_MARKER).exists():
            raise SystemExit(f"{dest} exists and isn't a PopUpPick export; choose another folder")
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "app", dest / "app")
    shutil.copy2(ROOT / "app" / "index.html", dest / "index.html")
    for rel in EXPORT_FILES:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest / rel)
    (dest / EXPORT_MARKER).write_text("Static PopUpPick export, rebuilt by: python app.py --export\n")
    size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
    print(f"Exported the PopUpPick website to {dest} ({size / 1e6:.1f} MB)")


def run_workflow(fetch_events):
    steps = ([("Pull events from PredictHQ", ["scripts/get_raw_event_data.py"])] if fetch_events else []) + STEPS
    for n, (label, args) in enumerate(steps, 1):
        print(f"[{n}/{len(steps)}] {label}", flush=True)
        result = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout[-2000:], result.stderr[-4000:], sep="\n")
            raise SystemExit(f"Step failed: {label}")
        lines = [line for line in result.stdout.strip().splitlines() if line.strip()]
        summary = [ln for ln in lines if ln.split(" ", 1)[0] in ("Processed", "Scored", "Wrote", "Saved")]
        if summary or lines:
            print("      " + (summary or lines)[-1][:160], flush=True)


class Handler(SimpleHTTPRequestHandler):
    """Serves the site and its data files read-only, plus one endpoint that saves the request list."""

    def log_message(self, fmt, *args):          # keep the console quiet
        pass

    def _resolve(self, url_path):
        path = unquote(urlparse(url_path).path).lstrip("/")
        if path in ("", "index.html"):
            return SERVED["app"] / "index.html"
        for prefix, folder in sorted(SERVED.items(), key=lambda kv: -len(kv[0])):
            if path == prefix or path.startswith(prefix + "/"):
                target = (folder / path[len(prefix):].lstrip("/")).resolve()
                if folder.resolve() in target.parents or target == folder.resolve():
                    return target
        return None

    def do_GET(self):
        target = self._resolve(self.path)
        if target is None or not target.is_file():
            self.send_error(404, "Not found")
            return
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlparse(self.path).path != "/api/requests":
            self.send_error(404, "Not found")
            return
        try:
            rows = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"[]")
            assert isinstance(rows, list) and len(rows) <= 1000
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=REQUEST_FIELDS, extrasaction="ignore")
            writer.writeheader()
            for r in rows:
                writer.writerow({k: str(r.get(k, ""))[:200] for k in REQUEST_FIELDS})
            (OUTPUTS / "requests.csv").write_text(buf.getvalue())
            body = json.dumps({"saved": "outputs/requests.csv", "rows": len(rows),
                               "at": datetime.now().isoformat(timespec="seconds")}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, AssertionError):
            self.send_error(400, "Expected a JSON list of request rows")


def main():
    ap = argparse.ArgumentParser(description="Run the Pop-up Pick workflow and serve the PopUpPick website.")
    ap.add_argument("--no-rebuild", action="store_true", help="serve the current outputs without rebuilding")
    ap.add_argument("--fetch-events", action="store_true", help="pull fresh events from PredictHQ first")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true", help="don't open a browser tab")
    ap.add_argument("--export", metavar="DIR", help="write a static copy of the website to DIR and exit")
    args = ap.parse_args()

    if args.export:
        if not args.no_rebuild and not (OUTPUTS / "lineups.json").exists():
            run_workflow(args.fetch_events)
        export_static(args.export)
        return

    if not args.no_rebuild:
        run_workflow(args.fetch_events)
    missing = [f for f in ("lineups.json", "event_audience.json", "impact.json", "month_plan.json", "scores.csv")
               if not (OUTPUTS / f).exists()]
    if missing:
        raise SystemExit(f"Missing outputs {missing}: run without --no-rebuild first")

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://localhost:{args.port}/"
    print(f"\nPopUpPick is running at {url}  (Ctrl+C to stop)", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
