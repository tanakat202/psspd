#!/usr/bin/env python3
"""
Append original sequence IDs to unique_primer3.tab.

For each row in unique_primer3.tab, look up the original FASTA ID
(saved per-species in Materials/{prefix}/{prefix}.list by step0_translation.py)
and append it as a new last column.

Usage:
    python3 add_original_id.py <config.yaml>

Reads settings from the 'add_original_id' section of the config file.
"""

import os
import re
import sys
import yaml

# Make the repository-root shared module importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import species_config


# First column of unique_primer3.tab is '{prefix}_{NNNNNN}_{primer_idx}',
# where {NNNNNN} is the 6-digit gene number. We strip the trailing '_<idx>'
# to recover the gene key '{prefix}_{NNNNNN}'.
GENE_ID_PATTERN = re.compile(r'^(.+_\d{6})_\d+$')


def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_mapping(species_list, materials_dir):
    """Build a {prefix}_{gene_id} -> original_id dict from per-species .list files."""
    mapping = {}
    for species in species_list:
        prefix = species.get('prefix')
        if not prefix:
            print(f"Error: 'prefix' missing in species entry: {species}", file=sys.stderr)
            sys.exit(1)
        list_path = os.path.join(materials_dir, prefix, f"{prefix}.list")
        if not os.path.exists(list_path):
            print(f"Error: Mapping file not found: {list_path}", file=sys.stderr)
            sys.exit(1)
        with open(list_path, 'r', encoding='utf-8') as f:
            for lineno, line in enumerate(f, start=1):
                line = line.rstrip('\n')
                if not line:
                    continue
                parts = line.split('\t', 1)
                if len(parts) != 2:
                    print(
                        f"Error: Malformed line at {list_path}:{lineno}: '{line}'",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                gene_id, original_id = parts
                mapping[f"{prefix}_{gene_id}"] = original_id
    return mapping


def annotate(input_path, output_path, mapping):
    rows = 0
    with open(input_path, 'r', encoding='utf-8') as fin, \
            open(output_path, 'w', encoding='utf-8') as fout:
        for lineno, line in enumerate(fin, start=1):
            line_no_nl = line.rstrip('\n')
            if not line_no_nl:
                fout.write(line)
                continue
            rows += 1
            first_col = line_no_nl.split('\t', 1)[0]
            m = GENE_ID_PATTERN.match(first_col)
            if not m:
                print(
                    f"Error: Unexpected ID format at {input_path}:{lineno}: "
                    f"'{first_col}' (expected '<prefix>_<NNNNNN>_<idx>')",
                    file=sys.stderr,
                )
                sys.exit(1)
            key = m.group(1)
            if key not in mapping:
                print(
                    f"Error: Gene ID '{key}' not found in mapping "
                    f"(at {input_path}:{lineno})",
                    file=sys.stderr,
                )
                sys.exit(1)
            fout.write(f"{line_no_nl}\t{mapping[key]}\n")
    return rows


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 add_original_id.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)

    add_config = config.get('add_original_id') or {}
    input_file = add_config.get('input_file', 'unique_primer3.tab')
    output_file = add_config.get('output_file', 'unique_primer3_with_original_id.tab')
    materials_dir = add_config.get('materials_dir', '../Materials')

    try:
        species_list = species_config.load_species(config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Materials directory: {materials_dir}")
    print(f"Species: {[s.get('prefix') for s in species_list]}")

    mapping = load_mapping(species_list, materials_dir)
    print(f"Loaded {len(mapping)} ID mappings")

    rows = annotate(input_file, output_file, mapping)
    print(f"Wrote {rows} rows to {output_file}")


if __name__ == '__main__':
    main()
