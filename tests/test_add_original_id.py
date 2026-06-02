"""Tests for add_original_id: 6-digit gene-ID regex and mapping."""
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "Primer3"))
import add_original_id as aid  # noqa: E402


class TestGeneIdPattern(unittest.TestCase):
    def test_matches_six_digit_and_strips_idx(self):
        m = aid.GENE_ID_PATTERN.match("AA_000001_0")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "AA_000001")
        m2 = aid.GENE_ID_PATTERN.match("AB_000123_5")
        self.assertEqual(m2.group(1), "AB_000123")

    def test_rejects_old_gene_format(self):
        self.assertIsNone(aid.GENE_ID_PATTERN.match("AA_gene1_0"))


class TestLoadMapping(unittest.TestCase):
    def test_builds_prefixed_keys_from_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "AA"))
            with open(os.path.join(tmp, "AA", "AA.list"), "w") as f:
                f.write("000001\torigA\n000002\torigB\n")
            mapping = aid.load_mapping([{"prefix": "AA"}], tmp)
            self.assertEqual(
                mapping, {"AA_000001": "origA", "AA_000002": "origB"}
            )


class TestAnnotate(unittest.TestCase):
    def test_appends_original_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.tab")
            out = os.path.join(tmp, "out.tab")
            with open(inp, "w") as f:
                f.write("AA_000001_0\tPRIMERSEQ\n")
            rows = aid.annotate(inp, out, {"AA_000001": "origA"})
            self.assertEqual(rows, 1)
            with open(out) as f:
                self.assertEqual(f.read(), "AA_000001_0\tPRIMERSEQ\torigA\n")


if __name__ == "__main__":
    unittest.main()
