#!/usr/bin/env python3
"""
BLASTP実行スクリプト

使用方法:
    python3 run_blastp.py config.yaml

設定ファイル（YAML形式）からBLASTPのパラメータを読み込み、
BLASTPを実行します。

必要な設定項目:
    blastp:
        database: データベースファイルパス
        query: クエリファイルパス
        output: 出力ファイルパス
        evalue: E-value閾値（オプション、デフォルト: 1E-5）
        outfmt: 出力フォーマット（オプション、デフォルト: 6）
        num_threads: スレッド数（オプション、デフォルト: 4）
        executable: BLASTPの実行ファイルパス（オプション）
"""

import sys
import os
import subprocess
import yaml
import argparse
from pathlib import Path


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


def validate_blastp_config(config):
    """
    BLASTP設定の妥当性をチェックする
    
    Args:
        config (dict): 設定内容
        
    Returns:
        dict: BLASTP設定
    """
    if 'blastp' not in config:
        print("エラー: 設定ファイルに 'blastp' セクションがありません。", file=sys.stderr)
        sys.exit(1)
    
    blastp_config = config['blastp']
    
    # 必須パラメータのチェック
    required_params = ['database', 'query', 'output']
    for param in required_params:
        if param not in blastp_config:
            print(f"エラー: 必須パラメータ '{param}' が設定ファイルにありません。", file=sys.stderr)
            sys.exit(1)
    
    # データベースファイルの存在チェック
    if not os.path.exists(blastp_config['database']):
        print(f"エラー: データベースファイル '{blastp_config['database']}' が見つかりません。", file=sys.stderr)
        sys.exit(1)
    
    # クエリファイルの存在チェック
    if not os.path.exists(blastp_config['query']):
        print(f"エラー: クエリファイル '{blastp_config['query']}' が見つかりません。", file=sys.stderr)
        sys.exit(1)
    
    # 出力ディレクトリの作成
    output_dir = os.path.dirname(blastp_config['output'])
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"出力ディレクトリを作成しました: {output_dir}")
    
    return blastp_config


def build_blastp_command(config, blastp_config):
    """
    BLASTPコマンドを構築する

    Args:
        config (dict): 設定全体
        blastp_config (dict): BLASTP設定

    Returns:
        list: BLASTPコマンドリスト
    """
    # BLASTPの実行ファイルパス（executables セクション優先）
    executable = get_executable(config, 'blastp')
    
    # 基本コマンド構築
    cmd = [
        executable,
        '-db', blastp_config['database'],
        '-query', blastp_config['query'],
        '-out', blastp_config['output']
    ]
    
    # オプションパラメータの追加
    if 'evalue' in blastp_config:
        cmd.extend(['-evalue', str(blastp_config['evalue'])])
    
    if 'outfmt' in blastp_config:
        cmd.extend(['-outfmt', str(blastp_config['outfmt'])])
    
    if 'num_threads' in blastp_config:
        cmd.extend(['-num_threads', str(blastp_config['num_threads'])])
    
    return cmd


def run_blastp(cmd, blastp_config):
    """
    BLASTPを実行する
    
    Args:
        cmd (list): BLASTPコマンドリスト
        blastp_config (dict): BLASTP設定
    """
    print("BLASTPを実行しています...")
    print(f"コマンド: {' '.join(cmd)}")
    print(f"データベース: {blastp_config['database']}")
    print(f"クエリ: {blastp_config['query']}")
    print(f"出力ファイル: {blastp_config['output']}")
    print("-" * 50)
    
    try:
        # BLASTPの実行
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("BLASTPが正常に完了しました。")
        
        # 標準出力がある場合は表示
        if result.stdout:
            print("標準出力:")
            print(result.stdout)
        
        # 出力ファイルの確認
        if os.path.exists(blastp_config['output']):
            file_size = os.path.getsize(blastp_config['output'])
            print(f"出力ファイル '{blastp_config['output']}' が作成されました。")
            print(f"ファイルサイズ: {file_size:,} bytes")
            
            # 結果の簡単な統計
            try:
                with open(blastp_config['output'], 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"結果行数: {len(lines):,} 行")
                        print("最初の数行:")
                        for i, line in enumerate(lines[:3]):
                            print(f"  {i+1}: {line.strip()}")
                        if len(lines) > 3:
                            print("  ...")
                    else:
                        print("出力ファイルは空です。")
            except Exception as e:
                print(f"出力ファイルの読み込みエラー: {e}")
        else:
            print(f"警告: 出力ファイル '{blastp_config['output']}' が見つかりません。")
            
    except subprocess.CalledProcessError as e:
        print(f"エラー: BLASTPの実行に失敗しました（終了コード: {e.returncode}）", file=sys.stderr)
        if e.stdout:
            print("標準出力:", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print("標準エラー出力:", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"エラー: BLASTPの実行ファイルが見つかりません: {cmd[0]}", file=sys.stderr)
        print("BLASTPがインストールされているか、パスが正しいか確認してください。", file=sys.stderr)
        sys.exit(1)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='設定ファイルからBLASTPを実行する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 run_blastp.py config.yaml
    python3 run_blastp.py ../config.yaml

設定ファイルの例:
    blastp:
        database: "BLASTP/all_aa.fasta"
        query: "BLASTP/all_aa.fasta"
        output: "BLASTP/blastp.out"
        evalue: "1E-5"
        outfmt: 6
        num_threads: 4
        executable: "/path/to/blastp"  # オプション
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
    
    args = parser.parse_args()
    
    # 設定ファイルの読み込み
    config = load_config(args.config_file)
    
    # BLASTP設定の妥当性チェック
    blastp_config = validate_blastp_config(config)

    # BLASTPコマンドの構築
    cmd = build_blastp_command(config, blastp_config)
    
    if args.dry_run:
        print("ドライラン モード: 以下のコマンドが実行されます:")
        print(' '.join(cmd))
        return
    
    # BLASTPの実行
    run_blastp(cmd, blastp_config)


if __name__ == '__main__':
    main()