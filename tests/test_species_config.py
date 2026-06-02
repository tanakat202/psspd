"""Tests for species_config: prefix auto-numbering and species role derivation.

Run from the repository root:
    python3 -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import species_config as sc


class TestIndexToPrefix(unittest.TestCase):
    def test_first_block(self):
        self.assertEqual(sc.index_to_prefix(0), "AA")
        self.assertEqual(sc.index_to_prefix(1), "AB")
        self.assertEqual(sc.index_to_prefix(25), "AZ")

    def test_second_block_wraps(self):
        self.assertEqual(sc.index_to_prefix(26), "BA")
        self.assertEqual(sc.index_to_prefix(27), "BB")

    def test_last_valid(self):
        self.assertEqual(sc.index_to_prefix(675), "ZZ")

    def test_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            sc.index_to_prefix(676)
        with self.assertRaises(ValueError):
            sc.index_to_prefix(-1)


def _cfg(n=3, reference_count=None):
    species = [
        {"cds": f"cds_{i}.fna", "genome": f"genome_{i}.fna"} for i in range(n)
    ]
    cfg = {"species": species}
    if reference_count is not None:
        cfg["reference_count"] = reference_count
    return cfg


class TestLoadSpecies(unittest.TestCase):
    def test_assigns_prefixes_in_order(self):
        loaded = sc.load_species(_cfg(3))
        self.assertEqual([s["prefix"] for s in loaded], ["AA", "AB", "AC"])
        self.assertEqual([s["index"] for s in loaded], [0, 1, 2])

    def test_carries_cds_and_genome(self):
        loaded = sc.load_species(_cfg(2))
        self.assertEqual(loaded[0]["cds"], "cds_0.fna")
        self.assertEqual(loaded[0]["genome"], "genome_0.fna")

    def test_default_reference_count_is_one(self):
        loaded = sc.load_species(_cfg(3))
        self.assertEqual([s["is_reference"] for s in loaded], [True, False, False])

    def test_reference_count_two(self):
        loaded = sc.load_species(_cfg(3, reference_count=2))
        self.assertEqual([s["is_reference"] for s in loaded], [True, True, False])

    def test_missing_species_raises(self):
        with self.assertRaises(ValueError):
            sc.load_species({})

    def test_empty_species_raises(self):
        with self.assertRaises(ValueError):
            sc.load_species({"species": []})

    def test_entry_missing_cds_raises(self):
        with self.assertRaises(ValueError):
            sc.load_species({"species": [{"genome": "g.fna"}]})

    def test_entry_missing_genome_raises(self):
        with self.assertRaises(ValueError):
            sc.load_species({"species": [{"cds": "c.fna"}]})

    def test_reference_count_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            sc.load_species(_cfg(2, reference_count=0))
        with self.assertRaises(ValueError):
            sc.load_species(_cfg(2, reference_count=3))


class TestRoleHelpers(unittest.TestCase):
    def test_all_species(self):
        self.assertEqual(
            [s["prefix"] for s in sc.all_species(_cfg(3))], ["AA", "AB", "AC"]
        )

    def test_reference_and_other_default(self):
        cfg = _cfg(3)
        self.assertEqual([s["prefix"] for s in sc.reference_species(cfg)], ["AA"])
        self.assertEqual(
            [s["prefix"] for s in sc.other_species(cfg)], ["AB", "AC"]
        )

    def test_reference_and_other_count_two(self):
        cfg = _cfg(3, reference_count=2)
        self.assertEqual(
            [s["prefix"] for s in sc.reference_species(cfg)], ["AA", "AB"]
        )
        self.assertEqual([s["prefix"] for s in sc.other_species(cfg)], ["AC"])


class TestDerivationHelpers(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "species": [
                {"cds": "a_cds.fna", "genome": "a_gen.fna"},
                {"cds": "b_cds.fna", "genome": "b_gen.fna"},
                {"cds": "c_cds.fna", "genome": "c_gen.fna"},
            ],
            "reference_count": 1,
        }

    def test_blastp_input_files_all(self):
        self.assertEqual(
            sc.blastp_input_files(self.cfg),
            [
                "../Materials/AA/AA.aa.fasta",
                "../Materials/AB/AB.aa.fasta",
                "../Materials/AC/AC.aa.fasta",
            ],
        )

    def test_gmap_build_databases_other(self):
        self.assertEqual(
            sc.gmap_build_databases(self.cfg),
            [
                {"name": "AB", "genome": "../Materials/DL_data/b_gen.fna"},
                {"name": "AC", "genome": "../Materials/DL_data/c_gen.fna"},
            ],
        )

    def test_gmap_databases_other(self):
        self.assertEqual(
            sc.gmap_databases(self.cfg),
            [{"name": "AB", "output": "AB.gff3"}, {"name": "AC", "output": "AC.gff3"}],
        )

    def test_hit_list_targets_other(self):
        self.assertEqual(sc.hit_list_targets(self.cfg), ["AB", "AC"])

    def test_complete_list_hit_files_other(self):
        self.assertEqual(
            sc.complete_list_hit_files(self.cfg),
            ["../GMAP/AB_hit.tab", "../GMAP/AC_hit.tab"],
        )

    def test_blastn_db_databases_all(self):
        self.assertEqual(
            sc.blastn_db_databases(self.cfg),
            [
                {"name": "AA", "input": "../Materials/DL_data/a_gen.fna", "output": "AA.fna"},
                {"name": "AB", "input": "../Materials/DL_data/b_gen.fna", "output": "AB.fna"},
                {"name": "AC", "input": "../Materials/DL_data/c_gen.fna", "output": "AC.fna"},
            ],
        )

    def test_blastn_short_databases_all(self):
        self.assertEqual(
            sc.blastn_short_databases(self.cfg),
            [
                {"name": "AA", "db": "AA.fna", "output": "AA.out"},
                {"name": "AB", "db": "AB.fna", "output": "AB.out"},
                {"name": "AC", "db": "AC.fna", "output": "AC.out"},
            ],
        )

    def test_extract_hit_regions_targets_all(self):
        self.assertEqual(sc.extract_hit_regions_targets(self.cfg), ["AA", "AB", "AC"])

    def test_primer_pair_files_other(self):
        self.assertEqual(
            sc.primer_pair_files(self.cfg),
            ["AB_possiblePair.tab", "AC_possiblePair.tab"],
        )

    def test_reference_prefixes_and_pair_files(self):
        self.assertEqual(sc.reference_prefixes(self.cfg), ["AA"])
        self.assertEqual(sc.reference_pair_files(self.cfg), ["AA_possiblePair.tab"])

    def test_reference_count_two_shifts_partition(self):
        cfg = dict(self.cfg, reference_count=2)
        self.assertEqual(sc.reference_prefixes(cfg), ["AA", "AB"])
        self.assertEqual(sc.hit_list_targets(cfg), ["AC"])  # others
        self.assertEqual(sc.extract_hit_regions_targets(cfg), ["AA", "AB", "AC"])  # all


if __name__ == "__main__":
    unittest.main()
