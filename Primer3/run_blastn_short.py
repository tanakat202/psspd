#!/usr/bin/env python3
"""
Script to run BLASTN (blastn-short)

Usage:
    python3 run_blastn_short.py config.yaml

Reads settings from the blastn_short section of the config file
and runs blastn -task blastn-short to search primer sequences.

The E-value threshold is read from blastn_short.evalue (default: "10") and
kept as a string so values such as "10" or "1E-5" pass through unchanged.
"""

import subprocess
import sys
import os
import shutil
import yaml

# Make the repository-root shared module importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import species_config


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


def run_blastn_short(config: dict) -> None:
    """Run BLASTN (blastn-short)"""
    blastn_config = config.get('blastn_short', {})

    # blastn executable path (executables section takes priority)
    executable = get_executable(config, 'blastn')

    # Query file (primer sequences)
    query = blastn_config.get('query', 'primer3.fa')

    # Output format (default: 6 = tabular)
    outfmt = blastn_config.get('outfmt', 6)

    # Number of threads (default: 4)
    num_threads = blastn_config.get('num_threads', 4)

    # E-value threshold (default: "10"). Kept as a string so values such as
    # "10" or "1E-5" can be passed through to blastn unchanged.
    evalue = str(blastn_config.get('evalue', '10'))

    # Databases (name + db + output) are derived from all species.
    try:
        databases = species_config.blastn_short_databases(config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not databases:
        print("Error: No database configuration found", file=sys.stderr)
        sys.exit(1)

    # Check query file existence
    if not os.path.exists(query):
        print(f"Error: Query file not found: {query}", file=sys.stderr)
        sys.exit(1)

    print(f"blastn: {executable}")
    print(f"Query file: {query}")
    print(f"Output format: {outfmt}")
    print(f"Number of threads: {num_threads}")
    print(f"E-value: {evalue}")
    print(f"Number of databases to search: {len(databases)}")
    print()

    for db in databases:
        name = db.get('name')
        db_path = db.get('db')
        output = db.get('output')

        if not name or not db_path:
            print(f"Warning: Skipping entry with missing name or db", file=sys.stderr)
            continue

        # Use name.out if output file name is not specified
        if not output:
            output = f"{name}.out"

        print(f"Running BLASTN: {name}")
        print(f"  Database: {db_path}")
        print(f"  Output: {output}")

        # Run blastn -task blastn-short
        cmd = [
            executable,
            '-task', 'blastn-short',
            '-db', db_path,
            '-query', query,
            '-out', output,
            '-outfmt', str(outfmt),
            '-num_threads', str(num_threads),
            '-evalue', evalue
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
            print(f"Error: blastn execution failed", file=sys.stderr)
            if result.stderr:
                print(f"stderr: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)

        print(f"  Done: Created {output}")
        print()

    print("All BLASTN searches completed")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 run_blastn_short.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    run_blastn_short(config)


if __name__ == '__main__':
    main()
