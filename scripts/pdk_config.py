"""Print config.toml values as key=value lines for $GITHUB_OUTPUT.

  python3 scripts/pdk_config.py >> "$GITHUB_OUTPUT"

Keys are flattened: [model] agent -> model_agent, [limits] stage1_max_turns -> limits_stage1_max_turns.
"""

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


def flatten(cfg):
    out = {}
    for section in ("model", "limits"):
        for key, value in cfg.get(section, {}).items():
            out[f"{section}_{key}"] = value
    return out


def main(path=ROOT / "config.toml"):
    with open(path, "rb") as fh:
        cfg = tomllib.load(fh)
    for key, value in flatten(cfg).items():
        value = str(value)
        if not SAFE.match(value):
            sys.exit(f"config.toml: {key} has an unexpected value: {value!r}")
        print(f"{key}={value}")
    fix = int(cfg.get("limits", {}).get("max_fix_attempts", 3))
    if not 0 <= fix <= 3:
        sys.exit("config.toml: max_fix_attempts must be between 0 and 3")


if __name__ == "__main__":
    main()
