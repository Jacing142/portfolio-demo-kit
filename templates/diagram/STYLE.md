# Diagram style guide

Every diagram in this kit, and every diagram in a demo it builds, follows this guide.
Diagrams are hand-written SVG. No Mermaid, no drawing libraries, no external fonts or images.

## Rules

1. **Show only confirmed steps.** A demo diagram shows only the steps the owner confirmed in the Stage 1 issue. If a step happens outside the code (for example "a person reviews every draft"), it appears only if the owner said so, in the owner's words.
2. **Top to bottom, one column.** Boxes stack vertically so the diagram reads at 380px wide with no sideways scrolling.
3. **Two box types, told apart by more than colour.**
   - Automated step: blue solid outline, pale blue fill.
   - A person does or decides something: orange **dashed** outline, pale orange fill, and the word "Person:" at the start of the title.
4. **Every arrow has a label** saying what moves along it ("email text", "draft reply"). Labels sit to the right of the arrow.
5. **Plain words.** Box titles are 2 to 5 words. An optional second line (smaller, grey) says how, in under 40 characters.
6. **No real names**, product names of the client, internal system names or URLs.
7. **Legend.** End with a one-line legend (a small blue box labelled "Automated", a small dashed orange box labelled "A person does this") 22px below the last box; add 36 to the viewBox height.
8. **Accessible.** The `<svg>` has `role="img"` and an `aria-labelledby` pointing at a `<title>` and `<desc>` that describe the whole flow in one or two sentences.

## Measurements

| Item | Value |
|---|---|
| viewBox width | 360 |
| Box | x=32, width=296, height=64, rx=12 |
| Gap between boxes | 44 (arrow runs from box bottom +4 to next box top -4) |
| First box y | 16 |
| Box y for step i (from 0) | 16 + i x 108 |
| viewBox height | 16 + n x 108 - 44 + 16 |
| Title text | 15px, weight 600, x=180, centred, baseline at box y + 28 (or + 37 with no second line) |
| Second line | 12.5px, colour #4d5b6e, baseline at box y + 48 |
| Arrow | x=180, stroke #4d5b6e, width 2, arrowhead marker |
| Arrow label | 12.5px, colour #4d5b6e, x=192, baseline mid-gap |

## Colours

| Use | Colour |
|---|---|
| Automated outline | #1f5fbf |
| Automated fill | #e8f0fc |
| Person outline | #b35400 (dashed 6 4) |
| Person fill | #fdf0e4 |
| Text | #1b2533 |
| Secondary text and arrows | #4d5b6e |

## Skeleton

Copy this and add one `<g>` per step. See `example.svg` for a complete three-step diagram.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 288" role="img" aria-labelledby="t d"
     font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif">
  <title id="t">How the project works</title>
  <desc id="d">One sentence describing the flow from first step to last.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#4d5b6e"/>
    </marker>
  </defs>
  <!-- automated step -->
  <g>
    <rect x="32" y="16" width="296" height="64" rx="12" fill="#e8f0fc" stroke="#1f5fbf" stroke-width="2"/>
    <text x="180" y="44" text-anchor="middle" font-size="15" font-weight="600" fill="#1b2533">Step title</text>
    <text x="180" y="64" text-anchor="middle" font-size="12.5" fill="#4d5b6e">how, in a few words</text>
  </g>
  <!-- arrow with label -->
  <line x1="180" y1="84" x2="180" y2="120" stroke="#4d5b6e" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="192" y="106" font-size="12.5" fill="#4d5b6e">what moves</text>
  <!-- person step -->
  <g>
    <rect x="32" y="124" width="296" height="64" rx="12" fill="#fdf0e4" stroke="#b35400" stroke-width="2" stroke-dasharray="6 4"/>
    <text x="180" y="152" text-anchor="middle" font-size="15" font-weight="600" fill="#1b2533">Person: checks it</text>
    <text x="180" y="172" text-anchor="middle" font-size="12.5" fill="#4d5b6e">outside the code</text>
  </g>
</svg>
```

`url(#arrow)` is an in-document reference, which the page builder allows. Links to anything outside the SVG are rejected.
