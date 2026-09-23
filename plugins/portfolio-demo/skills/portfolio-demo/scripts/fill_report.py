"""Phase 8: write the scan counts into SANITISATION.md.

  python3 scripts/fill_report.py --output OUTPUT --report WORK/scan/report.json

Replaces the <!-- PDK:SCAN_RESULTS --> line with a table of counts only (never matched text).
Refuses unless the report says the scan was clean. Rescan afterwards: SANITISATION.md ships in the demo.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scanner.scan import summary_counts  # noqa: E402

MARKER = "<!-- PDK:SCAN_RESULTS -->"


def fill(output, report_path):
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not report.get("clean"):
        sys.exit("The last scan was not clean. Fix the findings and rescan before filling in the report.")
    doc = Path(output) / "SANITISATION.md"
    if not doc.exists():
        sys.exit(f"{doc} is missing")
    text = doc.read_text(encoding="utf-8")
    if MARKER not in text:
        sys.exit(f"SANITISATION.md has no {MARKER} line for the scan results")
    doc.write_text(text.replace(MARKER, summary_counts(report)), encoding="utf-8")
    print("Scan results written into SANITISATION.md")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args(argv)
    fill(args.output, args.report)


if __name__ == "__main__":
    main()
