#!/usr/bin/env python3
"""
Script to run Primer3

Usage:
    python3 run_primer3.py config.yaml

Input/output file paths are fixed (see defaults.py); the executable may be set
under the top-level 'executables' section.
"""

import subprocess
import sys
import os
import yaml

# Make the repository-root shared module importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    3. name itself (searched from PATH)
    """
    executables = config.get('executables') or {}
    if name in executables and executables[name]:
        return executables[name]
    if fallback:
        return fallback
    return name


def run_primer3(config: dict) -> None:
    """Run primer3_core"""
    # Input/output list files are fixed defaults (see defaults.py).
    input_file = defaults.PRIMER3_INPUT_FILE
    output_file = defaults.PRIMER3_OUTPUT_FILE
    executable = get_executable(config, 'primer3_core')
    working_dir = (config.get('primer3') or {}).get('working_dir')

    # Handle working directory
    original_dir = os.getcwd()
    if working_dir:
        os.chdir(working_dir)
        print(f"Working directory: {os.getcwd()}")

    try:
        # Check input file existence
        if not os.path.exists(input_file):
            print(f"Error: Input file not found: {input_file}", file=sys.stderr)
            sys.exit(1)

        print(f"Input file: {input_file}")
        print(f"Output file: {output_file}")
        print(f"Executable: {executable}")

        # Run primer3_core
        # Equivalent to: primer3_core < input > output
        with open(input_file, 'r', encoding='utf-8') as fin:
            with open(output_file, 'w', encoding='utf-8') as fout:
                result = subprocess.run(
                    [executable],
                    stdin=fin,
                    stdout=fout,
                    stderr=subprocess.PIPE,
                    text=True
                )

        if result.returncode != 0:
            print(f"Error: primer3_core execution failed", file=sys.stderr)
            if result.stderr:
                print(f"stderr: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)

        print(f"Done: Created {output_file}")

    finally:
        # Return to original directory
        if working_dir:
            os.chdir(original_dir)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 run_primer3.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    run_primer3(config)


if __name__ == '__main__':
    main()
