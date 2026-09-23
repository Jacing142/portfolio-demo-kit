#!/usr/bin/env bash
# Run the prompts (cached), build the page, and scan it. Used by Stage 2 after the build and after each fix.
# Needs: PDK_PRIVATE (folder holding canaries.json and the frozen decisions.json), ANTHROPIC_API_KEY.
# Exit code: 0 clean, non-zero otherwise. Always leaves work/scan/report.json and report.md.
set -uo pipefail

mkdir -p work/scan work/demo

fail_report() {
  python3 - "$1" <<'EOF'
import json, sys
msg = sys.argv[1]
json.dump({"clean": False, "build_error": msg, "findings": []}, open("work/scan/report.json", "w"), indent=2)
open("work/scan/report.md", "w").write("## Leak scan: NOT RUN\n\nThe demo could not be built: " + msg + "\n")
EOF
}

if [ -f work/demo/prompt_plan.json ]; then
  if ! python3 scripts/run_prompts.py work/demo/prompt_plan.json work/demo/results.json 2> work/scan/prompts.err; then
    fail_report "running the prompts failed: $(tail -c 600 work/scan/prompts.err)"
    exit 1
  fi
fi

rm -f output/index.html output/data.json output/diagram.svg
if ! python3 scripts/build_page.py --spec work/demo/spec.json --plan work/demo/prompt_plan.json \
    --results work/demo/results.json --out output 2> work/scan/build.err; then
  fail_report "the page build failed: $(tail -c 600 work/scan/build.err)"
  exit 1
fi

python3 -m scanner scan --source work/copy --output output \
  --canaries "$PDK_PRIVATE/canaries.json" --allow "$PDK_PRIVATE/decisions.json" \
  --report work/scan/report.json --markdown work/scan/report.md
