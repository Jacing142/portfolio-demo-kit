---
name: portfolio-demo
description: Turn a private client project into a safe public demo (static page, flow diagram, case-study README, sanitisation report). Use when asked to scan a project for sensitive content, classify what to keep/fake/remove, or build a portfolio demo from private work.
---

# Portfolio demo method

You turn a private project (any stack) into a public demo that shows what it does without exposing
anything sensitive. The owner decides what is kept, faked or removed. You never publish anything.

The same instructions run in two places:

- **GitHub Actions** (the normal route): Stage 1 runs phases 0-2 and writes an issue. Stage 2 runs
  phases 3-8 after the owner replies and comments `/build`. The workflow runs the scripts marked
  *(workflow)*; you run the rest.
- **Locally in Claude Code**: run every phase yourself, ask the phase 2 questions in the chat, and
  run the scripts in the order given in "Running locally" at the end.

## Ground rules

1. **Work only on the copy.** From phase 3 on, read the project only from `work/copy/`. Never read
   the canary list (it lives outside the repository on purpose) and never try to find the canaries.
2. **Invent, never alter.** Demo data is generated from the *structure* of the real data (column
   names, types, ranges, formats). Never start from a real row and change it.
3. **The owner's gate.** Anything the demo will *say* about production (who uses it, volumes,
   results, manual steps, other systems) must have been confirmed by the owner in phase 2. If it
   was not confirmed, leave it out.
4. **Plain words.** The owner is usually not technical. No jargon in anything they read.
5. **Never write a secret value** into the issue, the demo, or any file outside `work/`. Describe
   it and mask it: first 4 characters then `...`.
6. **Allowed placeholder data:** people's names you invent, emails on `example.com`,
   `example.org` or `example.net` only, order numbers and IDs in an obviously invented format
   (e.g. `EX-1001`), no real companies, products, places of work or assessment instruments.
7. **No external requests** in the demo: no fonts, scripts, images or links to other sites.

## Files you read and write

| Path | Who writes it | What |
|---|---|---|
| `work/preflight.md` | *(workflow)* `scripts/preflight.py` | file list, sizes, detected stack, warnings |
| `work/issue.md` | you, Stage 1 | the issue body, from `templates/stage1-issue.md` |
| `work/thread.md` | *(workflow)* `scripts/issue_thread.py` | the issue and the owner's replies |
| `work/copy/` | *(workflow)* `python3 -m scanner plant` | the project copy with 10 canaries planted |
| `work/decisions.json` | you, Stage 2 | the owner's decisions (format below). Frozen after your build step. |
| `work/demo/spec.json` | you | page content (format below) |
| `work/demo/prompt_plan.json` | you | the requests to run (format below) |
| `work/demo/diagram.svg` | you | the flow diagram, per `templates/diagram/STYLE.md` |
| `work/demo/results.json` | *(workflow)* `scripts/run_prompts.py` | real outputs from the API |
| `output/index.html`, `output/data.json`, `output/diagram.svg` | *(workflow)* `scripts/build_page.py` | the page. Never write these by hand. |
| `output/README.md` | you | case study, from `templates/case-study-README.md` |
| `output/SANITISATION.md` | you | report, from `templates/SANITISATION.md` |

Only `output/` goes into `demo.zip`, and only `output/` is scanned. Nothing else in `output/`.

---

## Phase 0: Preflight

1. Read `work/preflight.md` (or run `python3 scripts/preflight.py --folder <folder>` locally).
2. If there are no readable files, stop and say so in plain words.
3. Put this reminder at the top of what the owner reads: *You need permission to share this work
   publicly, and to send it to an AI provider for processing. If you are not sure, ask your client first.*
4. Note the detected stack. If a spreadsheet was uploaded as Excel, ask for CSV. If a sheet is very
   long, note that a 30-50 row sample is enough.

## Phase 1: Inventory and explain

1. Read every file in the project folder. Understand what it does end to end: inputs, each processing
   step, every prompt sent to a model, outputs, and where a person is involved.
