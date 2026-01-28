#!/usr/bin/env python3
"""
BLASTP データベース構築スクリプト

使用方法:
    python3 build_blastp_db.py config.yaml

設定ファイル（YAML形式）からパラメータを読み込み、
FASTAファイルの結合とBLASTPデータベースの構築を実行します。

必要な設定項目:
    build_blastp_db:
        input_files: FASTAファイルのリスト
        output_fasta: 結合後のFASTAファイルパス
        makeblastdb_executable: makeblastdbの実行ファイルパス（オプション）
        dbtype: データベースタイプ（デフォルト: prot）
"""

import sys
import os
import subprocess
import shutil
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
        dict: データベース構築設定
    """
    if 'build_blastp_db' not in config:
        print("エラー: 設定ファイルに 'build_blastp_db' セクションがありません。", file=sys.stderr)
        sys.exit(1)
    
    db_config = config['build_blastp_db']
    
    # 必須パラメータのチェック
    required_params = ['input_files', 'output_fasta']
    for param in required_params:
        if param not in db_config:
            print(f"エラー: 必須パラメータ '{param}' が設定ファイルにありません。", file=sys.stderr)
            sys.exit(1)
    
    # 入力ファイルの存在チェック
    input_files = db_config['input_files']
    if not isinstance(input_files, list):
        print("エラー: 'input_files' はリスト形式で指定してください。", file=sys.stderr)
        sys.exit(1)
    
    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"エラー: 入力ファイル '{input_file}' が見つかりません。", file=sys.stderr)
            sys.exit(1)
    
    # 出力ディレクトリの作成
    output_dir = os.path.dirname(db_config['output_fasta'])
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"出力ディレクトリを作成しました: {output_dir}")
    
    return db_config


def concatenate_fasta_files(input_files, output_fasta):
    """
    複数のFASTAファイルを結合する
    
    Args:
        input_files (list): 入力FASTAファイルのリスト
        output_fasta (str): 出力FASTAファイルパス
    """
    print("FASTAファイルを結合しています...")
    print(f"入力ファイル: {', '.join(input_files)}")
    print(f"出力ファイル: {output_fasta}")
    print("-" * 50)
    
    try:
        with open(output_fasta, 'w', encoding='utf-8') as outfile:
            for i, input_file in enumerate(input_files):
                print(f"処理中: {input_file} ({i+1}/{len(input_files)})")
                
                with open(input_file, 'r', encoding='utf-8') as infile:
                    # ファイルの内容を読み込んで出力ファイルに書き込み
                    content = infile.read()
                    outfile.write(content)
                    
                    # 最後のファイルでない場合、改行を追加
                    if not content.endswith('\n'):
                        outfile.write('\n')
        
        # 結合結果の確認
        if os.path.exists(output_fasta):
            file_size = os.path.getsize(output_fasta)
            print("結合が完了しました。")
            print(f"出力ファイル: {output_fasta}")
            print(f"ファイルサイズ: {file_size:,} bytes")
            
            # 配列数をカウント
            try:
                with open(output_fasta, 'r', encoding='utf-8') as f:
                    sequence_count = sum(
                        1 for line in f if line.startswith('>')
                    )
                print(f"配列数: {sequence_count:,} 個")
            except Exception as e:
                print(f"配列数カウント中にエラー: {e}")
        else:
            print("エラー: 結合ファイルが作成されませんでした。", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"エラー: ファイルの結合に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


def build_makeblastdb_command(config, db_config):
    """
    makeblastdbコマンドを構築する

    Args:
        config (dict): 設定全体
        db_config (dict): データベース構築設定

    Returns:
        list: makeblastdbコマンドリスト
    """
    # makeblastdbの実行ファイルパス（executables セクション優先）
    executable = get_executable(config, 'makeblastdb')
    
    # データベースタイプ（デフォルト: prot）
    dbtype = db_config.get('dbtype', 'prot')
    
    # 基本コマンド構築
    cmd = [
        executable,
        '-in', db_config['output_fasta'],
        '-dbtype', dbtype
    ]
    
    return cmd


def run_makeblastdb(cmd, db_config):
    """
    makeblastdbを実行する
    
    Args:
        cmd (list): makeblastdbコマンドリスト
        db_config (dict): データベース構築設定
    """
    print("BLASTPデータベースを構築しています...")
    print(f"コマンド: {' '.join(cmd)}")
    print(f"入力ファイル: {db_config['output_fasta']}")
    print(f"データベースタイプ: {db_config.get('dbtype', 'prot')}")
    print("-" * 50)
    
    try:
        # makeblastdbの実行
        cwd_path = os.path.dirname(os.path.abspath(db_config['output_fasta']))
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd_path or '.'
        )
        
        print("BLASTPデータベースの構築が正常に完了しました。")
        
        # 標準出力がある場合は表示
        if result.stdout:
            print("標準出力:")
            print(result.stdout)
        
        # 生成されたデータベースファイルの確認
        base_path = db_config['output_fasta']
        db_extensions = [
            '.phr', '.pin', '.pjs', '.pot', '.psq', '.ptf', '.pto'
        ]
        
        print("生成されたデータベースファイル:")
        total_size = 0
        for ext in db_extensions:
            db_file = base_path + ext
            if os.path.exists(db_file):
                file_size = os.path.getsize(db_file)
                total_size += file_size
                print(f"  {db_file}: {file_size:,} bytes")
            else:
                print(f"  {db_file}: 未作成")
        
        print(f"データベースファイル合計サイズ: {total_size:,} bytes")
            
    except subprocess.CalledProcessError as e:
        print(
            f"エラー: makeblastdbの実行に失敗しました（終了コード: {e.returncode}）",
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
            f"エラー: makeblastdbの実行ファイルが見つかりません: {cmd[0]}",
            file=sys.stderr
        )
        print(
            "BLAST+がインストールされているか、パスが正しいか確認してください。",
            file=sys.stderr
        )
        sys.exit(1)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='設定ファイルからBLASTPデータベースを構築する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 build_blastp_db.py config.yaml
    python3 build_blastp_db.py ../config.yaml

設定ファイルの例:
    build_blastp_db:
        input_files:
            - "../Materials/SpeciesA/SpeciesA.aa.fasta"
            - "../Materials/SpeciesB/SpeciesB.aa.fasta"
            - "../Materials/SpeciesC/SpeciesC.aa.fasta"
        output_fasta: "all_aa.fasta"
        dbtype: "prot"  # オプション（デフォルト: prot）
        makeblastdb_executable: "/path/to/makeblastdb"  # オプション
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
        '--concat-only',
        action='store_true',
        help='ファイルの結合のみ実行し、データベース構築は行わない'
    )
    
    args = parser.parse_args()
    
    # 設定ファイルの読み込み
    config = load_config(args.config_file)
    
    # 設定の妥当性チェック
    db_config = validate_config(config)
    
    if args.dry_run:
        print("ドライラン モード:")
        print("1. ファイル結合:")
        input_files_str = ' '.join(db_config['input_files'])
        print(f"   cat {input_files_str} > {db_config['output_fasta']}")
        
        if not args.concat_only:
            cmd = build_makeblastdb_command(config, db_config)
            print("2. データベース構築:")
            print(f"   {' '.join(cmd)}")
        return
    
    # FASTAファイルの結合
    concatenate_fasta_files(
        db_config['input_files'], db_config['output_fasta']
    )
    
    # データベースの構築（--concat-onlyが指定されていない場合）
    if not args.concat_only:
        cmd = build_makeblastdb_command(config, db_config)
        run_makeblastdb(cmd, db_config)
    else:
        print("ファイル結合のみが完了しました。データベース構築はスキップされました。")


if __name__ == '__main__':
    main()
