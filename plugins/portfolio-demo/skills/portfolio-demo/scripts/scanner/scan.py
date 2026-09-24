"""Run every check on the output folder and produce a report."""

import html
import json
import re
import shutil
import tempfile
from pathlib import Path

from . import checks, paraphrase
from .extract import normalize, output_texts, source_candidates, source_word_index, words


# Public model names (e.g. "claude-sonnet-5") appear in provenance labels and are not secrets.
MODEL_ID_RE = re.compile(r"(?:claude|gpt|gemini|llama|mistral|o\d)[a-z0-9.\-]*")


class Allowlist:
    """Text the owner chose to KEEP, plus text already public in this kit's own templates."""

    def __init__(self, keep=(), public_texts=(), n=6):
        self.keep = [normalize(k) for k in keep if k and k.strip()]
        self.public = "\n".join(normalize(t) for t in public_texts)
        self.grams = set()
        for text in list(self.keep) + [self.public]:
            ws = words(text)
            self.grams.update(tuple(ws[i:i + n]) for i in range(len(ws) - n + 1))
        # A run of words that crosses from the end of one kept string into the start of another
        # (e.g. two consecutive rules the owner kept) is not a leak, whatever order they were listed in.
        self.ends, self.starts = set(), set()
        for text in self.keep:
            ws = words(text)
            for k in range(1, min(n, len(ws) + 1)):
                self.ends.add(tuple(ws[-k:]))
                self.starts.add(tuple(ws[:k]))

    def covers(self, key):
        if MODEL_ID_RE.fullmatch(key):
            return True
        return any(key in k for k in self.keep) or (bool(self.public) and key in self.public)

    def covers_gram(self, gram):
        if gram in self.grams:
            return True
        return any(gram[:k] in self.ends and gram[k:] in self.starts for k in range(1, len(gram)))


def load_keep(path):
    """Accept a JSON list of strings, or a decisions.json with a "keep_strings" list."""
    if not path or not Path(path).exists():
        return [], []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data, []
    return data.get("keep_strings", []), data.get("proprietary_passages", [])


