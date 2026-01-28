#!/usr/bin/env python3
"""
BLASTP結果からヒットしない遺伝子を抽出するスクリプト

使用方法:
    python3 pick_nohit_genes.py config.yaml

設定ファイル（YAML形式）からターゲット種名を読み込み、
BLASTP結果を解析してヒットしない遺伝子を抽出します。
"""

import sys
import os
import re
import yaml
import argparse


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
        str: ターゲット種名
    """
    if 'no_hit_analysis' not in config:
        print("エラー: 設定ファイルに 'no_hit_analysis' セクションがありません。", file=sys.stderr)
        sys.exit(1)
    
    analysis_config = config['no_hit_analysis']
    
    if 'target' not in analysis_config:
        print("エラー: 必須パラメータ 'target' が設定ファイルにありません。", file=sys.stderr)
        sys.exit(1)
    
    target = analysis_config['target']
    
    # ターゲット種名の妥当性チェック
    valid_targets = ['SpeciesA', 'SpeciesB', 'SpeciesC']
    if target not in valid_targets:
        print(f"エラー: 無効なターゲット種名 '{target}'。"
              f"有効な値: {', '.join(valid_targets)}", file=sys.stderr)
        sys.exit(1)
    
    return target


def analyze_nohits(target):
    """
    BLASTP結果からヒットしない遺伝子を抽出する
    
    Args:
        target (str): ターゲット種名
    """
    # Set up BLAST result file open blastp.out
    if not os.path.exists("blastp.out"):
        print("エラー: blastp.out ファイルが存在しません。")
        return

    print(f"解析対象種名: {target}")
    print("BLASTP結果を解析しています...")
    
    # Open output file for writing in text mode
    with open("blastp_nohits.tab", "w+", encoding='utf-8') as out_file:
        # Read from blastp.out file
        blast_input = open("blastp.out", "r", encoding='utf-8')
        a = 0
        large_a = 0

        before_seq = ""
        seq_id = None
        while True:

            line = next(blast_input, "")
            if not line:  # End of file reached
                break
       
            parts = line.strip().split("\t")

            if len(parts) >= 2 and target in parts[0]:
                seq_id = parts[0]
                
                if (before_seq and re.search(r'\w', before_seq) and
                        seq_id not in before_seq):
                    if large_a == 0:
                        print(f"{before_seq}", file=out_file)
                        a += 1
                    
                    large_a = 0
                if target not in parts[1]:
                    large_a = 1
            before_seq = seq_id

        if large_a == 0 and before_seq:
            print(f"{before_seq}", file=out_file)
            a += 1
        
        blast_input.close()
        
    print(f"ヒットしない遺伝子数: {a}")
    print("結果ファイル 'blastp_nohits.tab' を作成しました。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='設定ファイルからBLASTP結果を解析してヒットしない遺伝子を抽出する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 pick_nohit_genes.py config.yaml
    python3 pick_nohit_genes.py ../config.yaml

設定ファイルの例:
    no_hit_analysis:
        target: "SpeciesB"
        """
    )
    
    parser.add_argument(
        'config_file',
        help='YAML形式の設定ファイルパス'
    )
    
    args = parser.parse_args()
    
    # 設定ファイルの読み込み
    config = load_config(args.config_file)
    
    # 設定の妥当性チェック
    target = validate_config(config)
    
    # ヒットしない遺伝子の解析
    analyze_nohits(target)


if __name__ == "__main__":
    main()
