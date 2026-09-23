"""Scanner tests. Run from the repo root: python3 -m unittest discover -s tests -t ."""

import html
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "portfolio-demo" / "skills" / "portfolio-demo"
sys.path.insert(0, str(SKILL / "scripts"))

from scanner import canaries, checks, scan  # noqa: E402
from scanner.__main__ import main  # noqa: E402
from scanner.config import load  # noqa: E402
from scanner.extract import output_texts, source_candidates  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "scanner"
SOURCE = FIX / "source"
CLEAN = FIX / "output_clean"
CFG = load(SKILL / "config.toml")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.out = self.tmp / "out"
        shutil.copytree(CLEAN, self.out)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_scan(self, canaries_path=None, allow_path=None, **kw):
        return scan.run(SOURCE, self.out, CFG, canaries_path, allow_path, [], **kw)

    def add_to_page(self, text, escape=True):
        page = self.out / "index.html"
        body = html.escape(text) if escape else text
        page.write_text(page.read_text().replace("</body>", f"<p>{body}</p></body>"))

    def checks_hit(self, report):
        return {f["check"] for f in report["findings"]}


class CleanOutput(Base):
    def test_clean_fixture_passes(self):
        report = self.run_scan()
        self.assertEqual(report["findings"], [], report["findings"])
        self.assertTrue(report["negative_control"]["passed"])
        self.assertTrue(report["clean"])

    def test_cli_exit_codes(self):
        self.assertEqual(main(["scan", "--source", str(SOURCE), "--output", str(self.out), "--public", str(self.tmp / "none")]), 0)
        self.add_to_page("Oswin Farrowdale")
        self.assertEqual(main(["scan", "--source", str(SOURCE), "--output", str(self.out), "--public", str(self.tmp / "none")]), 1)


class ExactStrings(Base):
    def test_code_literal(self):
        self.add_to_page("You are a careful assistant for the Quillmoor lending desk.")
        self.assertIn("exact", self.checks_hit(self.run_scan()))

    def test_csv_cell_long(self):
        self.add_to_page("Wants the bridging loan extended by six weeks")
        self.assertIn("exact", self.checks_hit(self.run_scan()))

    def test_csv_short_unique_value(self):
        self.add_to_page("Customer Idris Mawhinney called.")
        hits = [f for f in self.run_scan()["findings"] if f["check"] == "exact"]
        self.assertTrue(any(f["text"] == "Idris Mawhinney" for f in hits))

    def test_short_value_needs_whole_word(self):
        # A repeated category like "Lending" is not an identifier, and substrings do not count.
        self.add_to_page("Lending is a category.")
        self.assertEqual(self.run_scan()["findings"], [])

    def test_generic_phrase_cell_not_identifier(self):
        from scanner.extract import _identifier_like
        self.assertTrue(_identifier_like("Idris Mawhinney"))
        self.assertTrue(_identifier_like("PK-204981"))
        self.assertFalse(_identifier_like("THIRD EMAIL"))
        self.assertFalse(_identifier_like("on hold"))
        self.assertFalse(_identifier_like("processing"))
        self.assertTrue(_identifier_like("Mawhinney"))
        self.assertTrue(_identifier_like("jo@example.test"))
        self.assertFalse(_identifier_like("2026-04-14 08:02"))

    def test_model_name_is_public(self):
        allow = scan.Allowlist()
        self.assertTrue(allow.covers("claude-sonnet-5"))
        self.assertFalse(allow.covers("quillmoor lending"))

    def test_text_line(self):
        self.add_to_page("Never mention the internal risk band to the applicant under any circumstances.")
        self.assertIn("exact", self.checks_hit(self.run_scan()))

    def test_hidden_in_json_escaping(self):
        data = json.loads((self.out / "data.json").read_text())
        data["cases"][0]["output"] = "Note: Asked about early repayment fees again"
        (self.out / "data.json").write_text(json.dumps(data, ensure_ascii=True))
        self.assertIn("exact", self.checks_hit(self.run_scan()))

    def test_case_and_whitespace_ignored(self):
        self.add_to_page("NEVER mention   the internal risk band\n to the applicant under any circumstances.")
        self.assertIn("exact", self.checks_hit(self.run_scan()))


