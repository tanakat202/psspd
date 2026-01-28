#!/usr/bin/env python3
"""
Script to create hit lists from GFF3 files

Usage:
    python3 make_hit_list.py config.yaml

Reads parameters from the config file (YAML format)
and extracts coverage/identity from GFF3 files to create hit lists.

Required settings:
    make_hit_list:
        targets:
            - prefix: GFF3 file prefix
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
        dict: make_hit_list settings
    """
    if 'make_hit_list' not in config:
        print("Error: 'make_hit_list' section not found in config file.", file=sys.stderr)
        sys.exit(1)

    hit_config = config['make_hit_list']

    if 'targets' not in hit_config:
        print("Error: 'targets' not found in config file.", file=sys.stderr)
        sys.exit(1)

    if not isinstance(hit_config['targets'], list):
        print("Error: 'targets' must be specified as a list.", file=sys.stderr)
        sys.exit(1)

    if len(hit_config['targets']) == 0:
        print("Error: 'targets' must contain at least one entry.", file=sys.stderr)
        sys.exit(1)

    # Validate each target
    for i, target in enumerate(hit_config['targets']):
        if 'prefix' not in target:
            print(f"Error: targets[{i}] is missing 'prefix'.", file=sys.stderr)
            sys.exit(1)

    return hit_config


def process_gff3(prefix):
    """
    Process GFF3 file and create hit list

    Args:
        prefix (str): GFF3 file prefix

    Returns:
        int: Number of extracted hits
    """
    input_file = f"{prefix}.gff3"
    output_file = f"{prefix}_hit.tab"

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        return -1

    hit_count = 0

    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for line in infile:
                    line = line.strip()
                    dat = line.split("\t")

                    if len(dat) < 3:
                        continue

                    if "mRNA" in dat[2]:
                        m = re.search(r"ID=([a-zA-Z_.0-9]+)\.mrna", line)
                        if m:
                            gene_id = m.group(1)
                            m2 = re.search(r"coverage=([0-9.]+);identity=([0-9.]+)", line)
                            if m2:
                                coverage = m2.group(1)
                                identity = m2.group(2)
                                outfile.write(f"{gene_id}\t{coverage}\t{identity}\n")
                                hit_count += 1

        return hit_count

    except Exception as e:
        print(f"Error: An error occurred during file processing: {e}", file=sys.stderr)
        return -1


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Create hit lists from GFF3 files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 make_hit_list.py config.yaml
    python3 make_hit_list.py ../config.yaml

Config file example:
    make_hit_list:
        targets:
            - prefix: "SpeciesB"
            - prefix: "SpeciesC"
        """
    )

    parser.add_argument(
        'config_file',
        help='YAML config file path'
    )

    parser.add_argument(
        '--prefix', '-p',
        help='Process only a specific prefix'
    )

    args = parser.parse_args()

    # Load config file
    config = load_config(args.config_file)

    # Validate configuration
    hit_config = validate_config(config)

    # Determine processing targets
    targets = hit_config['targets']
    if args.prefix:
        targets = [t for t in targets if t['prefix'] == args.prefix]
        if not targets:
            print(f"Error: Prefix '{args.prefix}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    # Execute processing
    print(f"Number of targets: {len(targets)}")
    print("=" * 60)

    total_hits = 0
    for i, target in enumerate(targets):
        prefix = target['prefix']
        print(f"\n[{i+1}/{len(targets)}] Processing: {prefix}")
        print("-" * 40)
        print(f"Input file: {prefix}.gff3")
        print(f"Output file: {prefix}_hit.tab")

        hit_count = process_gff3(prefix)

        if hit_count >= 0:
            print(f"Extracted hits: {hit_count}")
            total_hits += hit_count
        else:
            print("Processing failed.")

    print()
    print("=" * 60)
    print(f"All processing completed. Total hits: {total_hits}")


if __name__ == '__main__':
    main()
