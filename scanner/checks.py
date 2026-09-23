"""The individual leak checks. Each returns a list of finding dicts.

A finding: {"check", "file", "text", "where", "severity"}.
"text" holds the matched string; reports mask it before showing it anywhere.
severity is "fail" (blocks the demo) or "warn" (for a human to review).
"""

import json
import re
from urllib.parse import urlparse

from .extract import normalize, strip_tags, words

PATTERNS = {
    "anthropic_key": r"sk-ant-[A-Za-z0-9_\-]{10,}",
    "openai_key": r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}",
    "aws_access_key": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
    "github_token": r"\bgh[pousr]_[A-Za-z0-9]{30,}",
    "slack_token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    "google_api_key": r"\bAIza[0-9A-Za-z_\-]{35}",
    "jwt": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "secret_assignment": r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "url": r"\bhttps?://[^\s\"'<>)\]]+",
    "private_ip": r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b",
    "long_id": r"\b(?=[A-Za-z0-9_-]*[0-9])(?=[A-Za-z0-9_-]*[a-z])(?=[A-Za-z0-9_-]*[A-Z])[A-Za-z0-9_-]{33,}\b",
}


def _host_allowed(host, allowed):
    host = (host or "").lower()
    return any(host == a or host.endswith("." + a) for a in allowed)


def secret_patterns(outputs, cfg):
    names = list(cfg.get("patterns", PATTERNS))
    table = {n: PATTERNS[n] for n in names if n in PATTERNS}
    table.update(cfg.get("extra_patterns", {}) or {})
    findings = []
    for rel, raw, _ in outputs:
        for name, rx in table.items():
            for m in re.finditer(rx, raw):
                hit = m.group(0)
                if name == "email" and _host_allowed(hit.split("@")[-1], cfg["allowed_email_domains"]):
                    continue
                if name == "url" and _host_allowed(urlparse(hit).hostname, cfg["allowed_url_hosts"]):
                    continue
                findings.append({"check": f"pattern:{name}", "file": rel, "text": hit,
                                 "where": "", "severity": "fail"})
    return _dedupe(findings)


def exact_strings(outputs, candidates, allow):
    findings = []
    for cand in candidates:
        key = normalize(cand["text"])
        if allow.covers(key):
            continue
        # Short values (names, order numbers) must match as whole words, not inside other words.
        short = re.compile(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])") if len(key) < 12 else None
        for rel, _, norm in outputs:
            if (short.search(norm) if short else key in norm):
                findings.append({"check": "exact", "file": rel, "text": cand["text"],
                                 "where": cand["where"], "severity": "fail"})
    return findings


def word_runs(outputs, source_docs, n, allow):
    """Find runs of n or more consecutive words copied from any source file."""
    index = {}
    for rel, ws in source_docs:
        for i in range(len(ws) - n + 1):
            gram = tuple(ws[i:i + n])
            if _informative(gram) and gram not in index:
                index[gram] = rel
    findings = []
    for rel, raw, _ in outputs:
        ws = words(strip_tags(raw))
        hits = [i for i in range(len(ws) - n + 1)
                if tuple(ws[i:i + n]) in index and not allow.covers_gram(tuple(ws[i:i + n]))]
        for start, end in _merge(hits, n):
            findings.append({"check": "word_run", "file": rel, "text": " ".join(ws[start:end]),
                             "where": index[tuple(ws[start:start + n])], "severity": "fail"})
    return _dedupe(findings)


def canaries(outputs, canary_list):
    findings = []
    for c in canary_list:
        key = normalize(c["value"])
        for rel, _, norm in outputs:
            if key in norm:
                findings.append({"check": f"canary:{c['kind']}", "file": rel, "text": c["value"],
                                 "where": c.get("planted_in", ""), "severity": "fail"})
    return findings


def hidden_files(root_files):
    return [{"check": "hidden_file", "file": rel, "text": rel, "where": "", "severity": "fail"}
            for rel in root_files if any(p.startswith(".") for p in rel.split("/"))]


DATA_RE = re.compile(r'<script[^>]*id="demo-data"[^>]*>(.*?)</script>', re.S)


def data_match(out_dir):
    """index.html's inline data must equal data.json, when both exist."""
    page, data = out_dir / "index.html", out_dir / "data.json"
    if not (page.exists() and data.exists()):
        return []
    m = DATA_RE.search(page.read_text(encoding="utf-8"))
    problem = None
    if not m:
        problem = "index.html has no <script id=\"demo-data\"> block"
    else:
        try:
            if json.loads(m.group(1)) != json.loads(data.read_text(encoding="utf-8")):
                problem = "inline data in index.html differs from data.json"
        except ValueError as exc:
            problem = f"data could not be parsed: {exc}"
    if problem:
        return [{"check": "data_match", "file": "index.html", "text": problem, "where": "",
                 "severity": "fail"}]
    return []


def _informative(gram):
    """Skip runs made of numbers and tiny words, e.g. a 1-5 answer scale."""
    return sum(1 for w in gram if len(w) >= 3 and not w.isdigit()) >= 3


def _merge(starts, n):
    spans = []
    for s in starts:
        if spans and s <= spans[-1][1]:
            spans[-1][1] = s + n
        else:
            spans.append([s, s + n])
    return spans


def _dedupe(findings):
    seen, out = set(), []
    for f in findings:
        key = (f["check"], f["file"], f["text"])
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out
