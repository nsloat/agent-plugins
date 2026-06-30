import sys
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
