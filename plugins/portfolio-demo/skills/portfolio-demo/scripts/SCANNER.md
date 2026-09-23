# Leak scanner

Checks the demo output folder against the private project before anything is packaged.
Python 3.11+ standard library only. No project-specific code: every setting is in `config.toml` under `[scan]`.

## Checks

| Check | Fails the scan? | What it looks for |
|---|---|---|
| `exact` | yes | Strings from the project in the output: code string literals, spreadsheet cells, lines of text. Case, whitespace, HTML escaping and JSON escaping are ignored. Short spreadsheet values that identify a row (a name, an email, an order number) are checked as whole words. |
| `word_run` | yes | Any run of `ngram_words` (default 6) consecutive words copied from any project file. |
| `pattern:*` | yes | API keys (Anthropic, OpenAI, AWS, GitHub, Slack, Google), JWTs, private keys, `password = "..."`, emails outside the allowed domains, links outside the allowed hosts, private IP addresses, long mixed-case IDs, plus any `extra_patterns`. |
| `canary:*` | yes | Any of the 10 canaries planted in the working copy. All must be absent. |
| `data_match` | yes | `index.html`'s inline data and `data.json` must hold the same data. |
| `hidden_file` | yes | Hidden files or folders (such as `.git`) in the output. |
| negative control | yes | One real project string is planted in a temporary copy of the output; the scan must catch it, or the whole scan fails. |
| `paraphrase` | no, warning | Optional. Asks the model whether text the owner marked PROPRIETARY was reworded into the demo. For a person to review. |

Not flagged: strings the owner chose to KEEP (`keep_strings` in `decisions.json`), text already
public in this skill's `templates/` folder, and model names such as `claude-sonnet-5`.

## Commands

```bash
python3 scripts/leak_scan.py plant --src PROJECT --dst WORK/copy --out WORK/private/canaries.json
python3 scripts/leak_scan.py scan --source WORK/copy --output OUTPUT \
    --canaries WORK/private/canaries.json --allow WORK/decisions.json \
    [--paraphrase] [--report WORK/scan/report.json] [--markdown WORK/scan/report.md]
python3 scripts/leak_scan.py patterns some-file-or-folder     # secret patterns only
```

Exit codes: `0` clean, `1` leaks found, `2` self-test failed or bad input.
`--report` holds the matched text in full: keep it in WORK, never in OUTPUT. `--markdown` masks every match.

## Tests

From the root of the portfolio-demo-kit repository:

```bash
python3 -m unittest discover -s tests -t .
```

Fixtures in `tests/fixtures/` are invented.
