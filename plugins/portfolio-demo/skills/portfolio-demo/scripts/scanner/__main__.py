"""Command line for the leak scanner. Run it through scripts/leak_scan.py:

  python3 scripts/leak_scan.py plant    --src PROJECT --dst WORK/copy --out WORK/private/canaries.json
  python3 scripts/leak_scan.py scan     --source WORK/copy --output OUTPUT [--canaries ...] [--allow ...]
  python3 scripts/leak_scan.py patterns FILE_OR_FOLDER    (secret patterns only)

Exit codes: 0 clean, 1 leaks found, 2 scanner self-test failed or bad input.
"""

import argparse
import json
import sys
from pathlib import Path

from . import canaries, checks, scan
from .config import load
from .extract import output_texts

# The skill folder: scripts/scanner/__main__.py -> scripts -> skill
ROOT = Path(__file__).resolve().parent.parent.parent


def main(argv=None):
    ap = argparse.ArgumentParser(prog="leak_scan.py")
    ap.add_argument("--config", default=str(ROOT / "config.toml"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plant", help="copy the project and plant 10 canaries in the copy")
    p.add_argument("--src", required=True)
    p.add_argument("--dst", required=True)
    p.add_argument("--out", required=True, help="where to save the canary list")

    s = sub.add_parser("scan", help="scan the demo output folder")
    s.add_argument("--source", required=True, help="the project copy the demo was built from")
    s.add_argument("--output", required=True, help="the folder that goes into demo.zip")
    s.add_argument("--canaries")
    s.add_argument("--allow", help="decisions.json (keep_strings) or a JSON list of kept strings")
    s.add_argument("--public", action="append", default=None,
                   help="folder of already-public text to ignore (default: the skill's templates/)")
    s.add_argument("--paraphrase", action="store_true", help="run the optional API rewording check")
    s.add_argument("--report", help="write the full JSON report here (keep it private)")
    s.add_argument("--markdown", help="write the masked markdown report here")

    t = sub.add_parser("patterns", help="secret patterns only")
    t.add_argument("path")

    args = ap.parse_args(argv)
    cfg = load(args.config)

    if args.cmd == "plant":
        if not Path(args.src).is_dir():
            print(f"Folder not found: {args.src}", file=sys.stderr)
            return 2
        planted = canaries.plant(args.src, args.dst, canaries.make())
        canaries.save(planted, args.out)
        print(f"Planted {len(planted)} canaries in {args.dst}")
        return 0

    if args.cmd == "patterns":
        path = Path(args.path)
        if path.is_file():
            outputs = [(path.name, path.read_text(encoding="utf-8"), "")]
        else:
            outputs = output_texts(path)
        hits = checks.secret_patterns(outputs, cfg)
        for h in hits:
            print(f"{h['check']} in {h['file']}: {scan.mask(h['text'])}")
        return 1 if hits else 0

    if not Path(args.output).is_dir() or not any(Path(args.output).iterdir()):
        print(f"Output folder is missing or empty: {args.output}", file=sys.stderr)
        return 2
    public = args.public if args.public is not None else [str(ROOT / "templates")]
    report = scan.run(args.source, args.output, cfg, args.canaries, args.allow, public,
                      paraphrase_on=args.paraphrase and cfg.get("paraphrase_check", False))
    md = scan.to_markdown(report)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.markdown:
        Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown).write_text(md, encoding="utf-8")
    print(md)
    if not report["negative_control"]["passed"]:
        return 2
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
