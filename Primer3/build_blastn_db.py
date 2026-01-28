#!/usr/bin/env python3
"""
BLASTN用データベースを構築するスクリプト

使用方法:
    python3 build_blastn_db.py config.yaml

設定ファイルのbuild_blastn_dbセクションから設定を読み込み、
makeblastdbを実行してBLASTNデータベースを構築します。
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


def build_blastn_db(config: dict) -> None:
    """BLASTNデータベースを構築する"""
    db_config = config.get('build_blastn_db', {})

    # makeblastdbの実行ファイルパス（executables セクション優先）
    executable = get_executable(config, 'makeblastdb')

    # データベースタイプ（デフォルト: nucl）
    dbtype = db_config.get('dbtype', 'nucl')

    # 構築するデータベースのリスト
    databases = db_config.get('databases', [])

    if not databases:
        print("エラー: データベース設定がありません", file=sys.stderr)
        sys.exit(1)

    print(f"makeblastdb: {executable}")
    print(f"データベースタイプ: {dbtype}")
    print(f"構築するデータベース数: {len(databases)}")
    print()

    for db in databases:
        name = db.get('name')
        input_file = db.get('input')
        output_name = db.get('output')

        if not name or not input_file:
            print(f"警告: name または input が指定されていないエントリをスキップします", file=sys.stderr)
            continue

        # 出力名が指定されていない場合は name.fna を使用
        if not output_name:
            output_name = f"{name}.fna"

        # 入力ファイルの存在確認
        if not os.path.exists(input_file):
            print(f"エラー: 入力ファイルが見つかりません: {input_file}", file=sys.stderr)
            sys.exit(1)

        print(f"データベース構築: {name}")
        print(f"  入力: {input_file}")
        print(f"  出力: {output_name}")

        # makeblastdbを実行
        cmd = [
            executable,
            '-in', input_file,
            '-out', output_name,
            '-dbtype', dbtype
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
            print(f"エラー: makeblastdbの実行に失敗しました", file=sys.stderr)
            if result.stderr:
                print(f"stderr: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)

        print(f"  完了: {output_name} データベースを作成しました")
        print()

    print("全てのデータベース構築が完了しました")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 build_blastn_db.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"エラー: 設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    build_blastn_db(config)


if __name__ == '__main__':
    main()
