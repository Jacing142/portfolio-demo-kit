"""Entry point for the leak scanner, so it runs from any working directory.

  python3 "${CLAUDE_SKILL_DIR}/scripts/leak_scan.py" plant --src PROJECT --dst WORK/copy --out WORK/private/canaries.json
  python3 "${CLAUDE_SKILL_DIR}/scripts/leak_scan.py" scan --source WORK/copy --output OUTPUT \
      --canaries WORK/private/canaries.json --allow WORK/decisions.json --report WORK/scan/report.json

See SCANNER.md for what it checks.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scanner.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
