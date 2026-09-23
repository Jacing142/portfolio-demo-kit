"""Turn the Stage 1 issue and its replies into work/thread.md for Stage 2.

  gh issue view N --json body,comments,title | python3 scripts/issue_thread.py work/thread.md

Prints folder=... read from the hidden marker Stage 1 put in the issue.
Only comments from people are kept; comments by bots (including this tool) are dropped,
except the Stage 1 body itself, which holds the proposed table.
"""

import json
import re
import sys
from pathlib import Path

MARKER_RE = re.compile(r"<!--\s*pdk:folder=([A-Za-z0-9._/ -]+)\s*-->")


def main(out_path):
    data = json.load(sys.stdin)
    body = data.get("body") or ""
    m = MARKER_RE.search(body)
    if not m or ".." in m.group(1):
        sys.exit("This issue was not opened by '1. Scan my project', so /build cannot use it.")
    parts = ["# Stage 1 issue (proposed classification)", "", body, "", "# Owner replies (oldest first)", ""]
    for c in data.get("comments", []):
        author = (c.get("author") or {}).get("login", "")
        text = (c.get("body") or "").strip()
        if author.endswith("[bot]") or author == "github-actions" or not text:
            continue
        parts += [f"## Reply from @{author} at {c.get('createdAt', '')}", "", text, ""]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(parts), encoding="utf-8")
    print(f"folder={m.group(1)}")


if __name__ == "__main__":
    main(sys.argv[1])
