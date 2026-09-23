"""Phase 0 preflight: check the files are there, detect the stack, flag anything too big.

  python3 scripts/preflight.py --folder input/ --example apps-script-feedback --out work/preflight.md

Prints folder=... and stack=... for $GITHUB_OUTPUT. Exits 1 with a plain message if there is nothing to read.
"""

import argparse
import csv
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER_RE = re.compile(r"^[A-Za-z0-9._/ -]+$")
IGNORE = {".gitkeep", ".DS_Store"}
KIT_README = ROOT / "input" / "README.md"  # upload instructions, not part of the project

STACKS = [
    ("Google Apps Script", lambda names, exts: "appsscript.json" in names or ".gs" in exts),
    ("Python", lambda names, exts: ".py" in exts or ".ipynb" in exts),
    ("JavaScript / TypeScript", lambda names, exts: bool(exts & {".js", ".ts", ".tsx", ".jsx", ".mjs"})),
    ("Spreadsheet data (CSV)", lambda names, exts: bool(exts & {".csv", ".tsv"})),
    ("Excel workbook", lambda names, exts: bool(exts & {".xlsx", ".xls"})),
    ("Web page (HTML/CSS)", lambda names, exts: bool(exts & {".html", ".css"})),
    ("SQL", lambda names, exts: ".sql" in exts),
    ("Text prompts / documents", lambda names, exts: bool(exts & {".txt", ".md"})),
]


def project_files(folder):
    return [p for p in sorted(folder.rglob("*"))
            if p.is_file() and p.name not in IGNORE and ".git" not in p.parts and p != KIT_README]


def resolve(folder, example):
    if not FOLDER_RE.match(folder) or ".." in folder or folder.startswith("/"):
        sys.exit(f"The folder name '{folder}' is not allowed. Use a folder inside this repository, like input/")
    path = ROOT / folder
    if not path.is_dir():
        sys.exit(f"The folder '{folder}' does not exist in this repository.")
    if not project_files(path) and folder.strip("/") == "input":
        ex = ROOT / "examples" / example / "before"
        if not ex.is_dir():
            sys.exit(f"input/ is empty and the example '{example}' does not exist.")
        return f"examples/{example}/before/", ex, True
    if not project_files(path):
        sys.exit(f"The folder '{folder}' has no files in it. Upload your project files first.")
    return folder.rstrip("/") + "/", path, False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default="input/")
    ap.add_argument("--example", default="apps-script-feedback")
    ap.add_argument("--out", default="work/preflight.md")
    args = ap.parse_args(argv)

    with open(ROOT / "config.toml", "rb") as fh:
        limits = tomllib.load(fh).get("limits", {})
    max_mb, warn_rows = limits.get("max_file_mb", 25), limits.get("warn_rows", 200)

    rel, path, used_example = resolve(args.folder, args.example)
    files = project_files(path)
    exts = {p.suffix.lower() for p in files}
    names = {p.name for p in files}
    stacks = [name for name, test in STACKS if test(names, exts)] or ["Unknown"]

    lines = ["# Preflight", "", f"- Folder: `{rel}`" + (" (your input/ folder was empty, so this is an example)" if used_example else ""),
             f"- Files: {len(files)}", f"- Detected: {', '.join(stacks)}", "", "| File | Size | Notes |", "|---|---|---|"]
    warnings = []
    for p in files:
        size = p.stat().st_size
        note = ""
        if size > max_mb * 1024 * 1024:
            note = f"too large (over {max_mb} MB)"
            warnings.append(f"{p.name} is larger than {max_mb} MB. Replace it with a small sample; the tool only needs the shape of the data.")
        elif p.suffix.lower() in {".csv", ".tsv"}:
            with p.open(encoding="utf-8", errors="replace", newline="") as fh:
                rows = sum(1 for _ in csv.reader(fh)) - 1
            note = f"{rows} rows"
            if rows > warn_rows:
                warnings.append(f"{p.name} has {rows} rows. A sample of 30-50 rows is enough and sends less to the AI provider.")
        elif p.suffix.lower() in {".xlsx", ".xls"}:
            note = "Excel file: save each sheet as CSV so it can be read"
            warnings.append(f"{p.name} is an Excel file. Please save each sheet as CSV (File > Download > CSV) and upload those instead.")
        lines.append(f"| {p.relative_to(path)} | {size / 1024:.1f} KB | {note} |")
    counts = Counter(p.suffix.lower() or "(none)" for p in files)
    lines += ["", "File types: " + ", ".join(f"{k} x{v}" for k, v in counts.most_common())]
    if warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in warnings]

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"folder={rel}")
    print(f"stack={'; '.join(stacks)}")
    print(f"used_example={'true' if used_example else 'false'}")


if __name__ == "__main__":
    main()
