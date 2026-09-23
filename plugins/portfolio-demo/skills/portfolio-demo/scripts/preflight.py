"""Phase 0 preflight: list the project's files, detect the stack, flag anything too big,
and choose an output folder outside the project.

  python3 scripts/preflight.py --project PATH [--output PATH]

The default output folder is ../<project-name>-portfolio-demo/ next to the project.
Refuses an output folder inside the project (and so inside its .git).
Prints a plain-text report; exits 1 with a plain message if something is wrong.
"""

import argparse
import csv
import sys
import tomllib
from collections import Counter
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
IGNORE_FILES = {".DS_Store"}

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
    out = []
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder)
        if p.is_file() and p.name not in IGNORE_FILES and not (set(rel.parts) & IGNORE_DIRS):
            out.append(p)
    return out


def inside(child, parent):
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="the private project folder")
    ap.add_argument("--output", help="where the demo goes (default: ../<project>-portfolio-demo/)")
    args = ap.parse_args(argv)

    with open(SKILL / "config.toml", "rb") as fh:
        limits = tomllib.load(fh).get("limits", {})
    max_mb, warn_rows = limits.get("max_file_mb", 25), limits.get("warn_rows", 200)

    project = Path(args.project).resolve()
    if not project.is_dir():
        sys.exit(f"Project folder not found: {project}")
    output = Path(args.output).resolve() if args.output else project.parent / f"{project.name}-portfolio-demo"
    if inside(output, project):
        sys.exit(f"The output folder {output} is inside the project. Choose a folder outside it, "
                 f"for example {project.parent / (project.name + '-portfolio-demo')}")
    if output.exists() and any(output.iterdir()):
        print(f"Note: the output folder {output} already has files in it. They may be overwritten.")

    files = project_files(project)
    if not files:
        sys.exit(f"No files found in {project}.")
    exts = {p.suffix.lower() for p in files}
    names = {p.name for p in files}
    stacks = [name for name, test in STACKS if test(names, exts)] or ["Unknown"]

    print(f"Project: {project}")
    print(f"Output folder: {output}")
    print(f"Files: {len(files)}")
    print(f"Detected: {', '.join(stacks)}")
    print("File types: " + ", ".join(f"{k} x{v}" for k, v in Counter(p.suffix.lower() or '(none)' for p in files).most_common()))
    print()
    warnings = []
    for p in files:
        size = p.stat().st_size
        note = ""
        if size > max_mb * 1024 * 1024:
            note = f"large (over {max_mb} MB)"
            warnings.append(f"{p.relative_to(project)} is over {max_mb} MB. A small sample is enough; only the shape of the data is needed.")
        elif p.suffix.lower() in {".csv", ".tsv"}:
            with p.open(encoding="utf-8", errors="replace", newline="") as fh:
                rows = max(sum(1 for _ in csv.reader(fh)) - 1, 0)
            note = f"{rows} rows"
            if rows > warn_rows:
                warnings.append(f"{p.relative_to(project)} has {rows} rows. Read only the header and a sample of 30-50 rows.")
        elif p.suffix.lower() in {".xlsx", ".xls"}:
            note = "Excel: cannot be read as text"
            warnings.append(f"{p.relative_to(project)} is an Excel file. Ask the owner to save each sheet as CSV.")
        print(f"  {p.relative_to(project)}  {size / 1024:.1f} KB  {note}".rstrip())
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")


if __name__ == "__main__":
    main()
