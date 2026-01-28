#!/usr/bin/env python3
"""
GMAP 実行スクリプト

使用方法:
    python3 run_gmap.py config.yaml

設定ファイル（YAML形式）からパラメータを読み込み、
GMAPを実行してGFF3ファイルを生成します。

必要な設定項目:
    gmap:
        query: クエリFASTAファイル（Nohit_cds.fa等）
        output_format: 出力フォーマット（gff3_gene等）
        databases:
            - name: データベース名（プレフィックス）
              output: 出力GFF3ファイル名

    gmap_build:
        db_dir: GMAPデータベースのディレクトリ

    executables:
        gmap: gmapの実行ファイルパス（オプション）
"""

import sys
import os
import subprocess
import yaml
import argparse


def get_executable(config, name, fallback=None):
    """
    実行ファイルパスを取得する

    優先順位:
    1. config['executables'][name]
    2. fallback（指定された場合）
    3. name自体（PATHから検索）

    Args:
        config (dict): 設定全体
        name (str): 実行ファイル名
        fallback (str): フォールバック値

    Returns:
        str: 実行ファイルパス
    """
    # executables セクションから取得
    executables = config.get('executables') or {}
    if name in executables and executables[name]:
        return executables[name]

    # フォールバック値があれば使用
    if fallback:
        return fallback

    # デフォルトはname自体（PATHから検索される）
    return name


