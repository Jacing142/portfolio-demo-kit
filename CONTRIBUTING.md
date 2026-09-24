# Contributing

## Layout

| Path | What |
|---|---|
| `.claude-plugin/marketplace.json` | Makes this repository a Claude Code plugin marketplace |
| `plugins/portfolio-demo/` | The plugin; `skills/portfolio-demo/` is the skill itself (SKILL.md, scripts, templates, config) |
| `tests/` | Tests for the scanner and the scripts, with invented fixtures |
| `examples/*/before/` | Invented projects to try the skill on; `after/` holds the skill's output |
| `docs/` | The website, served by GitHub Pages from `/docs` on `main` |

## Checks before a pull request

```bash
python3 -m unittest discover -s tests -t .
claude plugin validate .
claude plugin validate plugins/portfolio-demo
```

The scripts use the Python 3.11+ standard library only. Keep it that way, so the skill runs anywhere
without installing anything.
