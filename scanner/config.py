"""Load scan settings from config.toml, with safe defaults for anything missing."""

import tomllib
from pathlib import Path

DEFAULTS = {
    "min_string_length": 12,
    "min_line_length": 30,
    "ngram_words": 6,
    "paraphrase_check": False,
    "allowed_email_domains": ["example.com", "example.org", "example.net"],
    "allowed_url_hosts": ["example.com", "example.org", "example.net", "www.w3.org"],
    "patterns": [
        "anthropic_key", "openai_key", "aws_access_key", "github_token", "slack_token",
        "google_api_key", "jwt", "private_key", "secret_assignment", "email",
        "url", "private_ip", "long_id",
    ],
    "extra_patterns": {},
}


def load(path=None):
    """Return the [scan] settings merged over DEFAULTS, plus the model and pricing tables."""
    cfg = dict(DEFAULTS)
    model = "claude-sonnet-5"
    if path and Path(path).exists():
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
        cfg.update(data.get("scan", {}))
        model = data.get("model", {}).get("agent", model)
    cfg["model"] = model
    return cfg
