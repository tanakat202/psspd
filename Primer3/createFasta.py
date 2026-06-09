#!/usr/bin/env python3
"""
Script to create FASTA file from Primer3 output

Usage:
    python3 createFasta.py config.yaml

Input/output file paths are fixed (see defaults.py); outputs primer sequences
in FASTA format from the Primer3 output file.
"""

import re
import sys
import os
import yaml

# Make the repository-root shared module importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import defaults


def load_config(config_path: str) -> dict:
    """Load config file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_fasta(config: dict) -> None:
    """Create FASTA file from Primer3 output"""
    # Input/output file paths are fixed defaults (see defaults.py).
    input_file = defaults.CREATE_FASTA_INPUT_FILE
    output_file = defaults.CREATE_FASTA_OUTPUT_FILE

    # Check input file existence
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

    # Primer sequence patterns
    left_pattern = re.compile(r'^(PRIMER_LEFT_\d+_SEQUENCE)=(\w+)$')
    right_pattern = re.compile(r'^(PRIMER_RIGHT_\d+_SEQUENCE)=(\w+)$')
    seq_id_pattern = re.compile(r'^SEQUENCE_ID=(.+)$')

    seq_id = None

    with open(input_file, 'r', encoding='utf-8') as fin:
        with open(output_file, 'w', encoding='utf-8') as fout:
            for line in fin:
                line = line.rstrip('\n')

                # Get SEQUENCE_ID
                match = seq_id_pattern.match(line)
                if match:
                    seq_id = match.group(1)
                    continue

                # Match PRIMER_LEFT_*_SEQUENCE
                match = left_pattern.match(line)
                if match:
                    primer_name = match.group(1)
                    sequence = match.group(2)
                    seq_len = len(sequence)
                    fout.write(f">{seq_id}::{primer_name}::{seq_len}\n")
                    fout.write(f"{sequence}\n")
                    continue

                # Match PRIMER_RIGHT_*_SEQUENCE
                match = right_pattern.match(line)
                if match:
                    primer_name = match.group(1)
                    sequence = match.group(2)
                    seq_len = len(sequence)
                    fout.write(f">{seq_id}::{primer_name}::{seq_len}\n")
                    fout.write(f"{sequence}\n")
                    continue

    print(f"Done: Created {output_file}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 createFasta.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    create_fasta(config)


if __name__ == '__main__':
    main()
