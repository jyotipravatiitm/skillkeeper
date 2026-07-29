import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from skillkeeper.cli import parser
from skillkeeper.core import candidate_diff, evaluate, heal, health, load_cases, load_skill, promote, rollback, scan
from skillkeeper.store import Store


WEAK_SKILL = """---
name: demo-skill
description: Create demo presentations when a user asks for a slide deck.
---

# Demo

Identify the audience and create a title, agenda, content slides, and conclusion.
"""


TRAIN_CASE = {
    "id": "train",
    "skill": "demo-skill",
    "requirements": [
        {
            "id": "focus",
            "signals": ["one idea per slide", "answer-first title"],
            "repair": "Keep one idea per slide and use an answer-first title.",
        },
        {
            "id": "qa",
            "signals": ["render", "inspect"],
            "repair": "Render the deck and inspect every slide.",
        },
    ],
}


HOLDOUT_CASE = {
    "id": "holdout",
    "skill": "demo-skill",
    "requirements": [
        {"id": "focus", "signals": ["one idea per slide", "answer-first title"]},
        {"id": "qa", "signals": ["render", "inspect"]},
    ],
}


class SkillkeeperTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.skill = self.root / "skills" / "demo-skill"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text(WEAK_SKILL, encoding="utf-8")
        self.cases = self.root / "cases"
        self.cases.mkdir()
        (self.cases / "train.json").write_text(json.dumps(TRAIN_CASE), encoding="utf-8")
        (self.cases / "holdout.json").write_text(json.dumps(HOLDOUT_CASE), encoding="utf-8")
        self.store = Store(self.root / "state")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_cli_reports_version(self):
        output = StringIO()
        with self.assertRaises(SystemExit) as exit_context, redirect_stdout(output):
            parser().parse_args(["--version"])
        self.assertEqual(exit_context.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), "skillkeeper 0.1.1")

    def test_scan_indexes_valid_skill(self):
        records = scan([self.root / "skills"], self.store)
        self.assertEqual(records[0]["name"], "demo-skill")
        self.assertEqual(records[0]["issues"], [])
        self.assertEqual(len(self.store.inventory()), 1)

    def test_heal_stages_without_changing_live_skill(self):
        train = load_cases([self.cases / "train.json"])
        holdout = load_cases([self.cases / "holdout.json"])
        baseline_hash = load_skill(self.skill).hash
        result = heal(self.skill, train, holdout, self.store)
        self.assertEqual(result["status"], "staged")
        self.assertEqual(result["before_score"], 0.0)
        self.assertEqual(result["after_score"], 1.0)
        self.assertEqual(result["holdout_score"], 1.0)
        self.assertEqual(load_skill(self.skill).hash, baseline_hash)
        self.assertIn("Quality contract", candidate_diff(self.store, result["candidate_id"]))

    def test_promote_and_rollback_are_audited(self):
        train = load_cases([self.cases / "train.json"])
        holdout = load_cases([self.cases / "holdout.json"])
        baseline_hash = load_skill(self.skill).hash
        candidate = heal(self.skill, train, holdout, self.store)
        promoted = promote(self.store, candidate["candidate_id"])
        self.assertNotEqual(load_skill(self.skill).hash, baseline_hash)
        restored = rollback(self.store, self.skill, Path(promoted["backup_path"]))
        self.assertEqual(restored["restored_hash"], baseline_hash)
        self.assertEqual(self.store.recent_events(1)[0]["event_type"], "skill.rolled_back")

    def test_health_exposes_replay_gap(self):
        cases = load_cases([self.cases / "train.json"])
        report = health(self.skill, cases)
        self.assertEqual(report["health"], 50.0)
        self.assertEqual(report["state"], "unhealthy")
        self.assertEqual(evaluate(self.skill, cases)["passed"], 0)

    def test_candidate_is_rejected_when_holdout_does_not_clear_gate(self):
        train = load_cases([self.cases / "train.json"])
        impossible = [{
            "id": "new-behavior",
            "skill": "demo-skill",
            "requirements": [{"id": "sources", "signals": ["source notes"]}],
        }]
        result = heal(self.skill, train, impossible, self.store)
        self.assertEqual(result["status"], "rejected")

    def test_promotion_rejects_a_tampered_candidate(self):
        train = load_cases([self.cases / "train.json"])
        holdout = load_cases([self.cases / "holdout.json"])
        candidate = heal(self.skill, train, holdout, self.store)
        staged = Path(candidate["candidate_path"]) / "SKILL.md"
        staged.write_text(staged.read_text(encoding="utf-8") + "\nTampered.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed after evaluation"):
            promote(self.store, candidate["candidate_id"])


if __name__ == "__main__":
    unittest.main()
