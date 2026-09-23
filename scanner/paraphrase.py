"""Optional check: ask the model whether PROPRIETARY text was reworded into the demo.

Results are warnings for a human to review; they never block the demo on their own.
The API call is injectable so the tests run offline.
"""

import json
import os
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"

INSTRUCTIONS = """You compare two texts for a privacy review.
PROTECTED lists passages the owner marked as proprietary. DEMO is a public web page.
Find places where DEMO restates a PROTECTED passage closely enough that a reader could
recover its specific content (same specific rules, numbers, wording or structure), even if reworded.
Generic ideas and common phrases do not count.
Reply with JSON only: {"matches": [{"protected_index": <int>, "demo_excerpt": "<under 20 words>", "reason": "<one line>"}]}
Reply {"matches": []} if there are none."""


def call_api(model, system, user, max_tokens=2000):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    body = json.dumps({
        "model": model, "max_tokens": max_tokens, "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01",
    })
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return text, data.get("usage", {})


def check(outputs, protected, model, api=call_api):
    """Return (findings, usage). Findings are warnings."""
    if not protected:
        return [], {}
    demo = "\n\n".join(f"--- {rel} ---\n{raw[:40000]}" for rel, raw, _ in outputs
                       if rel.endswith((".html", ".md", ".json")))
    listing = "\n".join(f"[{i}] {p}" for i, p in enumerate(protected))
    user = f"PROTECTED:\n{listing}\n\nDEMO:\n{demo}"
    try:
        text, usage = api(model, INSTRUCTIONS, user)
        start, end = text.find("{"), text.rfind("}")
        matches = json.loads(text[start:end + 1]).get("matches", [])
    except Exception as exc:  # the check is advisory; report that it did not run
        return [{"check": "paraphrase", "file": "", "text": f"paraphrase check did not run: {exc}",
                 "where": "", "severity": "warn"}], {}
    findings = []
    for m in matches:
        idx = m.get("protected_index")
        where = f"proprietary item {idx}" if isinstance(idx, int) else ""
        findings.append({"check": "paraphrase", "file": "", "text": m.get("demo_excerpt", ""),
                         "where": where, "reason": m.get("reason", ""), "severity": "warn"})
    return findings, usage
