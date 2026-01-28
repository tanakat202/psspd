#!/usr/bin/env python3
"""
Primer3入力ファイル生成スクリプト

使用方法:
    python3 make_primer3_input.py config.yaml

設定ファイル（YAML形式）からパラメータを読み込み、
Target_cds.faからprimer3_input.listを生成します。

必要な設定項目:
    make_primer3_input:
        input_cds: 入力CDSファイル（Target_cds.fa）
        output_file: 出力ファイル（primer3_input.list）
        primer_opt_size: 最適プライマー長（デフォルト: 20）
        primer_min_size: 最小プライマー長（デフォルト: 18）
        primer_max_size: 最大プライマー長（デフォルト: 27）
        product_size_range: 増幅産物サイズ範囲（デフォルト: 300-500）
"""

import sys
import os
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
        dict: make_primer3_input設定
    """
    if 'make_primer3_input' not in config:
        print("エラー: 設定ファイルに 'make_primer3_input' セクションがありません。", file=sys.stderr)
        sys.exit(1)

    primer3_input_config = config['make_primer3_input']

    # 必須パラメータのチェック
    required_params = ['input_cds', 'output_file']
    for param in required_params:
        if param not in primer3_input_config:
            print(f"エラー: 必須パラメータ '{param}' が設定ファイルにありません。", file=sys.stderr)
            sys.exit(1)

    # 入力ファイルの存在チェック
    if not os.path.exists(primer3_input_config['input_cds']):
        print(f"エラー: 入力ファイル '{primer3_input_config['input_cds']}' が見つかりません。", file=sys.stderr)
        sys.exit(1)

    return primer3_input_config


def make_primer3_input(config):
    """
    Primer3入力ファイルを生成する

    Args:
        config (dict): make_primer3_input設定

    Returns:
        int: 処理したシーケンス数
    """
    input_cds = config['input_cds']
    output_file = config['output_file']

    # Primer3パラメータ（デフォルト値付き）
    primer_opt_size = config.get('primer_opt_size', 20)
    primer_min_size = config.get('primer_min_size', 18)
    primer_max_size = config.get('primer_max_size', 27)
    product_size_range = config.get('product_size_range', '300-500')

    seq_count = 0

    with open(input_cds, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('>'):
                    # ヘッダー行: IDを抽出
                    seq_id = line[1:].split()[0]
                    outfile.write(f"SEQUENCE_ID={seq_id}\n")
                else:
                    # 配列行: テンプレートとパラメータを出力
                    outfile.write(f"SEQUENCE_TEMPLATE={line}\n")
                    outfile.write(f"PRIMER_OPT_SIZE={primer_opt_size}\n")
                    outfile.write(f"PRIMER_MIN_SIZE={primer_min_size}\n")
                    outfile.write(f"PRIMER_MAX_SIZE={primer_max_size}\n")
                    outfile.write(f"PRIMER_PRODUCT_SIZE_RANGE={product_size_range}\n")
                    outfile.write("=\n")
                    seq_count += 1

    return seq_count


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='Target_cds.faからPrimer3入力ファイルを生成する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 make_primer3_input.py config.yaml
    python3 make_primer3_input.py ../config.yaml

設定ファイルの例:
    make_primer3_input:
        input_cds: "../GMAP/Target_cds.fa"
        output_file: "primer3_input.list"
        primer_opt_size: 20
        primer_min_size: 18
        primer_max_size: 27
        product_size_range: "300-500"
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
    primer3_input_config = validate_config(config)

    print("=" * 60)
    print("Primer3入力ファイル生成")
    print("=" * 60)
    print(f"入力ファイル: {primer3_input_config['input_cds']}")
    print(f"出力ファイル: {primer3_input_config['output_file']}")
    print(f"PRIMER_OPT_SIZE: {primer3_input_config.get('primer_opt_size', 20)}")
    print(f"PRIMER_MIN_SIZE: {primer3_input_config.get('primer_min_size', 18)}")
    print(f"PRIMER_MAX_SIZE: {primer3_input_config.get('primer_max_size', 27)}")
    print(f"PRIMER_PRODUCT_SIZE_RANGE: {primer3_input_config.get('product_size_range', '300-500')}")
    print("-" * 60)

    seq_count = make_primer3_input(primer3_input_config)

    print(f"処理したシーケンス数: {seq_count}")
    print("=" * 60)
    print("処理が完了しました。")


if __name__ == '__main__':
    main()
