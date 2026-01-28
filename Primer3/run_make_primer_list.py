#!/usr/bin/env python3
"""
Script to create primer list and run counting

Usage:
    python3 run_make_primer_list.py config.yaml

Processing:
1. Create possiblePair.list file (list pair candidate files for target species)
2. Run make_primerList3_Wo5000.py (extract unique primer pairs)
3. Run count.py (count primers and genes)

Reads settings from the make_primer_list section of the config file.
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


def run_python_script(python_exec: str, script: str, capture_output: bool = True) -> str:
    """Run a Python script"""
    cmd = [python_exec, script]
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

    return result.stdout


def run_make_primer_list(config: dict) -> None:
    """Run primer list creation process"""
    primer_config = config.get('make_primer_list', {})

    # Python executable path (executables section takes priority)
    python_exec = get_executable(config, 'python3')

    # List of files to include in possiblePair.list
    pair_files = primer_config.get('pair_files', [])
    if not pair_files:
        print("Error: pair_files not specified", file=sys.stderr)
        sys.exit(1)

    # possiblePair.list path
    pair_list_file = primer_config.get('pair_list_file', 'possiblePair.list')

    # Script paths
    make_primer_script = primer_config.get('make_primer_script', 'make_primerList3_Wo5000.py')
    count_script = primer_config.get('count_script', 'count.py')

    print(f"Python: {python_exec}")
    print(f"make_primerList3 script: {make_primer_script}")
    print(f"count script: {count_script}")
    print()

    # 1. Create possiblePair.list file
    print("1. Creating possiblePair.list")
    missing_files = []
    for pair_file in pair_files:
        if not os.path.exists(pair_file):
            missing_files.append(pair_file)

    if missing_files:
        print(f"Error: The following files were not found:", file=sys.stderr)
        for f in missing_files:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(1)

    with open(pair_list_file, 'w', encoding='utf-8') as f:
        for pair_file in pair_files:
            f.write(f"{pair_file}\n")
    print(f"   Output: {pair_list_file}")
    print(f"   Number of files: {len(pair_files)}")
    for pair_file in pair_files:
        print(f"     - {pair_file}")
    print()

    # Check script existence
    if not os.path.exists(make_primer_script):
        print(f"Error: Script not found: {make_primer_script}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(count_script):
        print(f"Error: Script not found: {count_script}", file=sys.stderr)
        sys.exit(1)

    # 2. Run make_primerList3_Wo5000.py
    print("2. Running make_primerList3_Wo5000.py")
    run_python_script(python_exec, make_primer_script)
    print("   Output: unique_primer3.tab")
    print()

    # 3. Run count.py
    print("3. Running count.py")
    run_python_script(python_exec, count_script)
    print()

    print("All processing completed")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 run_make_primer_list.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    run_make_primer_list(config)


if __name__ == '__main__':
    main()