2. Write the **5-line plain-English summary**: line 1 what it is for; lines 2-5 how it works.
3. List **everything sensitive or notable**, one row each. Look for:
   - PERSONAL: names, emails, phone numbers, addresses, employee or customer IDs, free-text answers
     written by people, anything that identifies someone.
   - PROPRIETARY: the client's name, product names, internal terms, prompt wording, scoring rules,
     target values, personas, policy text, business logic worth protecting.
   - SECRET: API keys, tokens, passwords, spreadsheet or document IDs, internal URLs, IP addresses,
     account numbers.
   - SAFE: generic code, standard library calls, public techniques.
   - UNSURE: anything you cannot place. Prefer UNSURE over guessing SAFE.
4. For each row propose KEEP, FAKE or REMOVE with a one-line reason. Default to FAKE for PERSONAL,
   REMOVE for SECRET, and FAKE or KEEP-with-owner-approval for PROPRIETARY.

## Phase 2: Classify and ask (the Stage 1 issue)

Fill `templates/stage1-issue.md` and write it to `work/issue.md`. It contains:

- the 5-line summary;
- the table, grouped PERSONAL, PROPRIETARY, SECRET, SAFE, UNSURE, numbered P1, R1, S1, K1, U1...;
- **questions the code cannot answer**, specific to this project:
  1. steps that happen outside the code (manual review, other scripts, who acts on the output);
  2. which parts to feature;
  3. anything about production the owner does not want stated publicly (and anything they do want stated);
  4. any other gap you noticed (e.g. "the prompt mentions a style guide that is not in the files").

Everything the demo will say about production goes through this gate: if the demo would describe it,
ask about it here. Keep the issue short enough to read on a phone. Do not include secret values.

Stage 1 stops here. Locally, ask the same questions in the chat and wait for answers.

## Phase 3: Plant canaries *(workflow)*

The workflow copies the project to `work/copy/` and inserts 10 unique fake strings (2 each of
name, email, key, ID, sentence). All later work uses the copy. If any canary reaches the demo, the
scan fails: it means a real row was copied instead of invented.

## Phase 4: Record decisions and make fake data

1. Read `work/thread.md`. Apply the owner's replies on top of your proposals. Where a reply is
   ambiguous, choose the safer option (FAKE over KEEP, REMOVE over FAKE) and say so in SANITISATION.md.
2. Write `work/decisions.json`:

```json
{
  "items": [{"id": "P1", "what": "Employee names", "group": "PERSONAL", "decision": "FAKE", "reason": "..."}],
  "keep_strings": ["exact text copied from the project that the owner said KEEP"],
  "proprietary_passages": ["text the owner marked PROPRIETARY, for the rewording check"],
  "confirmed_steps": ["steps the owner confirmed, in their words, for the diagram"],
  "do_not_state": ["things the owner does not want said publicly"]
}
```

   `keep_strings` is the scanner's allowlist: only exact strings from the project that the owner
   explicitly said to keep (e.g. trait names). Nothing else. If the owner said to keep the prompt
   wording, add each prompt passage. Never add anything to get a scan to pass.
3. Invent inputs from the structure: same columns, types, ranges and formats; realistic but clearly
   invented values. Include edge cases: an empty or very short answer, a very long one, an extreme
   value, a tricky case the logic has to handle. At most `max_demo_cases` in `config.toml`.

## Phase 5: Run the real logic and prompts on the fake data

1. **Prompts.** For each case, assemble the request exactly as the project would: its own system
   prompt, its own template, filled in with the invented input. Write `work/demo/prompt_plan.json`:

```json
{"cases": [{"id": "case-1", "system": "...", "messages": [{"role": "user", "content": "..."}]}]}
```

   If a prompt contains REMOVE or FAKE material (a client name, a real example), swap in the
   invented equivalent in the request too. Do not call the API yourself: the workflow runs
   `scripts/run_prompts.py`, which records the model the API reports.
2. **Logic.** Where the logic is portable (Python or JavaScript that runs without the client's
   systems), run it on the invented inputs and use its real results (e.g. scores, the assembled
   prompt). Where it is not (e.g. Apps Script calling SpreadsheetApp), reproduce the prompt
   assembly faithfully in the plan, and precompute anything else by reading the code carefully.
3. **Provenance.** Every output shown carries one label, set by `scripts/build_page.py`:
   - "Generated by <model> using this project's prompt on invented inputs": an API result exists.
   - "Illustrative, written by the agent": you wrote it (`output_illustrative` in spec.json).
   Use illustrative outputs only when a real run is impossible, and say why in SANITISATION.md.