def load_config(config_file):
    """
    YAML設定ファイルを読み込む

    Args:
        config_file (str): 設定ファイルのパス

    Returns:
        dict: 設定内容
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"エラー: 設定ファイル '{config_file}' が見つかりません。", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"エラー: 設定ファイルの読み込みに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


def validate_config(config):
    """
    設定の妥当性をチェックする

    Args:
        config (dict): 設定内容

    Returns:
        dict: GMAP実行設定
    """
    if 'gmap' not in config:
        print("エラー: 設定ファイルに 'gmap' セクションがありません。", file=sys.stderr)
        sys.exit(1)

    gmap_config = config['gmap']

    # 必須パラメータのチェック
    required_params = ['query', 'databases']
    for param in required_params:
        if param not in gmap_config:
            print(f"エラー: 必須パラメータ '{param}' が設定ファイルにありません。", file=sys.stderr)
            sys.exit(1)

    # クエリファイルの存在確認
    if not os.path.exists(gmap_config['query']):
        print(f"エラー: クエリファイル '{gmap_config['query']}' が見つかりません。", file=sys.stderr)
        sys.exit(1)

    # databasesがリストであることをチェック
    if not isinstance(gmap_config['databases'], list):
        print("エラー: 'databases' はリスト形式で指定してください。", file=sys.stderr)
        sys.exit(1)

    if len(gmap_config['databases']) == 0:
        print("エラー: 'databases' に少なくとも1つのデータベース設定が必要です。", file=sys.stderr)
        sys.exit(1)

    # gmap_buildセクションからdb_dirを取得
    if 'gmap_build' not in config or 'db_dir' not in config['gmap_build']:
        print("エラー: 'gmap_build.db_dir' が設定ファイルにありません。", file=sys.stderr)
        sys.exit(1)

    db_dir = config['gmap_build']['db_dir']

    # 各データベース設定の検証
    for i, db in enumerate(gmap_config['databases']):
        if 'name' not in db:
            print(f"エラー: databases[{i}] に 'name' がありません。", file=sys.stderr)
            sys.exit(1)
        if 'output' not in db:
            print(f"エラー: databases[{i}] に 'output' がありません。", file=sys.stderr)
            sys.exit(1)

        # データベースの存在確認
        db_path = os.path.join(db_dir, db['name'])
        if not os.path.exists(db_path):
            print(f"エラー: GMAPデータベース '{db_path}' が見つかりません。", file=sys.stderr)
            print("先にbuild_gmap_db.pyを実行してデータベースを構築してください。", file=sys.stderr)
            sys.exit(1)

    return gmap_config


def build_gmap_command(config, gmap_config, db_entry):
    """
    gmapコマンドを構築する

    Args:
        config (dict): 設定全体
        gmap_config (dict): GMAP実行設定
        db_entry (dict): 個別のデータベース設定

    Returns:
        list: gmapコマンドリスト
    """
    # gmapの実行ファイルパス
    executable = get_executable(config, 'gmap')

    # データベースディレクトリ
    db_dir = config['gmap_build']['db_dir']

    # 出力フォーマット（デフォルト: gff3_gene）
    output_format = gmap_config.get('output_format', 'gff3_gene')

    # コマンド構築
    cmd = [
        executable,
        '-D', db_dir,
        '-d', db_entry['name'],
        '-f', output_format,
        gmap_config['query']
    ]

    return cmd


def run_gmap(cmd, db_entry):
    """
    gmapを実行する

    Args:
        cmd (list): gmapコマンドリスト
        db_entry (dict): 個別のデータベース設定
    """
    output_file = db_entry['output']

    print(f"GMAP検索 '{db_entry['name']}' を実行しています...")
    print(f"コマンド: {' '.join(cmd)} > {output_file}")
    print("-" * 50)

    try:
        # gmapの実行（出力をファイルにリダイレクト）
        with open(output_file, 'w', encoding='utf-8') as out_f:
            result = subprocess.run(
                cmd,
                check=True,
                stdout=out_f,
                stderr=subprocess.PIPE,
                text=True
            )

        print(f"GMAP検索 '{db_entry['name']}' が正常に完了しました。")
        print(f"出力ファイル: {output_file}")

        # 出力ファイルのサイズ確認
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"ファイルサイズ: {file_size:,} bytes")

            # 行数カウント
            with open(output_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            print(f"行数: {line_count:,}")
        else:
            print(f"警告: 出力ファイル '{output_file}' が生成されていません。")

        # 標準エラー出力がある場合は表示
        if result.stderr:
            print("標準エラー出力:")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(
            f"エラー: gmapの実行に失敗しました（終了コード: {e.returncode}）",
            file=sys.stderr
        )
        if e.stderr:
            print("標準エラー出力:", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"エラー: gmapの実行ファイルが見つかりません: {cmd[0]}",
            file=sys.stderr
        )
        print(
            "GMAPがインストールされているか、パスが正しいか確認してください。",
            file=sys.stderr
        )
        sys.exit(1)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='設定ファイルからGMAPを実行してGFF3ファイルを生成する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 run_gmap.py config.yaml
    python3 run_gmap.py ../config.yaml

設定ファイルの例:
    gmap:
        query: "../BLASTP/Nohit_cds.fa"
        output_format: "gff3_gene"
        databases:
            - name: "SpeciesB"
              output: "SpeciesB.gff3"
            - name: "SpeciesC"
              output: "SpeciesC.gff3"

    gmap_build:
        db_dir: "../GMAP"
        """
    )

    parser.add_argument(
        'config_file',
        help='YAML形式の設定ファイルパス'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際には実行せず、コマンドのみ表示する'
    )

    parser.add_argument(
        '--database', '-d',
        help='特定のデータベースのみ検索する（名前で指定）'
    )

    args = parser.parse_args()

    # 設定ファイルの読み込み
    config = load_config(args.config_file)

    # 設定の妥当性チェック
    gmap_config = validate_config(config)

    # 検索対象のデータベースを決定
    databases = gmap_config['databases']
    if args.database:
        databases = [db for db in databases if db['name'] == args.database]
        if not databases:
            print(f"エラー: データベース '{args.database}' が設定ファイルに見つかりません。", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print("ドライラン モード: 以下のコマンドが実行されます:")
        for db_entry in databases:
            cmd = build_gmap_command(config, gmap_config, db_entry)
            print(f"  {' '.join(cmd)} > {db_entry['output']}")
        return

    # GMAP検索の実行
    print(f"検索するデータベース数: {len(databases)}")
    print(f"クエリファイル: {gmap_config['query']}")
    print("=" * 60)

    for i, db_entry in enumerate(databases):
        print(f"\n[{i+1}/{len(databases)}] データベース: {db_entry['name']}")
        print("=" * 60)

        cmd = build_gmap_command(config, gmap_config, db_entry)
        run_gmap(cmd, db_entry)

        print()

    print("=" * 60)
    print("すべてのGMAP検索が完了しました。")


if __name__ == '__main__':
    main()