class WordRuns(Base):
    def test_six_word_run(self):
        self.add_to_page("We reworded it but kept: summarise the applicant note in two sentences, then more.")
        self.assertIn("word_run", self.checks_hit(self.run_scan()))

    def test_five_words_ok(self):
        self.add_to_page("Summarise the applicant note in.")
        self.assertNotIn("word_run", self.checks_hit(self.run_scan()))


class Patterns(Base):
    def test_each_pattern(self):
        samples = {
            "anthropic_key": "sk-ant-api03-abcdefghijklmnop",
            "aws_access_key": "AKIAABCDEFGHIJKLMNOP",
            "github_token": "ghp_" + "a1" * 18,
            "email": "someone@realcompany.test",
            "url": "https://intranet.corp.test/page",
            "private_ip": "10.0.12.7",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----",
            "secret_assignment": 'password = "hunter2hunter2"',
            "long_id": "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
        }
        for name, value in samples.items():
            with self.subTest(name=name):
                shutil.rmtree(self.out)
                shutil.copytree(CLEAN, self.out)
                self.add_to_page(value)
                self.assertIn(f"pattern:{name}", self.checks_hit(self.run_scan()))

    def test_allowed_email_and_url(self):
        self.add_to_page("Write to demo@example.com or see https://example.org/x")
        self.assertEqual(self.run_scan()["findings"], [])

    def test_extra_pattern_from_config(self):
        cfg = dict(CFG, extra_patterns={"staff_id": r"EMP-\d{6}"})
        self.add_to_page("EMP-123456")
        hits = checks.secret_patterns(output_texts(self.out), cfg)
        self.assertTrue(any(h["check"] == "pattern:staff_id" for h in hits))


class Canaries(Base):
    def test_plant_puts_all_ten_in_copy(self):
        cl = canaries.plant(SOURCE, self.tmp / "copy", canaries.make(seed=1))
        self.assertEqual(len(cl), 10)
        self.assertEqual({c["kind"] for c in cl}, {"name", "email", "key", "id", "sentence"})
        text = "".join(p.read_text() for p in (self.tmp / "copy").rglob("*") if p.is_file())
        for c in cl:
            self.assertIn(c["value"], text)
            self.assertTrue(c["planted_in"])
        # the original is untouched
        self.assertNotIn(cl[0]["value"], (SOURCE / "people.csv").read_text())

    def test_never_planted_in_text_or_markdown(self):
        cl = canaries.plant(SOURCE, self.tmp / "copy", canaries.make(seed=3))
        self.assertEqual((self.tmp / "copy" / "prompts" / "rules.txt").read_text(),
                         (SOURCE / "prompts" / "rules.txt").read_text())
        self.assertFalse(any(c["planted_in"].endswith((".txt", ".md")) and c["planted_in"] != "pdk-notes.txt" for c in cl))

    def test_unique_per_run(self):
        a = {c["value"] for c in canaries.make()}
        b = {c["value"] for c in canaries.make()}
        self.assertFalse(a & b)

    def test_canary_in_output_fails(self):
        cl = canaries.make(seed=2)
        path = self.tmp / "canaries.json"
        canaries.save(cl, path)
        self.assertEqual(self.run_scan(canaries_path=path)["canaries"]["found"], 0)
        self.add_to_page(cl[4]["value"])  # the sentence
        report = self.run_scan(canaries_path=path)
        self.assertEqual(report["canaries"]["found"], 1)
        self.assertFalse(report["clean"])


class Allowlist(Base):
    def test_keep_decision_allows_string(self):
        text = "You are a careful assistant for the Quillmoor lending desk."
        self.add_to_page(text)
        allow = self.tmp / "decisions.json"
        allow.write_text(json.dumps({"keep_strings": [text]}))
        self.assertEqual(self.run_scan(allow_path=allow)["findings"], [])

    def test_run_across_two_kept_lines_allowed(self):
        a = "Never mention the internal risk band to the applicant under any circumstances."
        b = "Always close with the phrase: your file stays with the Quillmoor desk."
        self.add_to_page(a + " " + b)
        allow = self.tmp / "decisions.json"
        allow.write_text(json.dumps({"keep_strings": [a, b]}))
        self.assertEqual(self.run_scan(allow_path=allow)["findings"], [])

    def test_public_template_text_ignored(self):
        public = self.tmp / "public"
        public.mkdir()
        (public / "t.html").write_text("Always close with the phrase: your file stays with the Quillmoor desk.")
        self.add_to_page("Always close with the phrase: your file stays with the Quillmoor desk.")
        report = scan.run(SOURCE, self.out, CFG, None, None, [public])
        self.assertEqual(report["findings"], [])


