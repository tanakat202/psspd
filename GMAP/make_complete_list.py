#!/usr/bin/env python3
"""
Script to create final target list from GMAP hit lists

Usage:
    python3 make_complete_list.py config.yaml

Reads parameters from the config file (YAML format),
integrates multiple hit list files, and extracts CDS sequences that had no hits.

Required settings:
    make_complete_list:
        hit_files: List of hit list files
        input_cds: Input CDS file (Nohit_cds.fa)
        output_list: Output list file
        output_cds: Output CDS file
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
        dict: make_complete_list settings
    """
    if 'make_complete_list' not in config:
        print("Error: 'make_complete_list' section not found in config file.", file=sys.stderr)
        sys.exit(1)

    complete_config = config['make_complete_list']

    # Check required parameters
    required_params = ['hit_files', 'input_cds', 'output_list', 'output_cds']
    for param in required_params:
        if param not in complete_config:
            print(f"Error: Required parameter '{param}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    # Check that hit_files is a list
    if not isinstance(complete_config['hit_files'], list):
        print("Error: 'hit_files' must be specified as a list.", file=sys.stderr)
        sys.exit(1)

    # Check input CDS file existence
    if not os.path.exists(complete_config['input_cds']):
        print(f"Error: Input CDS file '{complete_config['input_cds']}' not found.", file=sys.stderr)
        sys.exit(1)

    return complete_config


def collect_hit_ids(hit_files):
    """
    Collect hit IDs from multiple hit list files

    Args:
        hit_files (list): List of hit list files

    Returns:
        set: Set of hit IDs
    """
    hit_ids = set()

    for hit_file in hit_files:
        if not os.path.exists(hit_file):
            print(f"Warning: Hit file '{hit_file}' not found. Skipping.")
            continue

        try:
            with open(hit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        dat = line.split("\t")
                        if dat:
                            hit_ids.add(dat[0])
            print(f"Loaded: {hit_file} ({len(hit_ids)} IDs cumulative)")
        except Exception as e:
            print(f"Warning: Error reading file '{hit_file}': {e}")

    return hit_ids


def extract_non_hit_sequences(input_cds, hit_ids, output_list, output_cds):
    """
    Extract sequences that had no hits

    Args:
        input_cds (str): Input CDS file path
        hit_ids (set): Set of hit IDs
        output_list (str): Output list file path
        output_cds (str): Output CDS file path

    Returns:
        int: Number of extracted sequences
    """
    extracted_count = 0
    current_id = None
    output_flag = False

    try:
        with open(input_cds, 'r', encoding='utf-8') as infile:
            with open(output_list, 'w', encoding='utf-8') as out_list:
                with open(output_cds, 'w', encoding='utf-8') as out_cds:
                    for line in infile:
                        line = line.rstrip('\n')

                        # Process header line
                        match = re.match(r'>(\S+)', line)
                        if match:
                            current_id = match.group(1)
                            if current_id not in hit_ids:
                                output_flag = True
                                out_cds.write(line + '\n')
                                out_list.write(current_id + '\n')
                                extracted_count += 1
                            else:
                                output_flag = False
                        elif output_flag:
                            # Process sequence line
                            out_cds.write(line + '\n')

        return extracted_count

    except Exception as e:
        print(f"Error: An error occurred during file processing: {e}", file=sys.stderr)
        return -1


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Create final target list from GMAP hit lists',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 make_complete_list.py config.yaml
    python3 make_complete_list.py ../config.yaml

Config file example:
    make_complete_list:
        hit_files:
            - "SpeciesB_hit.tab"
            - "SpeciesC_hit.tab"
        input_cds: "../BLASTP/Nohit_cds.fa"
        output_list: "Target.list"
        output_cds: "Target_cds.fa"
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
    complete_config = validate_config(config)

    print("=" * 60)
    print("Creating Final Target List from GMAP Hit Lists")
    print("=" * 60)

    # Collect hit IDs
    print("\n[1] Loading hit list files")
    print("-" * 40)
    hit_ids = collect_hit_ids(complete_config['hit_files'])
    print(f"Total hit IDs: {len(hit_ids)}")

    # Extract sequences with no hits
    print("\n[2] Extracting sequences with no hits")
    print("-" * 40)
    print(f"Input file: {complete_config['input_cds']}")
    print(f"Output list: {complete_config['output_list']}")
    print(f"Output CDS: {complete_config['output_cds']}")

    extracted_count = extract_non_hit_sequences(
        complete_config['input_cds'],
        hit_ids,
        complete_config['output_list'],
        complete_config['output_cds']
    )

    if extracted_count >= 0:
        print(f"\nExtracted sequences: {extracted_count}")
        print("=" * 60)
        print("Processing completed.")
    else:
        print("Processing failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
