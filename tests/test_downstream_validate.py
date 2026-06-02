"""Regression: stage scripts must work when their (now-removed) config
sections are absent, deriving everything from the 'species' list."""
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "GMAP"))
sys.path.insert(0, os.path.join(REPO_ROOT, "BLASTP"))
import make_hit_list  # noqa: E402
import pick_nohit_genes  # noqa: E402


def _cfg():
    # No 'make_hit_list' / 'no_hit_analysis' sections — they were removed.
    return {
        "species": [
            {"cds": "a.fna", "genome": "ag.fna"},
            {"cds": "b.fna", "genome": "bg.fna"},
            {"cds": "c.fna", "genome": "cg.fna"},
        ],
        "reference_count": 1,
    }


class TestMakeHitListWithoutSection(unittest.TestCase):
    def test_derives_targets_when_section_absent(self):
        hit_config = make_hit_list.validate_config(_cfg())
        self.assertEqual(
            [t["prefix"] for t in hit_config["targets"]], ["AB", "AC"]
        )


class TestPickNohitWithoutSection(unittest.TestCase):
    def test_returns_reference_when_section_absent(self):
        self.assertEqual(pick_nohit_genes.validate_config(_cfg()), ["AA"])


if __name__ == "__main__":
    unittest.main()
