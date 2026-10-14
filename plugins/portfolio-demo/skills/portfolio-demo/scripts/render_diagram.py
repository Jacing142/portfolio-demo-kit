"""Phase 6: render the interactive diagram with the bundled Archify renderer.

  python3 scripts/render_diagram.py --json WORK/demo/diagram.archify.json --work WORK/diagram --out OUTPUT

Runs `node vendor/archify/bin/archify.mjs finalize workflow ...` inside WORK, then copies only the
finished HTML to OUTPUT/diagram.html. Archify's receipt files stay in WORK.

Exit codes:
  0  diagram.html written (it may say it was not checked in a browser if no Chrome was found)
  1  Archify rejected the diagram: fix the JSON using the messages printed, then rerun
  3  Node.js is not installed: the demo ships with diagram.svg only (the fallback)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ARCHIFY = SKILL / "vendor" / "archify" / "bin" / "archify.mjs"
FALLBACK = 3


def find_node():
    node = shutil.which("node")
    if not node:
        return None
    try:
        version = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
        major = int(version.lstrip("v").split(".")[0])
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return node if major >= 18 else None


def find_chrome():
    """Chrome for Archify's browser check: ARCHIFY_CHROME, else Playwright's Chromium if installed."""
    if os.environ.get("ARCHIFY_CHROME"):
        return os.environ["ARCHIFY_CHROME"]
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            path = p.chromium.executable_path
        return path if path and Path(path).exists() else None
    except Exception:  # Playwright missing or its browser not downloaded: Archify looks for Chrome itself
        return None


def check_json(path):
    """Refuse fields that would put private file names or repository links into the public diagram."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    problems = []
    if data.get("diagram_type") != "workflow":
        problems.append('diagram_type must be "workflow"')
    if "repository" in data.get("meta", {}):
        problems.append("meta.repository is not allowed: it links to the private project")
    for node in data.get("nodes", []):
        if "sources" in node:
            problems.append(f"node {node.get('id')}: sources are not allowed: they name private files")
        if "brand" in node:
            problems.append(f"node {node.get('id')}: brand marks are not allowed in a demo")
    return data, problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="the Archify workflow JSON Claude wrote")
    ap.add_argument("--work", required=True, help="a folder inside WORK for Archify's files")
    ap.add_argument("--out", required=True, help="the demo OUTPUT folder")
    args = ap.parse_args(argv)

    node = find_node()
    if not node:
        stale = Path(args.out) / "diagram.html"
        if stale.exists():
            stale.unlink()
        print("Node.js 18 or newer was not found, so there is no interactive diagram. "
              "The demo will use diagram.svg only.")
        return FALLBACK

    data, problems = check_json(args.json)
    if problems:
        print("Fix the diagram JSON first:\n  - " + "\n  - ".join(problems))
        return 1

    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    for old in work.glob("diagram.*"):  # Archify will not overwrite an earlier run's receipts
        old.unlink()
    candidate = work / "candidate.json"
    data.setdefault("meta", {})["output"] = "diagram.html"
    data["meta"]["quality_profile"] = "showcase"
    candidate.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    env = dict(os.environ, ARCHIFY_UPDATE_CHECK_DISABLED="1")
    chrome = find_chrome()
    if chrome:
        env["ARCHIFY_CHROME"] = chrome
    proc = subprocess.run(
        [node, str(ARCHIFY), "finalize", "workflow", "candidate.json", "diagram.html",
         "--quality", "showcase", "--json"],
        cwd=work, env=env, capture_output=True, text=True, encoding="utf-8", timeout=600)
    try:
        receipt = json.loads(proc.stdout)
    except ValueError:
        print("Archify did not return a result:\n" + (proc.stderr or proc.stdout)[-2000:])
        return 1

    gates = receipt.get("gates", {})
    diags = receipt.get("diagnostics", [])
    no_chrome = gates.get("browser-check") == "skipped" and all(
        d.get("code") == "viewer/chrome-unavailable" for d in diags if d.get("severity") == "error")
    passed = all(gates.get(g) == "pass" for g in ("validate", "deliver", "check"))
    if not passed or (not receipt.get("ok") and not no_chrome):
        print("Archify rejected the diagram. Fix the JSON and rerun:")
        for d in diags[:12]:
            print(f"  - [{d.get('code')}] {d.get('message')}")
            for fix in d.get("supportedFixes", [])[:2]:
                print(f"      fix: {fix}")
        print(f"Gates: {gates}")
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(work / "diagram.html", out / "diagram.html")
    note = "checked in a browser" if not no_chrome else "NOT checked in a browser (no Chrome found)"
    print(f"Wrote {out / 'diagram.html'} ({(out / 'diagram.html').stat().st_size // 1024} KB), {note}.")
    print("Receipts stay in WORK and are not part of the demo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
