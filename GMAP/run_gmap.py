#!/usr/bin/env python3
"""
GMAP execution script

Usage:
    python3 run_gmap.py config.yaml

Reads parameters from the config file (YAML format)
and runs GMAP to generate GFF3 files.

Required settings:
    gmap:
        query: Query FASTA file (Nohit_cds.fa etc.)
        output_format: Output format (gff3_gene etc.)
        databases:
            - name: Database name (prefix)
              output: Output GFF3 file name

    gmap_build:
        db_dir: GMAP database directory

    executables:
        gmap: gmap executable path (optional)
"""

import sys
import os
import subprocess
import yaml
import argparse


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
        dict: GMAP execution settings
    """
    if 'gmap' not in config:
        print("Error: 'gmap' section not found in config file.", file=sys.stderr)
        sys.exit(1)

    gmap_config = config['gmap']

    # Check required parameters
    required_params = ['query', 'databases']
    for param in required_params:
        if param not in gmap_config:
            print(f"Error: Required parameter '{param}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    # Check query file existence
    if not os.path.exists(gmap_config['query']):
        print(f"Error: Query file '{gmap_config['query']}' not found.", file=sys.stderr)
        sys.exit(1)

    # Check that databases is a list
    if not isinstance(gmap_config['databases'], list):
        print("Error: 'databases' must be specified as a list.", file=sys.stderr)
        sys.exit(1)

    if len(gmap_config['databases']) == 0:
        print("Error: 'databases' must contain at least one database entry.", file=sys.stderr)
        sys.exit(1)

    # Get db_dir from gmap_build section
    if 'gmap_build' not in config or 'db_dir' not in config['gmap_build']:
        print("Error: 'gmap_build.db_dir' not found in config file.", file=sys.stderr)
        sys.exit(1)

    db_dir = config['gmap_build']['db_dir']

    # Validate each database entry
    for i, db in enumerate(gmap_config['databases']):
        if 'name' not in db:
            print(f"Error: databases[{i}] is missing 'name'.", file=sys.stderr)
            sys.exit(1)
        if 'output' not in db:
            print(f"Error: databases[{i}] is missing 'output'.", file=sys.stderr)
            sys.exit(1)

        # Check database existence
        db_path = os.path.join(db_dir, db['name'])
        if not os.path.exists(db_path):
            print(f"Error: GMAP database '{db_path}' not found.", file=sys.stderr)
            print("Please run build_gmap_db.py first to build the database.", file=sys.stderr)
            sys.exit(1)

    return gmap_config


def build_gmap_command(config, gmap_config, db_entry):
    """
    Build gmap command

    Args:
        config (dict): Full configuration
        gmap_config (dict): GMAP execution settings
        db_entry (dict): Individual database entry

    Returns:
        list: gmap command list
    """
    # gmap executable path
    executable = get_executable(config, 'gmap')

    # Database directory
    db_dir = config['gmap_build']['db_dir']

    # Output format (default: gff3_gene)
    output_format = gmap_config.get('output_format', 'gff3_gene')

    # Build command
    cmd = [
        executable,
        '-D', db_dir,
        '-d', db_entry['name'],
        '-f', output_format,
        gmap_config['query']
    ]

    return cmd


def run_gmap(cmd, db_entry):
    """
    Run gmap

    Args:
        cmd (list): gmap command list
        db_entry (dict): Individual database entry
    """
    output_file = db_entry['output']

    print(f"Running GMAP search '{db_entry['name']}'...")
    print(f"Command: {' '.join(cmd)} > {output_file}")
    print("-" * 50)

    try:
        # Run gmap (redirect output to file)
        with open(output_file, 'w', encoding='utf-8') as out_f:
            result = subprocess.run(
                cmd,
                check=True,
                stdout=out_f,
                stderr=subprocess.PIPE,
                text=True
            )

        print(f"GMAP search '{db_entry['name']}' completed successfully.")
        print(f"Output file: {output_file}")

        # Check output file size
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"File size: {file_size:,} bytes")

            # Count lines
            with open(output_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            print(f"Number of lines: {line_count:,}")
        else:
            print(f"Warning: Output file '{output_file}' was not generated.")

        # Display stderr if available
        if result.stderr:
            print("Standard error:")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(
            f"Error: gmap execution failed (exit code: {e.returncode})",
            file=sys.stderr
        )
        if e.stderr:
            print("Standard error:", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"Error: gmap executable not found: {cmd[0]}",
            file=sys.stderr
        )
        print(
            "Please verify that GMAP is installed and the path is correct.",
            file=sys.stderr
        )
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Run GMAP and generate GFF3 files from config file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 run_gmap.py config.yaml
    python3 run_gmap.py ../config.yaml

Config file example:
    gmap:
        query: "../BLASTP/Nohit_cds.fa"
        output_format: "gff3_gene"
        databases:
            - name: "SpeciesB"
              output: "SpeciesB.gff3"
            - name: "SpeciesC"
              output: "SpeciesC.gff3"

    gmap_build:
        db_dir: "../GMAP"
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
        '--database', '-d',
        help='Search only a specific database (specify by name)'
    )

    args = parser.parse_args()

    # Load config file
    config = load_config(args.config_file)

    # Validate configuration
    gmap_config = validate_config(config)

    # Determine databases to search
    databases = gmap_config['databases']
    if args.database:
        databases = [db for db in databases if db['name'] == args.database]
        if not databases:
            print(f"Error: Database '{args.database}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print("Dry run mode: The following commands would be executed:")
        for db_entry in databases:
            cmd = build_gmap_command(config, gmap_config, db_entry)
            print(f"  {' '.join(cmd)} > {db_entry['output']}")
        return

    # Run GMAP searches
    print(f"Number of databases to search: {len(databases)}")
    print(f"Query file: {gmap_config['query']}")
    print("=" * 60)

    for i, db_entry in enumerate(databases):
        print(f"\n[{i+1}/{len(databases)}] Database: {db_entry['name']}")
        print("=" * 60)

        cmd = build_gmap_command(config, gmap_config, db_entry)
        run_gmap(cmd, db_entry)

        print()

    print("=" * 60)
    print("All GMAP searches completed.")


if __name__ == '__main__':
    main()
