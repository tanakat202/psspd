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
        str: Target species name
    """
    if 'no_hit_analysis' not in config:
        print("Error: 'no_hit_analysis' section not found in config file.", file=sys.stderr)
        sys.exit(1)

    analysis_config = config['no_hit_analysis']

    if 'target' not in analysis_config:
        print("Error: Required parameter 'target' not found in config file.", file=sys.stderr)
        sys.exit(1)

    target = analysis_config['target']

    # Validate target species name
    valid_targets = ['SpeciesA', 'SpeciesB', 'SpeciesC']
    if target not in valid_targets:
        print(f"Error: Invalid target species name '{target}'. "
              f"Valid values: {', '.join(valid_targets)}", file=sys.stderr)
        sys.exit(1)

    return target


def analyze_nohits(target):
    """
    Extract genes with no BLASTP hits

    Args:
        target (str): Target species name
    """
    # Set up BLAST result file open blastp.out
    if not os.path.exists("blastp.out"):
        print("Error: blastp.out file does not exist.")
        return

    print(f"Target species: {target}")
    print("Analyzing BLASTP results...")

    # Open output file for writing in text mode
    with open("blastp_nohits.tab", "w+", encoding='utf-8') as out_file:
        # Read from blastp.out file
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

    print(f"Number of genes with no hits: {a}")
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

Config file example:
    no_hit_analysis:
        target: "SpeciesB"
        """
    )

    parser.add_argument(
        'config_file',
        help='YAML config file path'
    )

    args = parser.parse_args()

    # Load config file
    config = load_config(args.config_file)

    # Validate configuration
    target = validate_config(config)

    # Analyze genes with no hits
    analyze_nohits(target)


if __name__ == "__main__":
    main()