## Phase 6: Build the page and diagram

1. **Diagram**: write `work/demo/diagram.svg` following `templates/diagram/STYLE.md`. Show only
   steps the code performs plus steps the owner confirmed (`confirmed_steps`). Nothing else.
2. **Page content**: write `work/demo/spec.json`:

```json
{
  "title": "Short plain title (no client name)",
  "tagline": "One sentence",
  "what_it_does": ["paragraph", "paragraph"],
  "built_with": "Python, the Anthropic API",
  "diagram": "diagram.svg",
  "diagram_caption": "Blue steps are automated. Dashed orange steps are done by a person.",
  "cases": [
    {"id": "case-1", "label": "What this example shows", "input": {"Field": "invented value"},
     "prompt_shown": "full"},
    {"id": "case-2", "label": "...", "input": "plain text is fine too",
     "prompt_shown": "summary", "prompt_summary": "What the prompt asks for, in one or two sentences",
     "output_illustrative": "only if this case cannot be run"}
  ],
  "not_shown": ["What the demo leaves out, in plain words"]
}
```

   `prompt_shown: "full"` only when the owner said to KEEP the prompt wording (and its passages are in
   `keep_strings`). Otherwise use `"summary"` with a `prompt_summary` in your own words.
3. **Case study**: fill `templates/case-study-README.md` into `output/README.md`.
4. **Report**: fill `templates/SANITISATION.md` into `output/SANITISATION.md`. Describe what was
   found without repeating it. Keep the `<!-- PDK:SCAN_RESULTS -->` line as it is.
5. Check your work builds: `python3 scripts/build_page.py --spec work/demo/spec.json --plan work/demo/prompt_plan.json --results work/demo/results.json --out output/`
   (before the prompts have run, cases without results are skipped; that is expected).

## Phase 7: Scan *(workflow)*

`python3 -m scanner scan --source work/copy --output output/ --canaries <list> --allow work/decisions.json`

It checks exact strings (code literals, spreadsheet cells, lines of text), runs of 6 or more words,
secret patterns, all 10 canaries, that `index.html` and `data.json` hold the same data, and runs a
self-test (one real string planted in a temporary copy must be caught). Nothing is produced until
it is clean.

**If you are asked to fix a failed scan** you get `work/scan/report.json`. For each finding:
find where the text came from (`where`), then change the *source of it* in `work/demo/` or
`output/README.md` / `output/SANITISATION.md`: replace it with invented text, reword it in your
own words, or drop it. Then rebuild the page. Never edit `work/decisions.json`, the scanner, its
config, or the canaries; never delete a case just to hide a finding without saying so in
SANITISATION.md.

## Phase 8: Package *(workflow)*

The workflow writes the scan counts into SANITISATION.md, rescans, zips `output/` (no hidden files,
no `.git`) into `demo.zip`, attaches it and SANITISATION.md to the run, and comments on the issue.

---

## Running locally in Claude Code

From the repository root, with `ANTHROPIC_API_KEY` set:

```bash
python3 scripts/preflight.py --folder input/                       # phase 0
# phases 1-2: you read the files and ask the owner in the chat
mkdir -p ../pdk-private
python3 -m scanner plant --src input/ --dst work/copy --out ../pdk-private/canaries.json   # phase 3
# phases 4-6: you write work/decisions.json, work/demo/*, output/README.md, output/SANITISATION.md
python3 scripts/run_prompts.py work/demo/prompt_plan.json work/demo/results.json          # phase 5
python3 scripts/build_page.py --spec work/demo/spec.json --plan work/demo/prompt_plan.json \
  --results work/demo/results.json --out output/                                          # phase 6
python3 -m scanner scan --source work/copy --output output/ --canaries ../pdk-private/canaries.json \
  --allow work/decisions.json --paraphrase --report work/scan/report.json                  # phase 7
python3 scripts/package_demo.py fill && python3 -m scanner scan --source work/copy --output output/ \
  --canaries ../pdk-private/canaries.json --allow work/decisions.json --report work/scan/report.json \
  && python3 scripts/package_demo.py zip                                                  # phase 8
```

`work/` and `output/` are ignored by git so nothing private is committed by accident.
