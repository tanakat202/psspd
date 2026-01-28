#!/usr/bin/env python3
"""
BLASTPでヒットしない遺伝子のCDS配列を抽出するスクリプト

使用方法:
    python3 extract_nohit.fa.py config.yaml

設定ファイル（YAML形式）からパラメータを読み込み、
ヒットしない遺伝子のリストからCDS配列を抽出します。

必要な設定項目:
    extract_nohit:
        target: 対象種名
        nohits_file: ヒットしない遺伝子リストファイル
        input_cds_file: 入力CDSファイル
        output_file: 出力ファイル
"""

import os
import sys
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
        dict: extract_nohit設定
    """
    if 'extract_nohit' not in config:
        print("エラー: 設定ファイルに 'extract_nohit' セクションがありません。", file=sys.stderr)
        sys.exit(1)
    
    extract_config = config['extract_nohit']
    
    # 必須パラメータのチェック
    required_params = ['target', 'nohits_file', 'input_cds_file',
                       'output_file']
    for param in required_params:
        if param not in extract_config:
            print(f"エラー: 必須パラメータ '{param}' が設定ファイルにありません。", file=sys.stderr)
            sys.exit(1)
    
    target = extract_config['target']
    
    # パスの展開（{target}の置換）
    input_template = extract_config['input_cds_file']
    extract_config['input_cds_file'] = input_template.format(target=target)
    
    return extract_config


def load_nohits_list(nohits_file):
    """
    ヒットしない遺伝子のリストを読み込む
    
    Args:
        nohits_file (str): ヒットしない遺伝子リストファイル
        
    Returns:
        dict: 遺伝子IDの辞書
    """
    if not os.path.exists(nohits_file):
        print(f"エラー: ヒットしない遺伝子リストファイル"
              f" '{nohits_file}' が見つかりません。", file=sys.stderr)
        sys.exit(1)
    
    nohits_dict = {}
    try:
        with open(nohits_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # 空行をスキップ
                    nohits_dict[line] = 1
        
        print(f"ヒットしない遺伝子数: {len(nohits_dict)}")
        return nohits_dict
        
    except (IOError, OSError) as e:
        print(f"エラー: ヒットしない遺伝子リストファイルの読み込みに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


def extract_sequences(extract_config, nohits_dict):
    """
    ヒットしない遺伝子のCDS配列を抽出する
    
    Args:
        extract_config (dict): extract_nohit設定
        nohits_dict (dict): ヒットしない遺伝子IDの辞書
    """
    input_file = extract_config['input_cds_file']
    output_file = extract_config['output_file']
    target = extract_config['target']
    
    # 入力ファイルの存在チェック
    if not os.path.exists(input_file):
        print(f"エラー: 入力CDSファイル '{input_file}' が見つかりません。", file=sys.stderr)
        sys.exit(1)
    
    print(f"対象種名: {target}")
    print(f"入力ファイル: {input_file}")
    print(f"出力ファイル: {output_file}")
    print("CDS配列を抽出しています...")
    
    extracted_count = 0
    found_sequences = False
    
    try:
        with open(output_file, "w", encoding='utf-8') as out_file:
            with open(input_file, "r", encoding='utf-8') as in_file:
                for line in in_file:
                    line = line.strip()
                    
                    if line.startswith(">"):  # シーケンスヘッダー行
                        seq_id = line.split(' ', 1)[0][1:]  # '>'を除去して最初のスペースまで
                        
                        if seq_id in nohits_dict:
                            out_file.write(f"{line}\n")
                            found_sequences = True
                            extracted_count += 1
                        else:
                            found_sequences = False
                            
                    elif found_sequences:
                        # 現在のシーケンスが対象の場合、配列行を出力
                        out_file.write(f"{line}\n")
        
        print(f"抽出された配列数: {extracted_count}")
        
        # 出力ファイルの確認
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"出力ファイル '{output_file}' を作成しました。")
            print(f"ファイルサイズ: {file_size:,} bytes")
            
            # 簡単な統計
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                sequence_count = sum(1 for line in lines
                                     if line.startswith('>'))
                print(f"配列数: {sequence_count}")
        
        if extracted_count == 0:
            print("警告: 抽出された配列がありません。ファイルパスや遺伝子IDを確認してください。")
            
    except (IOError, OSError) as e:
        print(f"エラー: CDS配列の抽出中にエラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='設定ファイルからヒットしない遺伝子のCDS配列を抽出する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 extract_nohit.fa.py config.yaml
    python3 extract_nohit.fa.py ../config.yaml

設定ファイルの例:
    extract_nohit:
        target: "SpeciesA"
        nohits_file: "blastp_nohits.tab"
        input_cds_file: "../Materials/{target}/{target}.cds.fasta"
        output_file: "Nohit_cds.fa"
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
    extract_config = validate_config(config)
    
    # ヒットしない遺伝子リストの読み込み
    nohits_dict = load_nohits_list(extract_config['nohits_file'])
    
    # CDS配列の抽出
    extract_sequences(extract_config, nohits_dict)


if __name__ == '__main__':
    main()
