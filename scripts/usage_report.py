"""Summarise tokens and cost for a stage, as markdown for the issue comment.

  python3 scripts/usage_report.py --agent "Build=path/to/execution.json" --agent "Fix 1=..." \
      --prompts work/demo/results.json --scan work/scan/report.json

Agent figures come from the execution file that anthropics/claude-code-action writes
(its "result" entry carries total_cost_usd and usage). If a file is missing or has no
figures, the table says so and points to where to look instead.
"""

import argparse
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WHERE = ("Exact figures: open this run in the Actions tab and expand the Claude step, "
         "or see Usage in your Anthropic Console (console.anthropic.com).")


def agent_usage(path):
    p = Path(path) if path else None
    if not p or not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None
    items = data if isinstance(data, list) else [data]
    for item in reversed(items):
        if isinstance(item, dict) and item.get("type") == "result":
            u = item.get("usage", {}) or {}
            return {
                "input": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                + u.get("cache_creation_input_tokens", 0),
                "output": u.get("output_tokens", 0),
                "cost": item.get("total_cost_usd"),
                "turns": item.get("num_turns"),
            }
    return None


def price(model, usage):
    with open(ROOT / "config.toml", "rb") as fh:
        p = tomllib.load(fh).get("pricing", {}).get(model)
    if not p:
        return None
    return usage.get("input_tokens", 0) / 1e6 * p["input"] + usage.get("output_tokens", 0) / 1e6 * p["output"]


def fmt_cost(c):
    return "not reported" if c is None else f"${c:.2f}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", action="append", default=[], help="LABEL=execution_file")
    ap.add_argument("--prompts", help="results.json from run_prompts.py")
    ap.add_argument("--scan", help="scan report.json (for the rewording check)")
    ap.add_argument("--model", default="")
    args = ap.parse_args(argv)

    rows, total, missing = [], 0.0, False
    for entry in args.agent:
        label, _, path = entry.partition("=")
        u = agent_usage(path)
        if u is None:
            missing = True
            rows.append(f"| {label} (agent) | not reported | not reported | not reported |")
            continue
        total += u["cost"] or 0
        missing |= u["cost"] is None
        rows.append(f"| {label} (agent, {u['turns']} turns) | {u['input']:,} | {u['output']:,} | {fmt_cost(u['cost'])} |")
    if args.prompts and Path(args.prompts).is_file():
        r = json.loads(Path(args.prompts).read_text(encoding="utf-8"))
        s = r.get("spent", {})
        c = r.get("cost_usd")
        total += c or 0
        missing |= c is None
        rows.append(f"| Your prompts on invented inputs ({s.get('calls', 0)} calls, {r.get('requested_model', '')}) "
                    f"| {s.get('input_tokens', 0):,} | {s.get('output_tokens', 0):,} | {fmt_cost(c)} |")
    if args.scan and Path(args.scan).is_file():
        u = json.loads(Path(args.scan).read_text(encoding="utf-8")).get("paraphrase_usage") or {}
        if u:
            c = price(args.model, u)
            total += c or 0
            missing |= c is None
            rows.append(f"| Rewording check | {u.get('input_tokens', 0):,} | {u.get('output_tokens', 0):,} | {fmt_cost(c)} |")

    lines = ["### Cost of this stage", "", "| Step | Input tokens | Output tokens | Cost (estimate) |",
             "|---|---|---|---|"] + rows
    lines += ["", f"**Total (estimate): ${total:.2f}**" + (" plus the steps marked 'not reported'" if missing else ""),
              "", WHERE]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
