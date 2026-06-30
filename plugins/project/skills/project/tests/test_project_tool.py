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


import subprocess


def _init_repo(path: Path, branch: str):
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t.co"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)
    (path / "README.md").write_text("x\n")
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "init"], check=True)


class TestDiscovery(unittest.TestCase):
    def test_is_git_repo_true_and_false(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d) / "r"
            _init_repo(repo, "main")
            self.assertTrue(pt.is_git_repo(repo))
            self.assertFalse(pt.is_git_repo(Path(d)))

    def test_default_branch_local_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d) / "r"
            _init_repo(repo, "trunk")
            # No origin remote, so falls back to local branch detection
            self.assertEqual(pt.default_branch(repo), "trunk")

    def test_discover_repos_finds_and_sorts(self):
        with tempfile.TemporaryDirectory() as d:
            _init_repo(Path(d) / "beta", "main")
            _init_repo(Path(d) / "alpha", "master")
            (Path(d) / "not-a-repo").mkdir()
            repos = pt.discover_repos(d)
            names = [r["name"] for r in repos]
            self.assertEqual(names, ["alpha", "beta"])
            self.assertEqual(repos[0]["base"], "master")
            self.assertEqual(repos[1]["base"], "main")
            self.assertTrue(repos[0]["path"].endswith("/alpha"))


class TestSuggest(unittest.TestCase):
    RULES = [
        {"match": ["terraform", "infra", "kubernetes"], "repo": "ops-infra"},
        {"match": ["checkout", "frontend", "ui"], "repo": "web-frontend"},
    ]

    def test_suggests_on_keyword(self):
        text = "Update the terraform config for the API gateway"
        self.assertEqual(pt.suggest_repos(text, self.RULES), ["ops-infra"])

    def test_case_insensitive_and_dedup(self):
        text = "Terraform change plus another terraform tweak"
        self.assertEqual(pt.suggest_repos(text, self.RULES), ["ops-infra"])

    def test_multiple_repos_in_rule_order(self):
        text = "New checkout UI needs a new infra kubernetes config"
        self.assertEqual(pt.suggest_repos(text, self.RULES), ["ops-infra", "web-frontend"])

    def test_no_match_empty(self):
        self.assertEqual(pt.suggest_repos("unrelated text", self.RULES), [])

    def test_none_text_safe(self):
        self.assertEqual(pt.suggest_repos(None, self.RULES), [])


class TestAgentsMd(unittest.TestCase):
    def _cfg(self):
        return {"projects_root": "~/projects", "branch_namespace": "alice-co"}

    def test_block_is_marker_wrapped(self):
        block = pt.render_agents_block(self._cfg())
        self.assertTrue(block.startswith(pt.BLOCK_START))
        self.assertTrue(block.rstrip().endswith(pt.BLOCK_END))
        self.assertIn("alice-co", block)
        self.assertIn("~/projects", block)
        self.assertIn("/project new", block)

    def test_inject_appends_when_absent(self):
        content = "# AGENTS.md\n\nExisting content.\n"
        block = pt.render_agents_block(self._cfg())
        out = pt.inject_block(content, block)
        self.assertIn("Existing content.", out)
        self.assertIn(pt.BLOCK_START, out)
        self.assertIn(pt.BLOCK_END, out)

    def test_inject_is_idempotent(self):
        content = "# AGENTS.md\n\nExisting content.\n"
        block = pt.render_agents_block(self._cfg())
        once = pt.inject_block(content, block)
        twice = pt.inject_block(once, block)
        self.assertEqual(once, twice)
        self.assertEqual(once.count(pt.BLOCK_START), 1)

    def test_inject_replaces_existing_block(self):
        content = "# AGENTS.md\n\nExisting.\n"
        old = pt.inject_block(content, pt.render_agents_block({
            "projects_root": "~/old-projects", "branch_namespace": "old-ns"}))
        new = pt.inject_block(old, pt.render_agents_block(self._cfg()))
        self.assertIn("alice-co", new)
        self.assertNotIn("old-ns", new)
        self.assertEqual(new.count(pt.BLOCK_START), 1)