class NegativeControl(Base):
    def test_control_runs_and_passes(self):
        nc = self.run_scan()["negative_control"]
        self.assertTrue(nc["passed"])
        self.assertEqual(nc["planted_in"], "index.html")

    def test_control_fails_when_matching_is_broken(self):
        # Simulate a broken scanner: exact matching that never finds anything.
        original = checks.exact_strings
        checks.exact_strings = lambda *a, **k: []
        try:
            report = self.run_scan()
        finally:
            checks.exact_strings = original
        self.assertFalse(report["negative_control"]["passed"])
        self.assertFalse(report["clean"])

    def test_control_fails_without_source_strings(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        report = scan.run(empty, self.out, CFG, None, None, [])
        self.assertFalse(report["negative_control"]["passed"])
        self.assertFalse(report["clean"])

    def test_control_does_not_touch_real_output(self):
        before = (self.out / "index.html").read_text()
        self.run_scan()
        self.assertEqual(before, (self.out / "index.html").read_text())


class Structure(Base):
    def test_data_mismatch(self):
        (self.out / "data.json").write_text(json.dumps({"title": "changed"}))
        self.assertIn("data_match", self.checks_hit(self.run_scan()))

    def test_hidden_files_and_git(self):
        (self.out / ".git").mkdir()
        (self.out / ".git" / "config").write_text("x")
        self.assertIn("hidden_file", self.checks_hit(self.run_scan()))


class Paraphrase(Base):
    def test_warnings_only(self):
        allow = self.tmp / "decisions.json"
        allow.write_text(json.dumps({"keep_strings": [], "proprietary_passages": ["Never mention the risk band."]}))

        def fake_api(model, system, user, max_tokens=2000):
            self.assertIn("Never mention the risk band.", user)
            return '{"matches": [{"protected_index": 0, "demo_excerpt": "does not reveal bands", "reason": "same rule"}]}', {"input_tokens": 10}

        report = self.run_scan(allow_path=allow, paraphrase_on=True, api=fake_api)
        self.assertEqual(len(report["warnings"]), 1)
        self.assertTrue(report["clean"])  # warnings do not block

    def test_api_error_becomes_warning(self):
        allow = self.tmp / "decisions.json"
        allow.write_text(json.dumps({"proprietary_passages": ["x"]}))

        def broken(*a, **k):
            raise RuntimeError("offline")

        report = self.run_scan(allow_path=allow, paraphrase_on=True, api=broken)
        self.assertIn("did not run", report["warnings"][0]["text"])


class EntryPoint(Base):
    def test_leak_scan_script_runs_from_any_directory(self):
        import os
        import subprocess
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "leak_scan.py"), "scan",
                            "--source", str(SOURCE), "--output", str(self.out)],
                           cwd=self.tmp, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASSED", r.stdout)

    def test_template_text_is_public_by_default(self):
        # Text from the skill's own templates is public, so it never counts as a leak.
        self.add_to_page("Every name, message and number here is invented.")
        self.assertEqual(main(["scan", "--source", str(SOURCE), "--output", str(self.out)]), 0)


class Reports(Base):
    def test_markdown_masks_matches(self):
        self.add_to_page("Oswin Farrowdale")
        md = scan.to_markdown(self.run_scan())
        self.assertIn("FAILED", md)
        self.assertNotIn("Oswin Farrowdale", md)
        self.assertNotIn("Farrowdale", md)

    def test_summary_has_no_text(self):
        self.add_to_page("Oswin Farrowdale")
        self.assertNotIn("Osw", scan.summary_counts(self.run_scan()))


class SourceExtraction(unittest.TestCase):
    def test_extracts_literals_cells_lines(self):
        texts = {c["text"] for c in source_candidates(SOURCE, 12, 30)}
        self.assertIn("You are a careful assistant for the Quillmoor lending desk.", texts)
        self.assertIn("oswin.farrowdale@quillmoor.test", texts)
        self.assertIn("Always close with the phrase: your file stays with the Quillmoor desk.", texts)


if __name__ == "__main__":
    unittest.main()
