# Page fixture

Invented inputs for testing `scripts/build_page.py` without an API key. The "generated" output in
`results.json` is a hand-written stand-in for a real API result, used only to check the page renders.

    python3 scripts/build_page.py --spec templates/demo-page/fixture/spec.json \
      --plan templates/demo-page/fixture/prompt_plan.json \
      --results templates/demo-page/fixture/results.json --out work/fixture-page
