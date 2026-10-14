"""Tests for the interactive diagram, the file contract and the video scripts.

Run from the repo root: python3 -m unittest discover -s tests -t .
Tests that need Node.js, Playwright or FFmpeg are skipped when those are missing.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "portfolio-demo" / "skills" / "portfolio-demo"
VIDEO = ROOT / "plugins" / "portfolio-demo" / "skills" / "portfolio-video"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(VIDEO / "scripts"))

import build_page  # noqa: E402
import fill_report  # noqa: E402
import make_audio  # noqa: E402
import render_diagram  # noqa: E402
import video_preflight  # noqa: E402
from scanner import scan  # noqa: E402
from scanner.config import load  # noqa: E402

PAGE = ROOT / "tests" / "fixtures" / "page"
SCAN = ROOT / "tests" / "fixtures" / "scanner"
EXAMPLE = SKILL / "vendor" / "archify" / "examples" / "agent-tool-call.workflow.json"
PUBLIC = [str(SKILL / d) for d in ("templates", "vendor/archify/assets", "vendor/archify/renderers")]


def has_playwright():
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)


class DiagramJson(Tmp):
    def write(self, data):
        p = self.tmp / "d.json"
        p.write_text(json.dumps(data))
        return p

    def test_refuses_fields_that_name_private_files(self):
        data = json.loads(EXAMPLE.read_text())
        data["meta"]["repository"] = {"origin": "https://example.com/x.git"}
        data["nodes"][0]["sources"] = [{"path": "secret/app.py"}]
        data["nodes"][1]["brand"] = "github"
        _, problems = render_diagram.check_json(self.write(data))
        self.assertEqual(len(problems), 3)

    def test_refuses_other_diagram_types(self):
        _, problems = render_diagram.check_json(self.write({"diagram_type": "architecture"}))
        self.assertTrue(problems)

    def test_no_node_means_fallback(self):
        out = self.tmp / "out"
        out.mkdir()
        (out / "diagram.html").write_text("old")
        old = render_diagram.find_node
        render_diagram.find_node = lambda: None
        try:
            code = render_diagram.main(["--json", str(EXAMPLE), "--work", str(self.tmp / "w"), "--out", str(out)])
        finally:
            render_diagram.find_node = old
        self.assertEqual(code, render_diagram.FALLBACK)
        self.assertFalse((out / "diagram.html").exists(), "a stale diagram.html must not survive a fallback")

    @unittest.skipUnless(render_diagram.find_node(), "Node.js 18+ not installed")
    def test_renders_html_only_into_output(self):
        out = self.tmp / "out"
        code = render_diagram.main(["--json", str(EXAMPLE), "--work", str(self.tmp / "w"), "--out", str(out)])
        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["diagram.html"])
        # A second run must not trip over the first run's receipts.
        self.assertEqual(render_diagram.main(["--json", str(EXAMPLE), "--work", str(self.tmp / "w"),
                                              "--out", str(out)]), 0)


class PageEmbed(Tmp):
    def build(self):
        build_page.main(["--spec", str(PAGE / "spec.json"), "--plan", str(PAGE / "prompt_plan.json"),
                         "--results", str(PAGE / "results.json"), "--out", str(self.tmp)])
        return (self.tmp / "index.html").read_text()

    def test_svg_only_without_diagram_html(self):
        page = self.build()
        self.assertNotIn("<iframe", page)
        self.assertIn('class="diagram-static"', page)

    def test_embeds_diagram_html_and_keeps_svg(self):
        (self.tmp / "diagram.html").write_text("<!doctype html><title>d</title>")
        page = self.build()
        self.assertIn('<iframe src="diagram.html"', page)
        self.assertIn('sandbox="allow-scripts allow-downloads"', page)
        self.assertIn("frame-src 'self'", page)
        self.assertIn('class="diagram-static"', page)


class ScannerAdditions(Tmp):
    def out_dir(self):
        out = self.tmp / "out"
        shutil.copytree(SCAN / "output_clean", out)
        return out

    def run_scan(self, out, **kw):
        return scan.run(SCAN / "source", out, load(SKILL / "config.toml"), public_dirs=PUBLIC, **kw)

    def test_contract_rejects_receipts(self):
        out = self.out_dir()
        (out / "diagram.finalize.json").write_text("{}")
        contracts = load(SKILL / "config.toml")["contracts"]
        report = self.run_scan(out, contract=contracts["demo"])
        self.assertFalse(report["clean"])
        self.assertEqual([f["check"] for f in report["findings"]], ["contract"])

    def test_contract_allows_video_folder(self):
        out = self.out_dir()
        (out / "video").mkdir()
        (out / "video" / "share-copy.txt").write_text("An invented demo.")
        report = self.run_scan(out, contract=load(SKILL / "config.toml")["contracts"]["demo"])
        self.assertTrue(report["clean"], report["findings"])

    def test_working_file_leak_is_caught(self):
        out = self.out_dir()
        source_line = (SCAN / "source" / "prompts" / "rules.txt").read_text().splitlines()[0]
        scene = self.tmp / "scene.html"
        scene.write_text(f"<div>{source_line}</div><div>https://intranet.corp.test/x</div>")
        report = self.run_scan(out, extra_paths=[scene])
        checks = {f["check"] for f in report["findings"]}
        self.assertTrue(checks & {"exact", "word_run"}, report["findings"])
        self.assertIn("pattern:url", checks)
        self.assertEqual(report["working_files_scanned"], ["(working file) scene.html"])

    def test_bundled_font_is_not_a_secret(self):
        out = self.out_dir()
        template = (SKILL / "vendor" / "archify" / "assets" / "template.html").read_text()
        (out / "diagram.html").write_text(template)
        report = self.run_scan(out)
        self.assertEqual([f for f in report["findings"] if f["check"].startswith("pattern:")], [])

    def test_fill_report_refreshes_existing_table(self):
        out = self.tmp
        (out / "SANITISATION.md").write_text("# R\n\n<!-- PDK:SCAN_RESULTS -->\n\n## After\n")
        report = {"clean": True, "files_scanned": ["a"] * 6, "working_files_scanned": [], "source_strings_checked": 5,
                  "findings": [], "warnings": [], "canaries": {"planted": 10, "found": 0},
                  "negative_control": {"passed": True}}
        rp = out / "r.json"
        rp.write_text(json.dumps(report))
        fill_report.fill(out, rp)
        report["files_scanned"] = ["a"] * 10
        rp.write_text(json.dumps(report))
        fill_report.fill(out, rp)
        text = (out / "SANITISATION.md").read_text()
        self.assertEqual(text.count("| Check | Result |"), 1)
        self.assertIn("| Files in this demo scanned | 10 |", text)
        self.assertIn("## After", text)


class VideoPreflight(Tmp):
    def demo(self, scanned=True):
        d = self.tmp / "demo"
        d.mkdir()
        for name in ("index.html", "data.json", "diagram.svg", "README.md"):
            (d / name).write_text("x")
        table = "| Scanner self-test | passed |" if scanned else "<!-- PDK:SCAN_RESULTS -->"
        (d / "SANITISATION.md").write_text(f"# R\n\n{table}\n")
        return d

    def test_accepts_finished_demo(self):
        self.assertEqual(video_preflight.check_demo(self.demo()), [])

    def test_refuses_unscanned_demo(self):
        self.assertTrue(video_preflight.check_demo(self.demo(scanned=False)))

    def test_refuses_extra_files(self):
        d = self.demo()
        (d / "notes.txt").write_text("private")
        self.assertTrue(video_preflight.check_demo(d))

    def test_work_folder_must_be_outside_demo(self):
        d = self.demo()
        with self.assertRaises(SystemExit):
            video_preflight.main(["--demo", str(d), "--work", str(d / "w")])


class Audio(Tmp):
    def test_writes_wav_of_right_length(self):
        out = self.tmp / "a.wav"
        make_audio.write(out, make_audio.build(2.0, 112, "calm", [1.0], [1.5]))
        with wave.open(str(out)) as w:
            self.assertEqual(w.getnchannels(), 2)
            self.assertAlmostEqual(w.getnframes() / w.getframerate(), 2.0, places=2)


@unittest.skipUnless(has_playwright() and shutil.which("ffmpeg"), "Playwright or FFmpeg not installed")
class RenderVideo(Tmp):
    SCENE = """<!doctype html><body style="margin:0;background:#fff">
<div id="b" style="position:absolute;top:40px;height:40px;background:#1f5fbf"></div>
<img src="https://example.com/x.png">
<script>window.render=t=>{document.getElementById('b').style.width=(t*100)+'px'};window.READY=Promise.resolve();</script>"""

    def test_renders_and_blocks_outside_requests(self):
        import render_video
        work = self.tmp / "vwork"
        (work / "scene").mkdir(parents=True)
        (work / "scene" / "scene.json").write_text(json.dumps({"width": 320, "height": 180, "duration": 1, "fps": 10}))
        (work / "scene" / "index.html").write_text(self.SCENE)
        out = self.tmp / "video"
        code = render_video.main(["--work", str(work), "--out", str(out), "--poster", "0.5"])
        self.assertEqual(code, 1, "the request to example.com must be reported as blocked")
        self.assertTrue((out / "launch.mp4").exists() and (out / "launch.jpg").exists())
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                                str(out / "launch.mp4")], capture_output=True, text=True)
        self.assertIn("320,180", probe.stdout)


if __name__ == "__main__":
    unittest.main()
