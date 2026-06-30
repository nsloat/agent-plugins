import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import project_tool as pt


class TestSlugAndBranch:
    def test_slugify_basic(self):
        assert pt.slugify("Add Export Feature") == "Add-Export-Feature"

    def test_slugify_collapses_and_trims(self):
        assert pt.slugify("  fix//login  bug ") == "fix-login-bug"

    def test_slugify_keeps_safe_chars(self):
        assert pt.slugify("FEAT-42.v2") == "FEAT-42.v2"

    def test_resolve_branch_joins_parts(self):
        assert pt.resolve_branch("alice-co", "FEAT-42", "auth revamp") == \
            "alice-co/FEAT-42/auth-revamp"

    def test_resolve_branch_skips_empty_category(self):
        assert pt.resolve_branch("alice-co", "", "cleanup") == "alice-co/cleanup"


class TestConfig(unittest.TestCase):
    def _valid_cfg(self):
        return {
            "repos_root": "~/code",
            "projects_root": "~/projects",
            "branch_namespace": "alice-co",
            "agents_md_path": "~/AGENTS.md",
            "repos": [{"name": "api-service", "path": "~/code/api-service", "base": "main"}],
            "signal_rules": [{"match": ["terraform"], "repo": "ops-infra"}],
        }

    def test_save_then_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "nested" / "config.json"
            pt.save_config(self._valid_cfg(), p)
            self.assertTrue(p.exists())
            self.assertEqual(pt.load_config(p), self._valid_cfg())

    def test_validate_ok(self):
        self.assertEqual(pt.validate_config(self._valid_cfg()), [])

    def test_validate_missing_namespace(self):
        cfg = self._valid_cfg()
        cfg["branch_namespace"] = ""
        self.assertIn("branch_namespace must be non-empty", pt.validate_config(cfg))

    def test_validate_missing_key(self):
        cfg = self._valid_cfg()
        del cfg["repos"]
        self.assertTrue(any("repos" in e for e in pt.validate_config(cfg)))

    def test_validate_bad_repo_entry(self):
        cfg = self._valid_cfg()
        cfg["repos"].append({"name": "x"})
        errs = pt.validate_config(cfg)
        self.assertTrue(any("path" in e for e in errs))
        self.assertTrue(any("base" in e for e in errs))
