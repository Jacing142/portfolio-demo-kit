"""Canaries: ten unique fake strings planted in a working copy of the project.

If any of them reaches the demo, real rows were copied instead of invented,
so the scan fails. Values are random per run and never written to the demo.
"""

import csv
import io
import json
import random
import shutil
import string
from pathlib import Path

from .extract import SKIP_DIRS, TABLE_EXT, iter_files, read_text

_SYLLABLES = ["bra", "cor", "dal", "fen", "gri", "hol", "jas", "kel", "lun", "mor", "nev",
              "orr", "pim", "quil", "ros", "sab", "tev", "ulm", "vor", "wyn", "yar", "zel"]
_NOUNS = ["renewal", "invoice", "audit", "handover", "rollout", "migration", "review", "pilot"]

COMMENT = {
    ".py": "# {}", ".sh": "# {}", ".rb": "# {}", ".r": "# {}", ".yml": "# {}", ".yaml": "# {}",
    ".toml": "# {}", ".ini": "; {}", ".cfg": "# {}", ".ps1": "# {}",
    ".js": "// {}", ".gs": "// {}", ".ts": "// {}", ".tsx": "// {}", ".jsx": "// {}",
    ".mjs": "// {}", ".cjs": "// {}", ".java": "// {}", ".kt": "// {}", ".go": "// {}",
    ".cs": "// {}", ".swift": "// {}", ".rs": "// {}", ".php": "// {}",
    ".sql": "-- {}", ".html": "<!-- {} -->", ".htm": "<!-- {} -->", ".xml": "<!-- {} -->",
    ".css": "/* {} */",
}
# Plain text and markdown files are never planted in: they are often prompts, and a canary inside
# a prompt would end up in the demo's assembled prompt. Spreadsheets and code comments are used instead.


def _word(rng, parts=2):
    return "".join(rng.choice(_SYLLABLES) for _ in range(parts))


def make(seed=None):
    """Return 10 canaries: 2 each of name, email, key, id, sentence."""
    rng = random.Random(seed)
    alnum = string.ascii_letters + string.digits
    out = []
    for _ in range(2):
        first, last = _word(rng).title(), _word(rng, 3).title()
        out.append({"kind": "name", "value": f"{first} {last}"})
        out.append({"kind": "email", "value": f"{first.lower()}.{last.lower()}@{_word(rng)}-{_word(rng)}.net"})
        out.append({"kind": "key", "value": "sk-ant-api03-" + "".join(rng.choice(alnum) for _ in range(40))})
        out.append({"kind": "id", "value": f"{rng.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{rng.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}-{rng.randint(10**7, 10**8 - 1)}"})
        out.append({"kind": "sentence", "value": f"Please move the {_word(rng)} {rng.choice(_NOUNS)} to {first} before the {_word(rng)} committee meets."})
    return out


def plant(src, dst, canaries):
    """Copy src to dst and insert every canary into the copy. Returns the canaries with locations."""
    src, dst = Path(src), Path(dst)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*SKIP_DIRS))
    files = [p for p in iter_files(dst) if read_text(p) is not None]
    tables = [p for p in files if p.suffix.lower() in TABLE_EXT]
    others = [p for p in files if p.suffix.lower() in COMMENT]
    pending = list(canaries)

    # Spreadsheets first: one extra row per table, canary values placed in its cells.
    for path in tables:
        if not pending:
            break
        text = read_text(path)
        delim = "\t" if path.suffix.lower() == ".tsv" else ","
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))
        width = max((len(r) for r in rows), default=1) or 1
        take = pending[: max(1, min(width, 3))]
        pending = pending[len(take):]
        row = [c["value"] for c in take] + [""] * (width - len(take))
        buf = io.StringIO()
        csv.writer(buf, delimiter=delim, lineterminator="\n").writerow(row)
        sep = "" if text.endswith("\n") or not text else "\n"
        path.write_text(text + sep + buf.getvalue(), encoding="utf-8")
        for c in take:
            c["planted_in"] = str(path.relative_to(dst))

    # Then code files, as comments at the end so the code still runs.
    i = 0
    while pending and others:
        path = others[i % len(others)]
        c = pending.pop(0)
        line = COMMENT[path.suffix.lower()].format(c["value"])
        text = read_text(path)
        sep = "" if text.endswith("\n") or not text else "\n"
        path.write_text(text + sep + line + "\n", encoding="utf-8")
        c["planted_in"] = str(path.relative_to(dst))
        i += 1

    if pending:
        notes = dst / "pdk-notes.txt"
        with notes.open("a", encoding="utf-8") as fh:
            for c in pending:
                fh.write(c["value"] + "\n")
                c["planted_in"] = "pdk-notes.txt"
    return canaries


def save(canaries, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"canaries": canaries}, indent=2), encoding="utf-8")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))["canaries"]
