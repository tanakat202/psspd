#!/usr/bin/env python3
"""
プライマーリスト作成とカウントを実行するスクリプト

使用方法:
    python3 run_make_primer_list.py config.yaml

処理内容:
1. possiblePair.listファイルを作成（対象種のペア候補ファイルをリスト化）
2. make_primerList3_Wo5000.pyを実行（ユニークなプライマーペアを抽出）
3. count.pyを実行（プライマー数と遺伝子数をカウント）

設定ファイルのmake_primer_listセクションから設定を読み込みます。
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


def run_python_script(python_exec: str, script: str, capture_output: bool = True) -> str:
    """Pythonスクリプトを実行する"""
    cmd = [python_exec, script]
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

    return result.stdout


def run_make_primer_list(config: dict) -> None:
    """プライマーリスト作成処理を実行する"""
    primer_config = config.get('make_primer_list', {})

    # Pythonの実行ファイルパス（executables セクション優先）
    python_exec = get_executable(config, 'python3')

    # possiblePair.listに含めるファイルリスト
    pair_files = primer_config.get('pair_files', [])
    if not pair_files:
        print("エラー: pair_filesが指定されていません", file=sys.stderr)
        sys.exit(1)

    # possiblePair.listのパス
    pair_list_file = primer_config.get('pair_list_file', 'possiblePair.list')

    # スクリプトのパス
    make_primer_script = primer_config.get('make_primer_script', 'make_primerList3_Wo5000.py')
    count_script = primer_config.get('count_script', 'count.py')

    print(f"Python: {python_exec}")
    print(f"make_primerList3 スクリプト: {make_primer_script}")
    print(f"count スクリプト: {count_script}")
    print()

    # 1. possiblePair.listファイルを作成
    print("1. possiblePair.listを作成します")
    missing_files = []
    for pair_file in pair_files:
        if not os.path.exists(pair_file):
            missing_files.append(pair_file)

    if missing_files:
        print(f"エラー: 以下のファイルが見つかりません:", file=sys.stderr)
        for f in missing_files:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(1)

    with open(pair_list_file, 'w', encoding='utf-8') as f:
        for pair_file in pair_files:
            f.write(f"{pair_file}\n")
    print(f"   出力: {pair_list_file}")
    print(f"   ファイル数: {len(pair_files)}")
    for pair_file in pair_files:
        print(f"     - {pair_file}")
    print()

    # スクリプトの存在確認
    if not os.path.exists(make_primer_script):
        print(f"エラー: スクリプトが見つかりません: {make_primer_script}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(count_script):
        print(f"エラー: スクリプトが見つかりません: {count_script}", file=sys.stderr)
        sys.exit(1)

    # 2. make_primerList3_Wo5000.pyを実行
    print("2. make_primerList3_Wo5000.py を実行します")
    run_python_script(python_exec, make_primer_script)
    print("   出力: unique_primer3.tab")
    print()

    # 3. count.pyを実行
    print("3. count.py を実行します")
    run_python_script(python_exec, count_script)
    print()

    print("全ての処理が完了しました")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 run_make_primer_list.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"エラー: 設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    run_make_primer_list(config)


if __name__ == '__main__':
    main()
