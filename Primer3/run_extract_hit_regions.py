#!/usr/bin/env python3
"""
Script to run extract_hit_regions.py and make_possiblePair5000.py

Usage:
    python3 run_extract_hit_regions.py config.yaml

Reads settings from the extract_hit_regions section of the config file
and runs Python scripts for each species.

Processing:
1. extract_hit_regions.py: Extract hit regions from BLASTN output
2. make_possiblePair5000.py: Extract primer pair candidates
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


def run_python_script(python_exec: str, script: str, prefix: str) -> None:
    """Run a Python script"""
    cmd = [python_exec, script, prefix]
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
        print(f"Error: {script} execution failed", file=sys.stderr)
        if result.stderr:
            print(f"stderr: {result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)


def run_extract_hit_regions(config: dict) -> None:
    """Run extract_hit_regions.py and make_possiblePair5000.py"""
    hit_config = config.get('extract_hit_regions', {})

    # Python executable path (executables section takes priority)
    python_exec = get_executable(config, 'python3')

    # Script paths
    extract_script = hit_config.get('extract_script', 'extract_hit_regions.py')
    pair_script = hit_config.get('pair_script', 'make_possiblePair5000.py')

    # List of species to process
    targets = hit_config.get('targets', [])

    if not targets:
        print("Error: No targets specified", file=sys.stderr)
        sys.exit(1)

    # Check script existence
    if not os.path.exists(extract_script):
        print(f"Error: Script not found: {extract_script}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(pair_script):
        print(f"Error: Script not found: {pair_script}", file=sys.stderr)
        sys.exit(1)

    print(f"Python: {python_exec}")
    print(f"extract_hit_regions script: {extract_script}")
    print(f"make_possiblePair script: {pair_script}")
    print(f"Targets: {len(targets)} species")
    print()

    for target in targets:
        prefix = target.get('prefix')

        if not prefix:
            print(f"Warning: Skipping entry with missing prefix", file=sys.stderr)
            continue

        # Check input file existence
        input_file = f"{prefix}.out"
        if not os.path.exists(input_file):
            print(f"Error: Input file not found: {input_file}", file=sys.stderr)
            sys.exit(1)

        print(f"Processing: {prefix}")

        # Run extract_hit_regions.py
        print(f"  1. Running extract_hit_regions.py")
        run_python_script(python_exec, extract_script, prefix)
        print(f"     Output: {prefix}.out.tab")

        # Run make_possiblePair5000.py
        print(f"  2. Running make_possiblePair5000.py")
        run_python_script(python_exec, pair_script, prefix)
        print(f"     Output: {prefix}_possiblePair2000.tab")

        print()

    print("All processing completed")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 run_extract_hit_regions.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    run_extract_hit_regions(config)


if __name__ == '__main__':
    main()
