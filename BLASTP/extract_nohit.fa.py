#!/usr/bin/env python3
"""
Script to extract CDS sequences of genes with no BLASTP hits

Usage:
    python3 extract_nohit.fa.py config.yaml

Reads parameters from the config file (YAML format)
and extracts CDS sequences from the no-hit gene list.

Required settings:
    extract_nohit:
        nohits_file: No-hit gene list file
        input_cds_file: Input CDS file template ({target} per reference species)
        output_file: Output file
    # The reference species are derived from the top-level 'species' list.
"""

import os
import sys
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
        dict: extract_nohit settings
    """
    if 'extract_nohit' not in config:
        print("Error: 'extract_nohit' section not found in config file.", file=sys.stderr)
        sys.exit(1)

    extract_config = config['extract_nohit']

    # Check required parameters
    required_params = ['nohits_file', 'input_cds_file', 'output_file']
    for param in required_params:
        if param not in extract_config:
            print(f"Error: Required parameter '{param}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    # Reference species are derived from the species list. The
    # 'input_cds_file' value is kept as a template and expanded per species
    # (its '{target}' placeholder is substituted with each prefix).
    try:
        extract_config['targets'] = species_config.reference_prefixes(config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    return extract_config


def load_nohits_list(nohits_file):
    """
    Load list of genes with no hits

    Args:
        nohits_file (str): No-hit gene list file

    Returns:
        dict: Dictionary of gene IDs
    """
    if not os.path.exists(nohits_file):
        print(f"Error: No-hit gene list file"
              f" '{nohits_file}' not found.", file=sys.stderr)
        sys.exit(1)

    nohits_dict = {}
    try:
        with open(nohits_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    nohits_dict[line] = 1

        print(f"Number of no-hit genes: {len(nohits_dict)}")
        return nohits_dict

    except (IOError, OSError) as e:
        print(f"Error: Failed to load no-hit gene list file: {e}", file=sys.stderr)
        sys.exit(1)


def extract_sequences(extract_config, nohits_dict):
    """
    Extract CDS sequences of genes with no hits

    Args:
        extract_config (dict): extract_nohit settings
        nohits_dict (dict): Dictionary of no-hit gene IDs
    """
    template = extract_config['input_cds_file']
    output_file = extract_config['output_file']
    targets = extract_config['targets']

    print(f"Output file: {output_file}")
    print("Extracting CDS sequences...")

    extracted_count = 0

    try:
        with open(output_file, "w", encoding='utf-8') as out_file:
            for target in targets:
                # Expand the {target} placeholder for this reference species.
                input_file = template.format(target=target)
                if not os.path.exists(input_file):
                    print(f"Error: Input CDS file '{input_file}' not found.", file=sys.stderr)
                    sys.exit(1)

                print(f"Target species: {target}")
                print(f"Input file: {input_file}")

                found_sequences = False
                with open(input_file, "r", encoding='utf-8') as in_file:
                    for line in in_file:
                        line = line.strip()

                        if line.startswith(">"):  # Sequence header line
                            seq_id = line.split(' ', 1)[0][1:]  # Remove '>' and take up to first space

                            if seq_id in nohits_dict:
                                out_file.write(f"{line}\n")
                                found_sequences = True
                                extracted_count += 1
                            else:
                                found_sequences = False

                        elif found_sequences:
                            # Output sequence line if current sequence is a target
                            out_file.write(f"{line}\n")

        print(f"Number of extracted sequences: {extracted_count}")

        # Check output file
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"Created output file '{output_file}'.")
            print(f"File size: {file_size:,} bytes")

            # Brief statistics
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                sequence_count = sum(1 for line in lines
                                     if line.startswith('>'))
                print(f"Number of sequences: {sequence_count}")

        if extracted_count == 0:
            print("Warning: No sequences were extracted. Please check file paths and gene IDs.")

    except (IOError, OSError) as e:
        print(f"Error: An error occurred during CDS sequence extraction: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Extract CDS sequences of genes with no hits from config file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 extract_nohit.fa.py config.yaml
    python3 extract_nohit.fa.py ../config.yaml

Config file example:
    extract_nohit:
        nohits_file: "blastp_nohits.tab"
        input_cds_file: "../Materials/{target}/{target}.cds.fasta"
        output_file: "Nohit_cds.fa"
    # The reference species ({target}) come from the top-level 'species' list.
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
    extract_config = validate_config(config)

    # Load no-hit gene list
    nohits_dict = load_nohits_list(extract_config['nohits_file'])

    # Extract CDS sequences
    extract_sequences(extract_config, nohits_dict)


if __name__ == '__main__':
    main()
