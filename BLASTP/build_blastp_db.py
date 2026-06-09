#!/usr/bin/env python3
"""
BLASTP database build script

Usage:
    python3 build_blastp_db.py config.yaml

Reads parameters from the config file (YAML format)
and performs FASTA file concatenation and BLASTP database construction.

This step has no configurable settings:
    # The concatenated FASTA file name is fixed (defaults.BLASTP_ALL_AA_FASTA)
    # and the database type is fixed (defaults.BLASTP_DBTYPE); neither is
    # configurable.
    # input_files are derived from the top-level 'species' list.
"""

import sys
import os
import subprocess
import shutil
import yaml
import argparse

# Make the repository-root shared modules importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import species_config
import defaults


def get_executable(config, name, fallback=None):
    """
    Get executable path

    Priority:
    1. config['executables'][name]
    2. fallback (if specified)
    3. name itself (searched from PATH)

    Args:
        config (dict): Full configuration
        name (str): Executable name
        fallback (str): Fallback value

    Returns:
        str: Executable path
    """
    # Get from executables section
    executables = config.get('executables') or {}
    if name in executables and executables[name]:
        return executables[name]

    # Use fallback value if available
    if fallback:
        return fallback

    # Default is name itself (searched from PATH)
    return name


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
        dict: Database build settings
    """
    # The 'build_blastp_db' section has no configurable settings anymore;
    # it may be absent or empty.
    db_config = config.get('build_blastp_db') or {}

    # Concatenated FASTA path and database type are fixed defaults
    # (see defaults.py), not configurable.
    db_config['output_fasta'] = defaults.BLASTP_ALL_AA_FASTA
    db_config['dbtype'] = defaults.BLASTP_DBTYPE

    # Input FASTA files are derived from the species list (all species).
    try:
        db_config['input_files'] = species_config.blastp_input_files(config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    input_files = db_config['input_files']

    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
            sys.exit(1)

    # Create output directory
    output_dir = os.path.dirname(db_config['output_fasta'])
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")

    return db_config


def concatenate_fasta_files(input_files, output_fasta):
    """
    Concatenate multiple FASTA files

    Args:
        input_files (list): List of input FASTA files
        output_fasta (str): Output FASTA file path
    """
    print("Concatenating FASTA files...")
    print(f"Input files: {', '.join(input_files)}")
    print(f"Output file: {output_fasta}")
    print("-" * 50)

    try:
        with open(output_fasta, 'w', encoding='utf-8') as outfile:
            for i, input_file in enumerate(input_files):
                print(f"Processing: {input_file} ({i+1}/{len(input_files)})")

                with open(input_file, 'r', encoding='utf-8') as infile:
                    # Read file contents and write to output file
                    content = infile.read()
                    outfile.write(content)

                    # Add newline if not the last file
                    if not content.endswith('\n'):
                        outfile.write('\n')

        # Verify concatenation result
        if os.path.exists(output_fasta):
            file_size = os.path.getsize(output_fasta)
            print("Concatenation completed.")
            print(f"Output file: {output_fasta}")
            print(f"File size: {file_size:,} bytes")

            # Count sequences
            try:
                with open(output_fasta, 'r', encoding='utf-8') as f:
                    sequence_count = sum(
                        1 for line in f if line.startswith('>')
                    )
                print(f"Number of sequences: {sequence_count:,}")
            except Exception as e:
                print(f"Error counting sequences: {e}")
        else:
            print("Error: Concatenated file was not created.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: File concatenation failed: {e}", file=sys.stderr)
        sys.exit(1)


def build_makeblastdb_command(config, db_config):
    """
    Build makeblastdb command

    Args:
        config (dict): Full configuration
        db_config (dict): Database build settings

    Returns:
        list: makeblastdb command list
    """
    # makeblastdb executable path (executables section takes priority)
    executable = get_executable(config, 'makeblastdb')

    # Database type (fixed: prot)
    dbtype = db_config['dbtype']

    # Build basic command
    cmd = [
        executable,
        '-in', db_config['output_fasta'],
        '-dbtype', dbtype
    ]

    return cmd


def run_makeblastdb(cmd, db_config):
    """
    Run makeblastdb

    Args:
        cmd (list): makeblastdb command list
        db_config (dict): Database build settings
    """
    print("Building BLASTP database...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Input file: {db_config['output_fasta']}")
    print(f"Database type: {db_config['dbtype']}")
    print("-" * 50)

    try:
        # Run makeblastdb
        cwd_path = os.path.dirname(os.path.abspath(db_config['output_fasta']))
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd_path or '.'
        )

        print("BLASTP database build completed successfully.")

        # Display stdout if available
        if result.stdout:
            print("Standard output:")
            print(result.stdout)

        # Check generated database files
        base_path = db_config['output_fasta']
        db_extensions = [
            '.phr', '.pin', '.pjs', '.pot', '.psq', '.ptf', '.pto'
        ]

        print("Generated database files:")
        total_size = 0
        for ext in db_extensions:
            db_file = base_path + ext
            if os.path.exists(db_file):
                file_size = os.path.getsize(db_file)
                total_size += file_size
                print(f"  {db_file}: {file_size:,} bytes")
            else:
                print(f"  {db_file}: not created")

        print(f"Total database file size: {total_size:,} bytes")

    except subprocess.CalledProcessError as e:
        print(
            f"Error: makeblastdb execution failed (exit code: {e.returncode})",
            file=sys.stderr
        )
        if e.stdout:
            print("Standard output:", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print("Standard error:", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"Error: makeblastdb executable not found: {cmd[0]}",
            file=sys.stderr
        )
        print(
            "Please verify that BLAST+ is installed and the path is correct.",
            file=sys.stderr
        )
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Build BLASTP database from config file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 build_blastp_db.py config.yaml
    python3 build_blastp_db.py ../config.yaml

This step has no configurable settings.
    # The concatenated FASTA file name (all_aa.fasta) and the database type
    # (prot) are fixed.
    # input_files are derived from the top-level 'species' list
    # (one ../Materials/{prefix}/{prefix}.aa.fasta per species).
        """
    )

    parser.add_argument(
        'config_file',
        help='YAML config file path'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Display commands without executing them'
    )

    parser.add_argument(
        '--concat-only',
        action='store_true',
        help='Only concatenate files without building the database'
    )

    args = parser.parse_args()

    # Load config file
    config = load_config(args.config_file)

    # Validate configuration
    db_config = validate_config(config)

    if args.dry_run:
        print("Dry run mode:")
        print("1. File concatenation:")
        input_files_str = ' '.join(db_config['input_files'])
        print(f"   cat {input_files_str} > {db_config['output_fasta']}")

        if not args.concat_only:
            cmd = build_makeblastdb_command(config, db_config)
            print("2. Database build:")
            print(f"   {' '.join(cmd)}")
        return

    # Concatenate FASTA files
    concatenate_fasta_files(
        db_config['input_files'], db_config['output_fasta']
    )

    # Build database (unless --concat-only is specified)
    if not args.concat_only:
        cmd = build_makeblastdb_command(config, db_config)
        run_makeblastdb(cmd, db_config)
    else:
        print("File concatenation only completed. Database build was skipped.")


if __name__ == '__main__':
    main()
