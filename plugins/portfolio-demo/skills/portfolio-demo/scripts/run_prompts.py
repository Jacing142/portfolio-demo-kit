"""Phase 5: run the project's own prompts on invented inputs, through the Anthropic API.

  python3 scripts/run_prompts.py WORK/demo/prompt_plan.json WORK/demo/results.json

Needs ANTHROPIC_API_KEY in the environment. Without it, write illustrative outputs instead.

The plan is written by Claude in phase 5 of SKILL.md:
  {"cases": [{"id": "case-1", "system": "...", "messages": [{"role": "user", "content": "..."}]}]}

Each result records the model the API reports it used, so the page's provenance label
comes from the API response, never from whoever wrote the plan. Results are cached by request, so
re-running after a fix only calls the API for cases that changed.
Python standard library only.
"""

import hashlib
import json
import os
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://api.anthropic.com/v1/messages"
# Models with server-side refusal fallback support: a declined request is retried on a fallback model.
FALLBACK_MODELS = {"claude-fable-5-1", "claude-fable-5", "claude-opus-5"}


def load_config():
    with open(ROOT / "config.toml", "rb") as fh:
        return tomllib.load(fh)


def request_body(case, model, max_tokens):
    body = {
        "model": model,
        "max_tokens": min(int(case.get("max_tokens", max_tokens)), max_tokens),
        "messages": case["messages"],
    }
    if case.get("system"):
        body["system"] = case["system"]
    return body


def call(body, key, retries=3):
    headers = {"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"}
    if body["model"] in FALLBACK_MODELS:
        body = dict(body, fallbacks="default")
        headers["anthropic-beta"] = "server-side-fallback-2026-07-01"
    data = json.dumps(body).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(API_URL, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            if exc.code in (429, 500, 502, 503, 529) and attempt < retries:
                time.sleep(float(exc.headers.get("retry-after") or 2 ** (attempt + 2)))
                continue
            raise RuntimeError(f"API error {exc.code}: {detail}") from None
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(2 ** (attempt + 2))
                continue
            raise RuntimeError(f"Could not reach the API: {exc.reason}") from None


def cost(usage, prices):
    if not prices:
        return None
    return round(usage.get("input_tokens", 0) / 1e6 * prices["input"]
                 + usage.get("output_tokens", 0) / 1e6 * prices["output"], 4)


def main(plan_path, results_path, call_fn=call):
    cfg = load_config()
    model = cfg["model"]["demo_outputs"]
    limits = cfg.get("limits", {})
    max_cases, max_tokens = limits.get("max_demo_cases", 6), limits.get("max_output_tokens", 2000)
    prices = cfg.get("pricing", {}).get(model)

    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    cases = plan.get("cases", [])
    if len(cases) > max_cases:
        print(f"Plan has {len(cases)} cases; only the first {max_cases} are run (config.toml max_demo_cases).")
        cases = cases[:max_cases]

    results_file = Path(results_path)
    previous = json.loads(results_file.read_text(encoding="utf-8")) if results_file.exists() else {}
    old_cases = previous.get("cases", {})
    spent = previous.get("spent", {"input_tokens": 0, "output_tokens": 0, "calls": 0})

    key = os.environ.get("ANTHROPIC_API_KEY", "")
    out = {}
    for case in cases:
        body = request_body(case, model, max_tokens)
        sha = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        if old_cases.get(case["id"], {}).get("request_sha") == sha:
            out[case["id"]] = old_cases[case["id"]]
            print(f"{case['id']}: unchanged, reused")
            continue
        if not key:
            sys.exit("ANTHROPIC_API_KEY is not set, so the prompts cannot be run. Write illustrative outputs instead.")
        resp = call_fn(body, key)
        usage = resp.get("usage", {})
        spent["input_tokens"] += usage.get("input_tokens", 0)
        spent["output_tokens"] += usage.get("output_tokens", 0)
        spent["calls"] += 1
        text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
        refused = resp.get("stop_reason") == "refusal"
        out[case["id"]] = {
            "output": None if refused else text,
            "model": resp.get("model", model),
            "stop_reason": resp.get("stop_reason"),
            "usage": usage,
            "request_sha": sha,
        }
        print(f"{case['id']}: {resp.get('stop_reason')} ({usage.get('output_tokens', 0)} output tokens)")

    result = {"requested_model": model, "cases": out, "spent": spent,
              "cost_usd": cost(spent, prices)}
    c = result["cost_usd"]
    print(f"Tokens used so far: {spent['input_tokens']:,} in, {spent['output_tokens']:,} out"
          + (f", about ${c:.2f}" if c is not None else ""))
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    try:
        main(sys.argv[1], sys.argv[2])
    except RuntimeError as exc:
        sys.exit(str(exc))
