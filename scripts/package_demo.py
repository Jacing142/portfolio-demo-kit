"""Phase 8: put the scan results into SANITISATION.md, then zip the output folder.

  python3 scripts/package_demo.py fill --output output/ --report work/scan/report.json
  python3 scripts/package_demo.py zip  --output output/ --dest work/dist

`fill` writes counts only (no matched text) where SANITISATION.md has <!-- PDK:SCAN_RESULTS -->.
`zip` refuses to package unless the report says the scan is clean, and never includes hidden
files or folders such as .git. The workflow rescans between the two steps.
"""

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scanner.scan import summary_counts  # noqa: E402

MARKER = "<!-- PDK:SCAN_RESULTS -->"


def fill(output, report_path):
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    doc = Path(output) / "SANITISATION.md"
    if not doc.exists():
        sys.exit("output/SANITISATION.md is missing")
    text = doc.read_text(encoding="utf-8")
    if MARKER not in text:
        sys.exit(f"SANITISATION.md has no {MARKER} placeholder for the scan results")
    doc.write_text(text.replace(MARKER, summary_counts(report)), encoding="utf-8")
    print("Scan results written into SANITISATION.md")


def make_zip(output, dest, report_path):
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not report.get("clean"):
        sys.exit("The last scan was not clean, so nothing was packaged.")
    output, dest = Path(output), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    zpath = dest / "demo.zip"
    count = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(output.rglob("*")):
            rel = p.relative_to(output)
            if p.is_file() and not any(part.startswith(".") for part in rel.parts):
                zf.write(p, str(rel))
                count += 1
    shutil.copy(output / "SANITISATION.md", dest / "SANITISATION.md")
    print(f"Wrote {zpath} with {count} files")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fill", "zip"])
    ap.add_argument("--output", default="output")
    ap.add_argument("--report", default="work/scan/report.json")
    ap.add_argument("--dest", default="work/dist")
    args = ap.parse_args(argv)
    if args.cmd == "fill":
        fill(args.output, args.report)
    else:
        make_zip(args.output, args.dest, args.report)


if __name__ == "__main__":
    main()
