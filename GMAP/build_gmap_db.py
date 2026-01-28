#!/usr/bin/env python3
"""
GMAP database build script

Usage:
    python3 build_gmap_db.py config.yaml

Reads parameters from the config file (YAML format)
and builds GMAP databases.

Required settings:
    gmap_build:
        executable: gmap_build executable path (optional)
        perl_interpreter: Perl interpreter path (optional)
        db_dir: Directory to create the database
        databases:
            - name: Database name (prefix)
              genome: Genome FASTA file path
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
        dict: GMAP build settings
    """
    if 'gmap_build' not in config:
        print("Error: 'gmap_build' section not found in config file.", file=sys.stderr)
        sys.exit(1)

    gmap_config = config['gmap_build']

    # Check required parameters
    required_params = ['db_dir', 'databases']
    for param in required_params:
        if param not in gmap_config:
            print(f"Error: Required parameter '{param}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    # Check that databases is a list
    if not isinstance(gmap_config['databases'], list):
        print("Error: 'databases' must be specified as a list.", file=sys.stderr)
        sys.exit(1)

    if len(gmap_config['databases']) == 0:
        print("Error: 'databases' must contain at least one database entry.", file=sys.stderr)
        sys.exit(1)

    # Validate each database entry
    for i, db in enumerate(gmap_config['databases']):
        if 'name' not in db:
            print(f"Error: databases[{i}] is missing 'name'.", file=sys.stderr)
            sys.exit(1)
        if 'genome' not in db:
            print(f"Error: databases[{i}] is missing 'genome'.", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(db['genome']):
            print(f"Error: Genome file '{db['genome']}' not found.", file=sys.stderr)
            sys.exit(1)

    # Create database directory
    db_dir = gmap_config['db_dir']
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Created database directory: {db_dir}")

    return gmap_config


def build_gmap_build_command(config, gmap_config, db_entry):
    """
    Build gmap_build command

    Args:
        config (dict): Full configuration
        gmap_config (dict): GMAP build settings
        db_entry (dict): Individual database entry

    Returns:
        list: gmap_build command list
    """
    # gmap_build executable path (executables section takes priority)
    executable = get_executable(config, 'gmap_build')

    # Perl interpreter setting (used when shebang is broken)
    # executables section takes priority
    perl_interpreter = get_executable(config, 'perl', None)
    # perl may return None, so check explicitly
    executables = config.get('executables') or {}
    if 'perl' not in executables or not executables.get('perl'):
        perl_interpreter = None

    # Build basic command
    if perl_interpreter:
        # Execute via Perl interpreter
        cmd = [
            perl_interpreter,
            executable,
            '-D', gmap_config['db_dir'],
            '-d', db_entry['name'],
            db_entry['genome']
        ]
    else:
        cmd = [
            executable,
            '-D', gmap_config['db_dir'],
            '-d', db_entry['name'],
            db_entry['genome']
        ]

    return cmd


def run_gmap_build(cmd, db_entry, gmap_config):
    """
    Run gmap_build

    Args:
        cmd (list): gmap_build command list
        db_entry (dict): Individual database entry
        gmap_config (dict): GMAP build settings
    """
    print(f"Building GMAP database '{db_entry['name']}'...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Genome file: {db_entry['genome']}")
    print(f"Output directory: {gmap_config['db_dir']}")
    print("-" * 50)

    try:
        # Run gmap_build
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        print(f"GMAP database '{db_entry['name']}' build completed successfully.")

        # Display stdout if available
        if result.stdout:
            print("Standard output:")
            print(result.stdout)

        # Check generated database
        db_path = os.path.join(gmap_config['db_dir'], db_entry['name'])
        if os.path.exists(db_path):
            print(f"Database directory: {db_path}")
            # List files in directory
            try:
                files = os.listdir(db_path)
                if files:
                    print(f"Number of generated files: {len(files)}")
                else:
                    print("Warning: Database directory is empty.")
            except Exception as e:
                print(f"Error reading directory: {e}")
        else:
            print(f"Warning: Database directory '{db_path}' not found.")

    except subprocess.CalledProcessError as e:
        print(
            f"Error: gmap_build execution failed (exit code: {e.returncode})",
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
            f"Error: gmap_build executable not found: {cmd[0]}",
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
        description='Build GMAP database from config file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 build_gmap_db.py config.yaml
    python3 build_gmap_db.py ../config.yaml

Config file example:
    gmap_build:
        executable: "/path/to/gmap_build"  # Optional
        db_dir: "./"
        databases:
            - name: "SpeciesB"
              genome: "../Materials/DL_data/genome_B.fna"
            - name: "SpeciesC"
              genome: "../Materials/DL_data/genome_C.fna"
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
        help='Build only a specific database (specify by name)'
    )

    args = parser.parse_args()

    # Load config file
    config = load_config(args.config_file)

    # Validate configuration
    gmap_config = validate_config(config)

    # Determine databases to build
    databases = gmap_config['databases']
    if args.database:
        databases = [db for db in databases if db['name'] == args.database]
        if not databases:
            print(f"Error: Database '{args.database}' not found in config file.", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print("Dry run mode: The following commands would be executed:")
        for db_entry in databases:
            cmd = build_gmap_build_command(config, gmap_config, db_entry)
            print(f"  {' '.join(cmd)}")
        return

    # Build databases
    print(f"Number of databases to build: {len(databases)}")
    print("=" * 60)

    for i, db_entry in enumerate(databases):
        print(f"\n[{i+1}/{len(databases)}] Database: {db_entry['name']}")
        print("=" * 60)

        cmd = build_gmap_build_command(config, gmap_config, db_entry)
        run_gmap_build(cmd, db_entry, gmap_config)

        print()

    print("=" * 60)
    print("All GMAP database builds completed.")


if __name__ == '__main__':
    main()
