"""Integration: the shipped config_sample.yaml drives all derivations."""
import os
import sys
import unittest

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
import species_config as sc  # noqa: E402

SAMPLE = os.path.join(REPO_ROOT, "config_sample.yaml")


class TestConfigSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SAMPLE, encoding="utf-8") as f:
            cls.cfg = yaml.safe_load(f)

    def test_reference_count_default_one(self):
        self.assertEqual(self.cfg.get("reference_count"), 1)

    def test_species_have_cds_and_genome_only(self):
        loaded = sc.load_species(self.cfg)
        self.assertEqual([s["prefix"] for s in loaded], ["AA", "AB", "AC"])
        for s in loaded:
            self.assertTrue(s["cds"])
            self.assertTrue(s["genome"])

    def test_roles(self):
        self.assertEqual(sc.reference_prefixes(self.cfg), ["AA"])
        self.assertEqual(sc.hit_list_targets(self.cfg), ["AB", "AC"])
        self.assertEqual(
            sc.extract_hit_regions_targets(self.cfg), ["AA", "AB", "AC"]
        )

    def test_blastn_db_genomes_under_dl_data(self):
        for db in sc.blastn_db_databases(self.cfg):
            self.assertTrue(db["input"].startswith("../Materials/DL_data/"))
            self.assertTrue(db["output"].endswith(".fna"))

    def test_no_per_species_enumeration_left_in_sections(self):
        """The downstream sections must no longer enumerate species by hand."""
        self.assertNotIn("input_files", self.cfg.get("build_blastp_db", {}))
        self.assertNotIn("databases", self.cfg.get("gmap_build", {}))
        self.assertNotIn("databases", self.cfg.get("gmap", {}))
        self.assertNotIn("targets", self.cfg.get("make_hit_list", {}))
        self.assertNotIn("hit_files", self.cfg.get("make_complete_list", {}))
        self.assertNotIn("databases", self.cfg.get("build_blastn_db", {}))
        self.assertNotIn("databases", self.cfg.get("blastn_short", {}))
        self.assertNotIn("targets", self.cfg.get("extract_hit_regions", {}))
        self.assertNotIn("pair_files", self.cfg.get("make_primer_list", {}))
        self.assertNotIn("target", self.cfg.get("no_hit_analysis", {}) or {})
        self.assertNotIn("target", self.cfg.get("extract_nohit", {}))


if __name__ == "__main__":
    unittest.main()
