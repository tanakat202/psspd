#!/usr/bin/env python3
"""
GMAP データベース構築スクリプト

使用方法:
    python3 build_gmap_db.py config.yaml

設定ファイル（YAML形式）からパラメータを読み込み、
GMAPデータベースを構築します。

必要な設定項目:
    gmap_build:
        executable: gmap_buildの実行ファイルパス（オプション）
        perl_interpreter: Perlインタープリタのパス（オプション）
        db_dir: データベースを作成するディレクトリ
        databases:
            - name: データベース名（プレフィックス）
              genome: ゲノムFASTAファイルパス
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
        dict: GMAP構築設定
    """
    if 'gmap_build' not in config:
        print("エラー: 設定ファイルに 'gmap_build' セクションがありません。", file=sys.stderr)
        sys.exit(1)

    gmap_config = config['gmap_build']

    # 必須パラメータのチェック
    required_params = ['db_dir', 'databases']
    for param in required_params:
        if param not in gmap_config:
            print(f"エラー: 必須パラメータ '{param}' が設定ファイルにありません。", file=sys.stderr)
            sys.exit(1)

    # databasesがリストであることをチェック
    if not isinstance(gmap_config['databases'], list):
        print("エラー: 'databases' はリスト形式で指定してください。", file=sys.stderr)
        sys.exit(1)

    if len(gmap_config['databases']) == 0:
        print("エラー: 'databases' に少なくとも1つのデータベース設定が必要です。", file=sys.stderr)
        sys.exit(1)

    # 各データベース設定の検証
    for i, db in enumerate(gmap_config['databases']):
        if 'name' not in db:
            print(f"エラー: databases[{i}] に 'name' がありません。", file=sys.stderr)
            sys.exit(1)
        if 'genome' not in db:
            print(f"エラー: databases[{i}] に 'genome' がありません。", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(db['genome']):
            print(f"エラー: ゲノムファイル '{db['genome']}' が見つかりません。", file=sys.stderr)
            sys.exit(1)

    # データベースディレクトリの作成
    db_dir = gmap_config['db_dir']
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"データベースディレクトリを作成しました: {db_dir}")

    return gmap_config


def build_gmap_build_command(config, gmap_config, db_entry):
    """
    gmap_buildコマンドを構築する

    Args:
        config (dict): 設定全体
        gmap_config (dict): GMAP構築設定
        db_entry (dict): 個別のデータベース設定

    Returns:
        list: gmap_buildコマンドリスト
    """
    # gmap_buildの実行ファイルパス（executables セクション優先）
    executable = get_executable(config, 'gmap_build')

    # Perlインタープリタの設定（shebangが壊れている場合に使用）
    # executables セクション優先
    perl_interpreter = get_executable(config, 'perl', None)
    # perl は None が返る可能性があるので、明示的にNoneチェック
    executables = config.get('executables') or {}
    if 'perl' not in executables or not executables.get('perl'):
        perl_interpreter = None

    # 基本コマンド構築
    if perl_interpreter:
        # Perlインタープリタ経由で実行
        cmd = [
            perl_interpreter,
            executable,
            '-D', gmap_config['db_dir'],
            '-d', db_entry['name'],
            db_entry['genome']
        ]
    else:
        cmd = [
            executable,
            '-D', gmap_config['db_dir'],
            '-d', db_entry['name'],
            db_entry['genome']
        ]

    return cmd


def run_gmap_build(cmd, db_entry, gmap_config):
    """
    gmap_buildを実行する

    Args:
        cmd (list): gmap_buildコマンドリスト
        db_entry (dict): 個別のデータベース設定
        gmap_config (dict): GMAP構築設定
    """
    print(f"GMAPデータベース '{db_entry['name']}' を構築しています...")
    print(f"コマンド: {' '.join(cmd)}")
    print(f"ゲノムファイル: {db_entry['genome']}")
    print(f"出力ディレクトリ: {gmap_config['db_dir']}")
    print("-" * 50)

    try:
        # gmap_buildの実行
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        print(f"GMAPデータベース '{db_entry['name']}' の構築が正常に完了しました。")

        # 標準出力がある場合は表示
        if result.stdout:
            print("標準出力:")
            print(result.stdout)

        # 生成されたデータベースの確認
        db_path = os.path.join(gmap_config['db_dir'], db_entry['name'])
        if os.path.exists(db_path):
            print(f"データベースディレクトリ: {db_path}")
            # ディレクトリ内のファイル一覧
            try:
                files = os.listdir(db_path)
                if files:
                    print(f"生成されたファイル数: {len(files)}")
                else:
                    print("警告: データベースディレクトリが空です。")
            except Exception as e:
                print(f"ディレクトリ読み込みエラー: {e}")
        else:
            print(f"警告: データベースディレクトリ '{db_path}' が見つかりません。")

    except subprocess.CalledProcessError as e:
        print(
            f"エラー: gmap_buildの実行に失敗しました（終了コード: {e.returncode}）",
            file=sys.stderr
        )
        if e.stdout:
            print("標準出力:", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print("標準エラー出力:", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"エラー: gmap_buildの実行ファイルが見つかりません: {cmd[0]}",
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
        description='設定ファイルからGMAPデータベースを構築する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 build_gmap_db.py config.yaml
    python3 build_gmap_db.py ../config.yaml

設定ファイルの例:
    gmap_build:
        executable: "/path/to/gmap_build"  # オプション
        db_dir: "./"
        databases:
            - name: "SpeciesB"
              genome: "../Materials/DL_data/genome_B.fna"
            - name: "SpeciesC"
              genome: "../Materials/DL_data/genome_C.fna"
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
        help='特定のデータベースのみ構築する（名前で指定）'
    )

    args = parser.parse_args()

    # 設定ファイルの読み込み
    config = load_config(args.config_file)

    # 設定の妥当性チェック
    gmap_config = validate_config(config)

    # 構築対象のデータベースを決定
    databases = gmap_config['databases']
    if args.database:
        databases = [db for db in databases if db['name'] == args.database]
        if not databases:
            print(f"エラー: データベース '{args.database}' が設定ファイルに見つかりません。", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print("ドライラン モード: 以下のコマンドが実行されます:")
        for db_entry in databases:
            cmd = build_gmap_build_command(config, gmap_config, db_entry)
            print(f"  {' '.join(cmd)}")
        return

    # データベースの構築
    print(f"構築するデータベース数: {len(databases)}")
    print("=" * 60)

    for i, db_entry in enumerate(databases):
        print(f"\n[{i+1}/{len(databases)}] データベース: {db_entry['name']}")
        print("=" * 60)

        cmd = build_gmap_build_command(config, gmap_config, db_entry)
        run_gmap_build(cmd, db_entry, gmap_config)

        print()

    print("=" * 60)
    print("すべてのGMAPデータベースの構築が完了しました。")


if __name__ == '__main__':
    main()
