#!/usr/bin/env python3
"""
Primer3を実行するスクリプト

使用方法:
    python3 run_primer3.py config.yaml

設定ファイルのprimer3セクションから入出力ファイルパスを読み込み、
primer3_coreを実行します。
"""

import subprocess
import sys
import os
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
    3. name自体（PATHから検索）
    """
    executables = config.get('executables') or {}
    if name in executables and executables[name]:
        return executables[name]
    if fallback:
        return fallback
    return name


def run_primer3(config: dict) -> None:
    """primer3_coreを実行する"""
    primer3_config = config.get('primer3', {})

    # 設定値の取得
    input_file = primer3_config.get('input_file', 'primer3_input.list')
    output_file = primer3_config.get('output_file', 'primer3_output.list')
    executable = get_executable(config, 'primer3_core')
    working_dir = primer3_config.get('working_dir')

    # 作業ディレクトリの処理
    original_dir = os.getcwd()
    if working_dir:
        os.chdir(working_dir)
        print(f"作業ディレクトリ: {os.getcwd()}")

    try:
        # 入力ファイルの存在確認
        if not os.path.exists(input_file):
            print(f"エラー: 入力ファイルが見つかりません: {input_file}", file=sys.stderr)
            sys.exit(1)

        print(f"入力ファイル: {input_file}")
        print(f"出力ファイル: {output_file}")
        print(f"実行ファイル: {executable}")

        # primer3_coreを実行
        # primer3_core < input > output と同等の処理
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
            print(f"エラー: primer3_coreの実行に失敗しました", file=sys.stderr)
            if result.stderr:
                print(f"stderr: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)

        print(f"完了: {output_file} を作成しました")

    finally:
        # 元のディレクトリに戻る
        if working_dir:
            os.chdir(original_dir)


def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 run_primer3.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"エラー: 設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    run_primer3(config)


if __name__ == '__main__':
    main()
