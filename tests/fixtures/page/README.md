# Page fixture

Invented inputs for testing `scripts/build_page.py` without an API key. The "generated" output in
`results.json` is a hand-written stand-in for a real API result, used only to check the page renders.

    python3 plugins/portfolio-demo/skills/portfolio-demo/scripts/build_page.py --spec tests/fixtures/page/spec.json \
      --plan tests/fixtures/page/prompt_plan.json \
      --results tests/fixtures/page/results.json --out /tmp/fixture-page
