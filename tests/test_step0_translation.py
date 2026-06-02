"""Tests for step0_translation: 6-digit gene IDs and prefix derivation."""
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATERIALS = os.path.join(REPO_ROOT, "Materials")
STEP0 = os.path.join(MATERIALS, "step0_translation.py")

sys.path.insert(0, MATERIALS)
import step0_translation as step0  # noqa: E402


def _headers(path):
    with open(path) as f:
        return [ln.strip() for ln in f if ln.startswith(">")]


class TestGeneIdFormat(unittest.TestCase):
    def setUp(self):
        self.codon = {"ATG": "M", "AAA": "K"}
        self.tmp = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.cwd)

    def _write_input(self, name="in.fna"):
        path = os.path.join(self.tmp, name)
        with open(path, "w") as f:
            f.write(">origID_alpha some description\nATGAAA\n")
            f.write(">origID_beta\nATGATG\n")
        return path

    def test_fasta_headers_are_six_digit(self):
        step0.process_species(self._write_input(), "AA", self.codon)
        self.assertEqual(
            _headers("AA/AA.aa.fasta"), [">AA_000001", ">AA_000002"]
        )
        self.assertEqual(
            _headers("AA/AA.cds.fasta"), [">AA_000001", ">AA_000002"]
        )

    def test_list_maps_six_digit_to_original_id(self):
        step0.process_species(self._write_input(), "AB", self.codon)
        with open("AB/AB.list") as f:
            lines = [ln.rstrip("\n") for ln in f]
        self.assertEqual(lines, ["000001\torigID_alpha", "000002\torigID_beta"])


class TestMainDerivesPrefixes(unittest.TestCase):
    """Integration: species is a {cds,genome} list; prefixes come from order."""

    def test_main_creates_prefix_dirs_from_species_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            dl = os.path.join(tmp, "DL_data")
            os.makedirs(dl)
            for name in ("first.fna", "second.fna"):
                with open(os.path.join(dl, name), "w") as f:
                    f.write(">g1\nATG\n")
            with open(os.path.join(tmp, "codon.txt"), "w") as f:
                f.write("ATG\tM\n")
            cfg = os.path.join(tmp, "config.yaml")
            with open(cfg, "w") as f:
                f.write(
                    "codon_file: codon.txt\n"
                    "reference_count: 1\n"
                    "species:\n"
                    "  - cds: first.fna\n"
                    "    genome: g_first.fna\n"
                    "  - cds: second.fna\n"
                    "    genome: g_second.fna\n"
                )
            result = subprocess.run(
                [sys.executable, STEP0, "config.yaml"],
                cwd=tmp, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "AA", "AA.aa.fasta")))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "AB", "AB.aa.fasta")))


if __name__ == "__main__":
    unittest.main()
