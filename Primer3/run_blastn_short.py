#!/usr/bin/env python3
"""
BLASTN（blastn-short）を実行するスクリプト

使用方法:
    python3 run_blastn_short.py config.yaml

設定ファイルのblastn_shortセクションから設定を読み込み、
blastn -task blastn-short を実行してプライマー配列の検索を行います。
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


def run_blastn_short(config: dict) -> None:
    """BLASTN（blastn-short）を実行する"""
    blastn_config = config.get('blastn_short', {})

    # blastnの実行ファイルパス（executables セクション優先）
    executable = get_executable(config, 'blastn')

    # クエリファイル（プライマー配列）
    query = blastn_config.get('query', 'primer3.fa')

    # 出力フォーマット（デフォルト: 6 = tabular）
    outfmt = blastn_config.get('outfmt', 6)

    # スレッド数（デフォルト: 4）
    num_threads = blastn_config.get('num_threads', 4)

    # 検索対象データベースのリスト
    databases = blastn_config.get('databases', [])

    if not databases:
        print("エラー: データベース設定がありません", file=sys.stderr)
        sys.exit(1)

    # クエリファイルの存在確認
    if not os.path.exists(query):
        print(f"エラー: クエリファイルが見つかりません: {query}", file=sys.stderr)
        sys.exit(1)

    print(f"blastn: {executable}")
    print(f"クエリファイル: {query}")
    print(f"出力フォーマット: {outfmt}")
    print(f"スレッド数: {num_threads}")
    print(f"検索対象データベース数: {len(databases)}")
    print()

    for db in databases:
        name = db.get('name')
        db_path = db.get('db')
        output = db.get('output')

        if not name or not db_path:
            print(f"警告: name または db が指定されていないエントリをスキップします", file=sys.stderr)
            continue

        # 出力ファイル名が指定されていない場合は name.out を使用
        if not output:
            output = f"{name}.out"

        print(f"BLASTN実行: {name}")
        print(f"  データベース: {db_path}")
        print(f"  出力: {output}")

        # blastn -task blastn-short を実行
        cmd = [
            executable,
            '-task', 'blastn-short',
            '-db', db_path,
            '-query', query,
            '-out', output,
            '-outfmt', str(outfmt),
            '-num_threads', str(num_threads)
        ]
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
            print(f"エラー: blastnの実行に失敗しました", file=sys.stderr)
            if result.stderr:
                print(f"stderr: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)

        print(f"  完了: {output} を作成しました")
        print()

    print("全てのBLASTN検索が完了しました")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 run_blastn_short.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"エラー: 設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    run_blastn_short(config)


if __name__ == '__main__':
    main()
