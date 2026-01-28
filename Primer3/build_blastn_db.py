#!/usr/bin/env python3
"""
Script to build BLASTN databases

Usage:
    python3 build_blastn_db.py config.yaml

Reads settings from the build_blastn_db section of the config file
and runs makeblastdb to build BLASTN databases.
"""

import subprocess
import sys
import os
import shutil
import yaml


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
    db_config = config.get('build_blastn_db', {})

    # makeblastdb executable path (executables section takes priority)
    executable = get_executable(config, 'makeblastdb')

    # Database type (default: nucl)
    dbtype = db_config.get('dbtype', 'nucl')

    # List of databases to build
    databases = db_config.get('databases', [])

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
