# Interactive diagram rules (Archify)

The demo has two diagrams of the same flow:

- `diagram.svg`, hand-written by `STYLE.md`: one column, readable at 380px. Phones see this one.
- `diagram.html`, rendered by the bundled Archify renderer from a JSON file you write: wider,
  interactive (themes, path tracing, export). Screens 600px and wider see this one.

Both show **the same steps**: only steps the code performs plus steps the owner confirmed in
phase 2 (`confirmed_steps`). Nothing else.

Archify is vendored in `vendor/archify/` (MIT, see its `LICENSE` and `VENDORED_FROM`). You do not
need its own skill file. Read `vendor/archify/examples/agent-tool-call.workflow.json` for the shape
and `vendor/archify/schemas/workflow.schema.json` when you need a field. The example shows shape,
not content: use fresh IDs and wording.

## Write `WORK/demo/diagram.archify.json`

```json
{
  "schema_version": 2,
  "diagram_type": "workflow",
  "meta": {
    "title": "Same plain title as the page", "output": "diagram.html", "quality_profile": "showcase",
    "legend": { "entries": {
      "backend": { "label": "Automated step" },
      "database": { "label": "Reads stored data" },
      "external": { "label": "Outside input or a person" } } }
  },
  "lanes": [
    { "id": "auto", "label": "Automated" },
    { "id": "person", "label": "Person: done by hand" }
  ],
  "groups": [
    { "id": "by-hand", "label": "A person does this", "lane": "person", "fromCol": 3, "toCol": 3, "variant": "dashed" }
  ],
  "mainPath": ["in", "step1", "step2", "review", "out"],
  "nodes": [
    { "id": "review", "lane": "person", "col": 3, "type": "external", "icon": "person",
      "label": "Checks each draft", "sublabel": "before it is sent", "tag": "by a person" }
  ],
  "edges": [ { "from": "step2", "to": "review", "label": "draft reply" } ]
}
```

Rules:

1. **Workflow type only.** Lanes are rows; `col` is 0 to 5 (at most 6 columns). Steps on the main
   path move left to right; a step back to an earlier column is an edge with `"role": "return"`.
2. **A person's step is told apart by more than colour:** it sits in the lane labelled
   `Person: done by hand`, has `"icon": "person"` and `"tag": "by a person"`, and is inside a
   `dashed` group labelled `A person does this`. Automated steps use the other lanes and no person icon.
3. **Node types:** `backend` for an automated step (code or a model call), `database` for reading
   stored data, `external` for where input comes from and for a person's step. Keep the legend
   labels above, so the legend says what the colours mean in plain words.
4. **Every edge has a label** saying what moves along it, as in `diagram.svg`.
5. **Never add `meta.repository`, node `sources` or `brand`.** They would put private file names,
   repository links or real product logos into the public diagram. `render_diagram.py` refuses them.
   Do not pass `--repo-root`.
6. **No real names**, client system names, product names or URLs. Word each step freshly (the
   scanner checks this file too).
7. Leave out `meta.visual_preset`, `meta.animation`, `meta.viewBox` and node `width`: the defaults
   are right.

## Render it

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_diagram.py --json $WORK/demo/diagram.archify.json \
  --work $WORK/diagram --out <OUTPUT>
```

- Exit 0: `OUTPUT/diagram.html` is written. Archify's receipt files stay in `WORK/diagram/`.
- Exit 1: Archify rejected the layout. Its messages say exactly what to change (for example
  "at most 6 columns"). Fix the JSON and rerun, up to 3 times. If it still fails, tell the owner
  and continue with `diagram.svg` only.
- Exit 3: Node.js 18+ is not installed. Continue with `diagram.svg` only, and tell the owner they
  can install Node.js to get the interactive diagram next time.

If it says the diagram was not checked in a browser, that only means no Chrome or Chromium was
found; the diagram is still valid.