def load_public(dirs):
    texts = []
    for d in dirs or []:
        for p in sorted(Path(d).rglob("*")):
            if p.is_file() and "fixture" not in p.parts:
                try:
                    texts.append(p.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    pass
    return texts


def all_files(root):
    root = Path(root)
    return [str(p.relative_to(root)) for p in sorted(root.rglob("*")) if p.is_file()]


def _leak_checks(out_dir, candidates, source_docs, allow, cfg, canary_list):
    outputs = output_texts(out_dir)
    found = []
    found += checks.exact_strings(outputs, candidates, allow)
    found += checks.word_runs(outputs, source_docs, cfg["ngram_words"], allow)
    found += checks.secret_patterns(outputs, cfg)
    found += checks.canaries(outputs, canary_list)
    return outputs, found


def negative_control(out_dir, candidates, allow, cfg):
    """Plant one real source string in a copy of the output and confirm the scan catches it."""
    usable = [c for c in candidates if not allow.covers(normalize(c["text"]))
              and len(c["text"]) >= cfg["min_string_length"]]
    if not usable:
        return {"passed": False, "detail": "no source string available to test the scanner with"}
    probe = max(usable, key=lambda c: len(c["text"]))
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "out"
        shutil.copytree(out_dir, copy)
        page = copy / "index.html"
        if page.exists():
            text = page.read_text(encoding="utf-8")
            snippet = f"<p>{html.escape(probe['text'])}</p>"
            text = text.replace("</body>", snippet + "</body>") if "</body>" in text else text + snippet
            page.write_text(text, encoding="utf-8")
            planted = "index.html"
        else:
            (copy / "control.txt").write_text(probe["text"], encoding="utf-8")
            planted = "control.txt"
        hits = checks.exact_strings(output_texts(copy), [probe], allow)
    caught = any(h["file"] == planted for h in hits)
    return {"passed": caught, "planted_in": planted, "probe_where": probe["where"],
            "detail": "caught" if caught else "NOT caught: the scanner is not working on this output"}


def run(source, output, cfg, canaries_path=None, allow_path=None, public_dirs=(), paraphrase_on=False,
        api=paraphrase.call_api):
    out_dir = Path(output)
    keep, protected = load_keep(allow_path)
    allow = Allowlist(keep, load_public(public_dirs), cfg["ngram_words"])
    candidates = source_candidates(source, cfg["min_string_length"], cfg["min_line_length"])
    source_docs = source_word_index(source)
    canary_list = []
    if canaries_path and Path(canaries_path).exists():
        from .canaries import load
        canary_list = load(canaries_path)

    outputs, findings = _leak_checks(out_dir, candidates, source_docs, allow, cfg, canary_list)
    findings += checks.hidden_files(all_files(out_dir))
    findings += checks.data_match(out_dir)

    warnings, usage = [], {}
    if paraphrase_on and protected:
        warnings, usage = paraphrase.check(outputs, protected, cfg["model"], api=api)

    control = negative_control(out_dir, candidates, allow, cfg)
    canary_hits = {f["text"] for f in findings if f["check"].startswith("canary:")}
    clean = not findings and control["passed"]
    return {
        "clean": clean,
        "files_scanned": all_files(out_dir),
        "source_strings_checked": len(candidates),
        "allowlist_entries": len(keep),
        "canaries": {"planted": len(canary_list), "found": len(canary_hits)},
        "negative_control": control,
        "findings": findings,
        "warnings": warnings,
        "paraphrase_usage": usage,
    }


def mask(text):
    text = str(text)
    return f"{text[:3]}... ({len(text)} chars)" if len(text) > 3 else "***"


def to_markdown(report):
    """A report safe to show the owner or paste anywhere: matched text is masked."""
    lines = ["## Leak scan: " + ("PASSED" if report["clean"] else "FAILED"), ""]
    nc = report["negative_control"]
    lines += [
        f"- Files scanned: {len(report['files_scanned'])}",
        f"- Strings from your project checked: {report['source_strings_checked']}",
        f"- Canaries found in the demo: {report['canaries']['found']} of {report['canaries']['planted']} (must be 0)",
        f"- Scanner self-test (a known string planted on purpose): {nc['detail']}",
        f"- Problems: {len(report['findings'])}",
        f"- Warnings for you to review: {len(report['warnings'])}",
    ]
    if report["findings"]:
        lines += ["", "| Check | File | Match (masked) | Comes from |", "|---|---|---|---|"]
        for f in report["findings"][:50]:
            lines.append(f"| {f['check']} | {f['file']} | {mask(f['text'])} | {f['where']} |")
        if len(report["findings"]) > 50:
            lines.append(f"| ... | {len(report['findings']) - 50} more | | |")
    if report["warnings"]:
        lines += ["", "Warnings (possible rewording of text you marked PROPRIETARY):", ""]
        for w in report["warnings"]:
            lines.append(f"- {w['where'] or 'check'}: {mask(w['text'])} {w.get('reason', '')}".rstrip())
    return "\n".join(lines) + "\n"


def summary_counts(report):
    """Counts only, no text: used in the public SANITISATION.md."""
    nc = report["negative_control"]
    return "\n".join([
        "| Check | Result |",
        "|---|---|",
        f"| Files in this demo scanned | {len(report['files_scanned'])} |",
        f"| Strings from the private project checked against the demo | {report['source_strings_checked']} |",
        f"| Exact copies found | {sum(f['check'] == 'exact' for f in report['findings'])} |",
        f"| Copied runs of words found | {sum(f['check'] == 'word_run' for f in report['findings'])} |",
        f"| Secret patterns found (keys, emails, private links, IDs) | {sum(f['check'].startswith('pattern:') for f in report['findings'])} |",
        f"| Canaries (planted fake strings) found | {report['canaries']['found']} of {report['canaries']['planted']} |",
        f"| Scanner self-test | {'passed' if nc['passed'] else 'failed'} |",
        f"| Possible rewording warnings reviewed by a person | {len(report['warnings'])} |",
    ])
