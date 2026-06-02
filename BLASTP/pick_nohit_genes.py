#!/usr/bin/env python3
"""
Script to extract genes with no BLASTP hits

Usage:
    python3 pick_nohit_genes.py config.yaml

Reads the target species name from the config file (YAML format)
and analyzes BLASTP results to extract genes with no hits.
"""

import sys
import os
import re
import yaml
import argparse

# Make the repository-root shared module importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import species_config


def load_config(config_file):
    """
    Load YAML config file

    Args:
        config_file (str): Config file path

    Returns:
        dict: Configuration contents
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to load config file: {e}", file=sys.stderr)
        sys.exit(1)


def validate_config(config):
    """
    Validate configuration

    Args:
        config (dict): Configuration contents

    Returns:
        list: Reference species prefixes (the targets to analyze)
    """
    try:
        return species_config.reference_prefixes(config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _analyze_one(target, out_file):
    """Write the no-hit genes of a single target species to out_file."""
    blast_input = open("blastp.out", "r", encoding='utf-8')
    a = 0
    large_a = 0
    before_seq = ""
    seq_id = None
    while True:
        line = next(blast_input, "")
        if not line:  # End of file reached
            break

        parts = line.strip().split("\t")

        if len(parts) >= 2 and target in parts[0]:
            seq_id = parts[0]

            if (before_seq and re.search(r'\w', before_seq) and
                    seq_id not in before_seq):
                if large_a == 0:
                    print(f"{before_seq}", file=out_file)
                    a += 1

                large_a = 0
            if target not in parts[1]:
                large_a = 1
        before_seq = seq_id

    if large_a == 0 and before_seq:
        print(f"{before_seq}", file=out_file)
        a += 1

    blast_input.close()
    return a


def analyze_nohits(targets):
    """
    Extract genes with no BLASTP hits for each reference (target) species.

    Args:
        targets (list): Reference species prefixes
    """
    # Set up BLAST result file open blastp.out
    if not os.path.exists("blastp.out"):
        print("Error: blastp.out file does not exist.")
        return

    total = 0
    # Open output file for writing in text mode (combined across targets)
    with open("blastp_nohits.tab", "w+", encoding='utf-8') as out_file:
        for target in targets:
            print(f"Target species: {target}")
            print("Analyzing BLASTP results...")
            total += _analyze_one(target, out_file)

    print(f"Number of genes with no hits: {total}")
    print("Created result file 'blastp_nohits.tab'.")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Analyze BLASTP results and extract genes with no hits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 pick_nohit_genes.py config.yaml
    python3 pick_nohit_genes.py ../config.yaml

The target species are the reference species, derived from the top-level
'species' list and 'reference_count' (no per-step config is needed).
        """
    )

    parser.add_argument(
        'config_file',
        help='YAML config file path'
    )

    args = parser.parse_args()

    # Load config file
    config = load_config(args.config_file)

    # Validate configuration (reference species prefixes)
    targets = validate_config(config)

    # Analyze genes with no hits
    analyze_nohits(targets)


if __name__ == "__main__":
    main()
