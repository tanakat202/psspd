#!/usr/bin/env python3
"""
Primer3 input file generation script

Usage:
    python3 make_primer3_input.py config.yaml

Reads parameters from the config file (YAML format)
and generates primer3_input.list from Target_cds.fa.

Required settings:
    make_primer3_input:
        input_cds: Input CDS file (Target_cds.fa)
        output_file: Output file (primer3_input.list)
        primer_opt_size: Optimal primer length (default: 20)
        primer_min_size: Minimum primer length (default: 18)
        primer_max_size: Maximum primer length (default: 27)
        product_size_range: Amplicon size range (default: 300-500)
"""

import sys
import os
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
        dict: make_primer3_input settings
    """
    if 'make_primer3_input' not in config:
        print("Error: 'make_primer3_input' section not found in config file.", file=sys.stderr)
        sys.exit(1)

    primer3_input_config = config['make_primer3_input']

    # Check required parameters
    required_params = ['input_cds', 'output_file']
    for param in required_params:
        if param not in primer3_input_config:
            print(f"Error: Required parameter '{param}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    # Check input file existence
    if not os.path.exists(primer3_input_config['input_cds']):
        print(f"Error: Input file '{primer3_input_config['input_cds']}' not found.", file=sys.stderr)
        sys.exit(1)

    return primer3_input_config


def make_primer3_input(config):
    """
    Generate Primer3 input file

    Args:
        config (dict): make_primer3_input settings

    Returns:
        int: Number of sequences processed
    """
    input_cds = config['input_cds']
    output_file = config['output_file']

    # Primer3 parameters (with default values)
    primer_opt_size = config.get('primer_opt_size', 20)
    primer_min_size = config.get('primer_min_size', 18)
    primer_max_size = config.get('primer_max_size', 27)
    product_size_range = config.get('product_size_range', '300-500')

    seq_count = 0

    with open(input_cds, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('>'):
                    # Header line: extract ID
                    seq_id = line[1:].split()[0]
                    outfile.write(f"SEQUENCE_ID={seq_id}\n")
                else:
                    # Sequence line: output template and parameters
                    outfile.write(f"SEQUENCE_TEMPLATE={line}\n")
                    outfile.write(f"PRIMER_OPT_SIZE={primer_opt_size}\n")
                    outfile.write(f"PRIMER_MIN_SIZE={primer_min_size}\n")
                    outfile.write(f"PRIMER_MAX_SIZE={primer_max_size}\n")
                    outfile.write(f"PRIMER_PRODUCT_SIZE_RANGE={product_size_range}\n")
                    outfile.write("=\n")
                    seq_count += 1

    return seq_count


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Generate Primer3 input file from Target_cds.fa',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 make_primer3_input.py config.yaml
    python3 make_primer3_input.py ../config.yaml

Config file example:
    make_primer3_input:
        input_cds: "../GMAP/Target_cds.fa"
        output_file: "primer3_input.list"
        primer_opt_size: 20
        primer_min_size: 18
        primer_max_size: 27
        product_size_range: "300-500"
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
    primer3_input_config = validate_config(config)

    print("=" * 60)
    print("Primer3 Input File Generation")
    print("=" * 60)
    print(f"Input file: {primer3_input_config['input_cds']}")
    print(f"Output file: {primer3_input_config['output_file']}")
    print(f"PRIMER_OPT_SIZE: {primer3_input_config.get('primer_opt_size', 20)}")
    print(f"PRIMER_MIN_SIZE: {primer3_input_config.get('primer_min_size', 18)}")
    print(f"PRIMER_MAX_SIZE: {primer3_input_config.get('primer_max_size', 27)}")
    print(f"PRIMER_PRODUCT_SIZE_RANGE: {primer3_input_config.get('product_size_range', '300-500')}")
    print("-" * 60)

    seq_count = make_primer3_input(primer3_input_config)

    print(f"Sequences processed: {seq_count}")
    print("=" * 60)
    print("Processing completed.")


if __name__ == '__main__':
    main()
