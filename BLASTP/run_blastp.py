#!/usr/bin/env python3
"""
BLASTP execution script

Usage:
    python3 run_blastp.py config.yaml

Reads BLASTP parameters from the config file (YAML format)
and runs BLASTP.

Settings:
    blastp:
        output: Output file path
        evalue: E-value threshold (optional, default: 1E-5)
        outfmt: Output format (optional, default: 6)
        num_threads: Number of threads (optional, default: 4)
        executable: BLASTP executable path (optional)
    # database and query are fixed (defaults.BLASTP_ALL_AA_FASTA, the same
    # all-vs-all FASTA); they are no longer configurable.
"""

import sys
import os
import subprocess
import yaml
import argparse
from pathlib import Path

# Make the repository-root shared module importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


def validate_blastp_config(config):
    """
    Validate BLASTP configuration

    Args:
        config (dict): Configuration contents

    Returns:
        dict: BLASTP settings
    """
    if 'blastp' not in config:
        print("Error: 'blastp' section not found in config file.", file=sys.stderr)
        sys.exit(1)

    blastp_config = config['blastp']

    # Database and query are the same fixed all-vs-all FASTA (see defaults.py),
    # not configurable.
    blastp_config['database'] = defaults.BLASTP_ALL_AA_FASTA
    blastp_config['query'] = defaults.BLASTP_ALL_AA_FASTA

    # Check required parameters
    required_params = ['output']
    for param in required_params:
        if param not in blastp_config:
            print(f"Error: Required parameter '{param}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    # Check database file existence
    if not os.path.exists(blastp_config['database']):
        print(f"Error: Database file '{blastp_config['database']}' not found.", file=sys.stderr)
        sys.exit(1)

    # Check query file existence
    if not os.path.exists(blastp_config['query']):
        print(f"Error: Query file '{blastp_config['query']}' not found.", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_dir = os.path.dirname(blastp_config['output'])
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")

    return blastp_config


def build_blastp_command(config, blastp_config):
    """
    Build BLASTP command

    Args:
        config (dict): Full configuration
        blastp_config (dict): BLASTP settings

    Returns:
        list: BLASTP command list
    """
    # BLASTP executable path (executables section takes priority)
    executable = get_executable(config, 'blastp')

    # Build basic command
    cmd = [
        executable,
        '-db', blastp_config['database'],
        '-query', blastp_config['query'],
        '-out', blastp_config['output']
    ]

    # Add optional parameters
    if 'evalue' in blastp_config:
        cmd.extend(['-evalue', str(blastp_config['evalue'])])

    if 'outfmt' in blastp_config:
        cmd.extend(['-outfmt', str(blastp_config['outfmt'])])

    if 'num_threads' in blastp_config:
        cmd.extend(['-num_threads', str(blastp_config['num_threads'])])

    return cmd


def run_blastp(cmd, blastp_config):
    """
    Run BLASTP

    Args:
        cmd (list): BLASTP command list
        blastp_config (dict): BLASTP settings
    """
    print("Running BLASTP...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Database: {blastp_config['database']}")
    print(f"Query: {blastp_config['query']}")
    print(f"Output file: {blastp_config['output']}")
    print("-" * 50)

    try:
        # Run BLASTP
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        print("BLASTP completed successfully.")

        # Display stdout if available
        if result.stdout:
            print("Standard output:")
            print(result.stdout)

        # Check output file
        if os.path.exists(blastp_config['output']):
            file_size = os.path.getsize(blastp_config['output'])
            print(f"Output file '{blastp_config['output']}' created.")
            print(f"File size: {file_size:,} bytes")

            # Brief statistics
            try:
                with open(blastp_config['output'], 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"Number of result lines: {len(lines):,}")
                        print("First few lines:")
                        for i, line in enumerate(lines[:3]):
                            print(f"  {i+1}: {line.strip()}")
                        if len(lines) > 3:
                            print("  ...")
                    else:
                        print("Output file is empty.")
            except Exception as e:
                print(f"Error reading output file: {e}")
        else:
            print(f"Warning: Output file '{blastp_config['output']}' not found.")

    except subprocess.CalledProcessError as e:
        print(f"Error: BLASTP execution failed (exit code: {e.returncode})", file=sys.stderr)
        if e.stdout:
            print("Standard output:", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print("Standard error:", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: BLASTP executable not found: {cmd[0]}", file=sys.stderr)
        print("Please verify that BLASTP is installed and the path is correct.", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Run BLASTP from config file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 run_blastp.py config.yaml
    python3 run_blastp.py ../config.yaml

Config file example:
    blastp:
        output: "BLASTP/blastp.out"
        evalue: "1E-5"
        outfmt: 6
        num_threads: 4
        executable: "/path/to/blastp"  # Optional
    # database and query are fixed (all_aa.fasta); not configurable.
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

    args = parser.parse_args()

    # Load config file
    config = load_config(args.config_file)

    # Validate BLASTP configuration
    blastp_config = validate_blastp_config(config)

    # Build BLASTP command
    cmd = build_blastp_command(config, blastp_config)

    if args.dry_run:
        print("Dry run mode: The following command would be executed:")
        print(' '.join(cmd))
        return

    # Run BLASTP
    run_blastp(cmd, blastp_config)


if __name__ == '__main__':
    main()
