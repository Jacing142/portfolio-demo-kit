# Contributing

## Layout

| Path | What |
|---|---|
| `.claude-plugin/marketplace.json` | Makes this repository a Claude Code plugin marketplace |
| `plugins/portfolio-demo/` | The plugin; `skills/portfolio-demo/` is the demo skill (SKILL.md, scripts, templates, config) and `skills/portfolio-video/` the video skill |
| `plugins/portfolio-demo/skills/portfolio-demo/vendor/archify/` | The Archify diagram renderer, copied unchanged (see below) |
| `tests/` | Tests for the scanner and the scripts, with invented fixtures |
| `examples/*/before/` | Invented projects to try the skill on; `after/` holds the skill's output |
| `docs/` | The website, served by GitHub Pages from `/docs` on `main` |

## Checks before a pull request

```bash
python3 -m unittest discover -s tests -t .
claude plugin validate .
claude plugin validate plugins/portfolio-demo
```

The demo scripts use the Python 3.11+ standard library only. Keep it that way, so the demo runs
anywhere without installing anything. Two parts are optional on purpose and must keep working
without their extras: the interactive diagram (Node.js 18+, falls back to `diagram.svg`) and the
video (Playwright and FFmpeg). Tests that need them are skipped when they are missing.

## Updating the bundled Archify

`vendor/archify/` is a copy of the `archify/` folder of https://github.com/tt-a1i/archify (MIT),
without its examples (except one workflow example), its generator scripts and its own `SKILL.md`
(kept as `ARCHIFY_SKILL.md`, so skill installers do not list it as a third skill).
`VENDORED_FROM` records the commit. To update: copy the same files from a newer commit, update
`VENDORED_FROM`, then run the tests and render `examples/python-support-triage` again. Do not edit
the vendored files.
