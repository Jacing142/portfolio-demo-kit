"""Read text out of the source project and the demo output.

Nothing here is project-specific: files are handled by extension only.
"""

import csv
import html
import io
import json
import re
from pathlib import Path

CODE_EXT = {
    ".py", ".js", ".gs", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".java", ".kt", ".rb",
    ".php", ".go", ".cs", ".swift", ".rs", ".sql", ".sh", ".ps1", ".r", ".json", ".yml",
    ".yaml", ".toml", ".html", ".htm", ".css", ".vue", ".svelte", ".xml", ".ini", ".cfg",
}
TABLE_EXT = {".csv", ".tsv"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

# Quoted string literals on one line: "..." '...' `...`
LITERAL_RE = re.compile(r'"((?:[^"\\\n]|\\.){3,})"|\'((?:[^\'\\\n]|\\.){3,})\'|`((?:[^`\\]|\\.){3,})`')
# Python-style triple-quoted blocks
TRIPLE_RE = re.compile(r'"""(.*?)"""|\'\'\'(.*?)\'\'\'', re.S)
WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
JSON_STR_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def normalize(text):
    """Lower-case, unescape HTML, and collapse all whitespace to single spaces."""
    text = html.unescape(text)
    return " ".join(text.lower().split())


TAG_RE = re.compile(r"<[^>]+>")
MARKUP_EXT = {".html", ".htm", ".svg", ".xml"}


def strip_tags(text):
    return TAG_RE.sub(" ", text)


def words(text):
    return WORD_RE.findall(normalize(text))


def iter_files(root):
    root = Path(root)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def read_text(path):
    """Return file text, or None for binary files."""
    data = Path(path).read_bytes()
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def _mostly_letters(s):
    letters = sum(c.isalpha() for c in s)
    return letters >= max(4, len(s) * 0.5)


NUMBERISH_RE = re.compile(r"[\d\s:/.\-+,%$()]+")


def _identifier_like(value):
    """Short but specific: an ID, an email, or a name-like value (Capitalised Words).

    Excludes numbers, dates and ordinary phrases such as "THIRD EMAIL" or "on hold".
    """
    if len(value) < 5 or NUMBERISH_RE.fullmatch(value) or not any(c.isalnum() for c in value):
        return False
    parts = value.split()
    if len(parts) == 1:
        return True
    return len(parts) <= 4 and all(w[:1].isupper() and not w.isupper() for w in parts)


def source_candidates(root, min_string_length, min_line_length):
    """Strings from the source project that must not appear in the demo.

    Returns a list of dicts: {"text", "where"}. Three kinds are collected:
    code string literals, spreadsheet cells, and whole lines of text.
    """
    root = Path(root)
    seen = set()
    out = []

    def add(text, where, strict=True):
        text = text.strip().strip("\"'`").strip()
        key = normalize(text)
        if key in seen or (strict and not _mostly_letters(text)):
            return
        seen.add(key)
        out.append({"text": text, "where": where})

    for path in iter_files(root):
        text = read_text(path)
        if text is None:
            continue
        rel = str(path.relative_to(root))
        ext = path.suffix.lower()
        if ext in TABLE_EXT:
            delim = "\t" if ext == ".tsv" else ","
            rows = list(csv.reader(io.StringIO(text), delimiter=delim))
            counts = {}
            for row in rows[1:]:
                for c, cell in enumerate(row):
                    counts[(c, cell.strip())] = counts.get((c, cell.strip()), 0) + 1
            for r, row in enumerate(rows, 1):
                for c, cell in enumerate(row, 1):
                    value = cell.strip()
                    if len(value) >= min_string_length:
                        add(value, f"{rel} row {r} col {c}")
                    elif r > 1 and counts.get((c - 1, value)) == 1 and _identifier_like(value):
                        # A value that appears once in its column (a name, email, order number)
                        # identifies a row, so it is checked even when short.
                        add(value, f"{rel} row {r} col {c}", strict=False)
            continue
        if ext in CODE_EXT:
            for m in LITERAL_RE.finditer(text):
                lit = next(g for g in m.groups() if g is not None)
                line_no = text.count("\n", 0, m.start()) + 1
                for piece in re.split(r"\\n|\n", lit):
                    if len(piece.strip()) >= min_string_length:
                        add(piece, f"{rel} line {line_no}")
            for m in TRIPLE_RE.finditer(text):
                block = m.group(1) if m.group(1) is not None else m.group(2)
                line_no = text.count("\n", 0, m.start()) + 1
                for piece in block.splitlines():
                    if len(piece.strip()) >= min_string_length:
                        add(piece, f"{rel} line {line_no}")
        for n, line in enumerate(text.splitlines(), 1):
            if len(line.strip()) >= min_line_length:
                add(line, f"{rel} line {n}")
    return out


def source_word_index(root):
    """Every source file as a list of words, for the word-run check."""
    root = Path(root)
    docs = []
    for path in iter_files(root):
        text = read_text(path)
        if text is None:
            continue
        if path.suffix.lower() in MARKUP_EXT:
            text = strip_tags(text)
        docs.append((str(path.relative_to(root)), words(text)))
    return docs


def _json_strings(raw):
    parts = []
    for m in JSON_STR_RE.finditer(raw):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except ValueError:
            pass
    return "\n".join(parts)


def output_texts(root):
    """Each output file as (relative path, raw text, normalized searchable text).

    The searchable text covers the raw file, its HTML-unescaped form and any JSON
    string values decoded, so a leak cannot hide behind escaping.
    """
    root = Path(root)
    out = []
    for path in iter_files(root):
        raw = read_text(path)
        if raw is None:
            continue
        variants = [raw, html.unescape(raw), _json_strings(raw), _json_strings(html.unescape(raw))]
        joined = "\n".join(variants)
        out.append((str(path.relative_to(root)), joined, normalize(joined)))
    return out
