#!/usr/bin/env python3
"""
Primer3 input file generation script

Usage:
    python3 make_primer3_input.py config.yaml

Reads parameters from the config file (YAML format)
and generates primer3_input.list from Target_cds.fa.

Settings:
    make_primer3_input:
        # input_cds and output_file are fixed (see defaults.py); the primer-size
        # knobs below stay configurable:
        primer_opt_size: Optimal primer length (default: 20)
        primer_min_size: Minimum primer length (default: 18)
        primer_max_size: Maximum primer length (default: 27)
        product_size_range: Amplicon size range (default: 300-500)
        primer_min_tm: Minimum primer Tm (default: 57.0)
        primer_opt_tm: Optimal primer Tm (default: 60.0)
        primer_max_tm: Maximum primer Tm (default: 63.0)
        primer_min_gc: Minimum primer GC% (default: 20.0)
        primer_opt_gc_percent: Optimal primer GC% (default: 50.0)
        primer_max_gc: Maximum primer GC% (default: 80.0)
"""

import sys
import os
import yaml
import argparse

# Make the repository-root shared module importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import defaults


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
    # The section keeps the optional primer-size knobs (primer_opt_size, etc.);
    # it may be absent or empty.
    primer3_input_config = config.get('make_primer3_input') or {}

    # input_cds and output_file are fixed defaults (see defaults.py),
    # not configurable.
    primer3_input_config['input_cds'] = defaults.MAKE_PRIMER3_INPUT_INPUT_CDS
    primer3_input_config['output_file'] = defaults.MAKE_PRIMER3_INPUT_OUTPUT_FILE

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

    # Tm parameters (with Primer3 default values)
    primer_min_tm = config.get('primer_min_tm', 57.0)
    primer_opt_tm = config.get('primer_opt_tm', 60.0)
    primer_max_tm = config.get('primer_max_tm', 63.0)

    # GC parameters (with Primer3 default values)
    primer_min_gc = config.get('primer_min_gc', 20.0)
    primer_opt_gc_percent = config.get('primer_opt_gc_percent', 50.0)
    primer_max_gc = config.get('primer_max_gc', 80.0)

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
                    outfile.write(f"PRIMER_MIN_TM={primer_min_tm}\n")
                    outfile.write(f"PRIMER_OPT_TM={primer_opt_tm}\n")
                    outfile.write(f"PRIMER_MAX_TM={primer_max_tm}\n")
                    outfile.write(f"PRIMER_MIN_GC={primer_min_gc}\n")
                    outfile.write(f"PRIMER_OPT_GC_PERCENT={primer_opt_gc_percent}\n")
                    outfile.write(f"PRIMER_MAX_GC={primer_max_gc}\n")
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
        # input_cds (../GMAP/Target_cds.fa) and output_file (primer3_input.list)
        # are fixed. Only the primer-size knobs are configurable:
        primer_opt_size: 20
        primer_min_size: 18
        primer_max_size: 27
        product_size_range: "300-500"
        primer_min_tm: 57.0
        primer_opt_tm: 60.0
        primer_max_tm: 63.0
        primer_min_gc: 20.0
        primer_opt_gc_percent: 50.0
        primer_max_gc: 80.0
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
    print(f"PRIMER_MIN_TM: {primer3_input_config.get('primer_min_tm', 57.0)}")
    print(f"PRIMER_OPT_TM: {primer3_input_config.get('primer_opt_tm', 60.0)}")
    print(f"PRIMER_MAX_TM: {primer3_input_config.get('primer_max_tm', 63.0)}")
    print(f"PRIMER_MIN_GC: {primer3_input_config.get('primer_min_gc', 20.0)}")
    print(f"PRIMER_OPT_GC_PERCENT: {primer3_input_config.get('primer_opt_gc_percent', 50.0)}")
    print(f"PRIMER_MAX_GC: {primer3_input_config.get('primer_max_gc', 80.0)}")
    print("-" * 60)

    seq_count = make_primer3_input(primer3_input_config)

    print(f"Sequences processed: {seq_count}")
    print("=" * 60)
    print("Processing completed.")


if __name__ == '__main__':
    main()
