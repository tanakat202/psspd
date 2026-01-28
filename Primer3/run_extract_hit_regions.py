#!/usr/bin/env python3
"""
extract_hit_regions.pyとmake_possiblePair5000.pyを実行するスクリプト

使用方法:
    python3 run_extract_hit_regions.py config.yaml

設定ファイルのextract_hit_regionsセクションから設定を読み込み、
各種に対してPythonスクリプトを実行します。

処理内容:
1. extract_hit_regions.py: BLASTN出力からヒット領域を抽出
2. make_possiblePair5000.py: プライマーペアの候補を抽出
"""

import subprocess
import sys
import os
import shutil
import yaml


def load_config(config_path: str) -> dict:
    """設定ファイルを読み込む"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_executable(config, name, fallback=None):
    """
    実行ファイルパスを取得する

    優先順位:
    1. config['executables'][name]
    2. fallback（指定された場合）
    3. PATHから検索
    4. name自体
    """
    executables = config.get('executables') or {}
    if name in executables and executables[name]:
        return executables[name]
    if fallback:
        return fallback
    # PATHから検索
    path = shutil.which(name)
    if path:
        return path
    return name


def run_python_script(python_exec: str, script: str, prefix: str) -> None:
    """Pythonスクリプトを実行する"""
    cmd = [python_exec, script, prefix]
    print(f"  コマンド: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        print(f"エラー: {script}の実行に失敗しました", file=sys.stderr)
        if result.stderr:
            print(f"stderr: {result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)


def run_extract_hit_regions(config: dict) -> None:
    """extract_hit_regions.pyとmake_possiblePair5000.pyを実行する"""
    hit_config = config.get('extract_hit_regions', {})

    # Pythonの実行ファイルパス（executables セクション優先）
    python_exec = get_executable(config, 'python3')

    # スクリプトのパス
    extract_script = hit_config.get('extract_script', 'extract_hit_regions.py')
    pair_script = hit_config.get('pair_script', 'make_possiblePair5000.py')

    # 処理対象の種リスト
    targets = hit_config.get('targets', [])

    if not targets:
        print("エラー: 処理対象（targets）が指定されていません", file=sys.stderr)
        sys.exit(1)

    # スクリプトの存在確認
    if not os.path.exists(extract_script):
        print(f"エラー: スクリプトが見つかりません: {extract_script}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(pair_script):
        print(f"エラー: スクリプトが見つかりません: {pair_script}", file=sys.stderr)
        sys.exit(1)

    print(f"Python: {python_exec}")
    print(f"extract_hit_regions スクリプト: {extract_script}")
    print(f"make_possiblePair スクリプト: {pair_script}")
    print(f"処理対象: {len(targets)}種")
    print()

    for target in targets:
        prefix = target.get('prefix')

        if not prefix:
            print(f"警告: prefixが指定されていないエントリをスキップします", file=sys.stderr)
            continue

        # 入力ファイルの存在確認
        input_file = f"{prefix}.out"
        if not os.path.exists(input_file):
            print(f"エラー: 入力ファイルが見つかりません: {input_file}", file=sys.stderr)
            sys.exit(1)

        print(f"処理対象: {prefix}")

        # extract_hit_regions.pyを実行
        print(f"  1. extract_hit_regions.py を実行")
        run_python_script(python_exec, extract_script, prefix)
        print(f"     出力: {prefix}.out.tab")

        # make_possiblePair5000.pyを実行
        print(f"  2. make_possiblePair5000.py を実行")
        run_python_script(python_exec, pair_script, prefix)
        print(f"     出力: {prefix}_possiblePair2000.tab")

        print()

    print("全ての処理が完了しました")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 run_extract_hit_regions.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"エラー: 設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    run_extract_hit_regions(config)


if __name__ == '__main__':
    main()
