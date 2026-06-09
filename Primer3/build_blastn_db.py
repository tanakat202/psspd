#!/usr/bin/env python3
"""
Script to build BLASTN databases

Usage:
    python3 build_blastn_db.py config.yaml

Runs makeblastdb to build per-species BLASTN databases. This step has no
configurable settings: the database type is fixed (defaults.BLASTN_DB_DBTYPE)
and the databases are derived from the top-level 'species' list. The
makeblastdb executable may be set under the top-level 'executables' section.
"""

import subprocess
import sys
import os
import shutil
import yaml

# Make the repository-root shared modules importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import species_config
import defaults


def load_config(config_path: str) -> dict:
    """Load config file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_executable(config, name, fallback=None):
    """
    Get executable path

    Priority:
    1. config['executables'][name]
    2. fallback (if specified)
    3. Search from PATH
    4. name itself
    """
    executables = config.get('executables') or {}
    if name in executables and executables[name]:
        return executables[name]
    if fallback:
        return fallback
    # Search from PATH
    path = shutil.which(name)
    if path:
        return path
    return name


def build_blastn_db(config: dict) -> None:
    """Build BLASTN databases"""
    # makeblastdb executable path (executables section takes priority)
    executable = get_executable(config, 'makeblastdb')

    # Database type is a fixed default (see defaults.py), not configurable.
    dbtype = defaults.BLASTN_DB_DBTYPE

    # Databases (name + genome input + output) are derived from all species.
    try:
        databases = species_config.blastn_db_databases(config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not databases:
        print("Error: No database configuration found", file=sys.stderr)
        sys.exit(1)

    print(f"makeblastdb: {executable}")
    print(f"Database type: {dbtype}")
    print(f"Number of databases to build: {len(databases)}")
    print()

    for db in databases:
        name = db.get('name')
        input_file = db.get('input')
        output_name = db.get('output')

        if not name or not input_file:
            print(f"Warning: Skipping entry with missing name or input", file=sys.stderr)
            continue

        # Use name.fna if output name is not specified
        if not output_name:
            output_name = f"{name}.fna"

        # Check input file existence
        if not os.path.exists(input_file):
            print(f"Error: Input file not found: {input_file}", file=sys.stderr)
            sys.exit(1)

        print(f"Building database: {name}")
        print(f"  Input: {input_file}")
        print(f"  Output: {output_name}")

        # Run makeblastdb
        cmd = [
            executable,
            '-in', input_file,
            '-out', output_name,
            '-dbtype', dbtype
        ]
        print(f"  Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            print(f"Error: makeblastdb execution failed", file=sys.stderr)
            if result.stderr:
                print(f"stderr: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)

        print(f"  Done: Created {output_name} database")
        print()

    print("All database builds completed")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 build_blastn_db.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    build_blastn_db(config)


if __name__ == '__main__':
    main()
