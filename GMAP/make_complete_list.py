#!/usr/bin/env python3
"""
GMAPヒットリストから最終ターゲットリストを作成するスクリプト

使用方法:
    python3 make_complete_list.py config.yaml

設定ファイル（YAML形式）からパラメータを読み込み、
複数のヒットリストファイルを統合し、ヒットしなかったCDS配列を抽出します。

必要な設定項目:
    make_complete_list:
        hit_files: ヒットリストファイルのリスト
        input_cds: 入力CDSファイル（Nohit_cds.fa）
        output_list: 出力リストファイル
        output_cds: 出力CDSファイル
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
        dict: make_complete_list設定
    """
    if 'make_complete_list' not in config:
        print("エラー: 設定ファイルに 'make_complete_list' セクションがありません。", file=sys.stderr)
        sys.exit(1)

    complete_config = config['make_complete_list']

    # 必須パラメータのチェック
    required_params = ['hit_files', 'input_cds', 'output_list', 'output_cds']
    for param in required_params:
        if param not in complete_config:
            print(f"エラー: 必須パラメータ '{param}' が設定ファイルにありません。", file=sys.stderr)
            sys.exit(1)

    # hit_filesがリストであることをチェック
    if not isinstance(complete_config['hit_files'], list):
        print("エラー: 'hit_files' はリスト形式で指定してください。", file=sys.stderr)
        sys.exit(1)

    # 入力CDSファイルの存在チェック
    if not os.path.exists(complete_config['input_cds']):
        print(f"エラー: 入力CDSファイル '{complete_config['input_cds']}' が見つかりません。", file=sys.stderr)
        sys.exit(1)

    return complete_config


def collect_hit_ids(hit_files):
    """
    複数のヒットリストファイルからヒットしたIDを収集する

    Args:
        hit_files (list): ヒットリストファイルのリスト

    Returns:
        set: ヒットしたIDのセット
    """
    hit_ids = set()

    for hit_file in hit_files:
        if not os.path.exists(hit_file):
            print(f"警告: ヒットファイル '{hit_file}' が見つかりません。スキップします。")
            continue

        try:
            with open(hit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        dat = line.split("\t")
                        if dat:
                            hit_ids.add(dat[0])
            print(f"読み込み: {hit_file} ({len(hit_ids)} IDs累計)")
        except Exception as e:
            print(f"警告: ファイル '{hit_file}' の読み込み中にエラー: {e}")

    return hit_ids


def extract_non_hit_sequences(input_cds, hit_ids, output_list, output_cds):
    """
    ヒットしなかった配列を抽出して出力する

    Args:
        input_cds (str): 入力CDSファイルパス
        hit_ids (set): ヒットしたIDのセット
        output_list (str): 出力リストファイルパス
        output_cds (str): 出力CDSファイルパス

    Returns:
        int: 抽出した配列数
    """
    extracted_count = 0
    current_id = None
    output_flag = False

    try:
        with open(input_cds, 'r', encoding='utf-8') as infile:
            with open(output_list, 'w', encoding='utf-8') as out_list:
                with open(output_cds, 'w', encoding='utf-8') as out_cds:
                    for line in infile:
                        line = line.rstrip('\n')

                        # ヘッダー行の処理
                        match = re.match(r'>(\S+)', line)
                        if match:
                            current_id = match.group(1)
                            if current_id not in hit_ids:
                                output_flag = True
                                out_cds.write(line + '\n')
                                out_list.write(current_id + '\n')
                                extracted_count += 1
                            else:
                                output_flag = False
                        elif output_flag:
                            # 配列行の処理
                            out_cds.write(line + '\n')

        return extracted_count

    except Exception as e:
        print(f"エラー: ファイル処理中にエラーが発生しました: {e}", file=sys.stderr)
        return -1


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='GMAPヒットリストから最終ターゲットリストを作成する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 make_complete_list.py config.yaml
    python3 make_complete_list.py ../config.yaml

設定ファイルの例:
    make_complete_list:
        hit_files:
            - "SpeciesB_hit.tab"
            - "SpeciesC_hit.tab"
        input_cds: "../BLASTP/Nohit_cds.fa"
        output_list: "Target.list"
        output_cds: "Target_cds.fa"
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
    complete_config = validate_config(config)

    print("=" * 60)
    print("GMAPヒットリストから最終ターゲットリストを作成")
    print("=" * 60)

    # ヒットしたIDを収集
    print("\n[1] ヒットリストファイルの読み込み")
    print("-" * 40)
    hit_ids = collect_hit_ids(complete_config['hit_files'])
    print(f"合計ヒットID数: {len(hit_ids)}")

    # ヒットしなかった配列を抽出
    print("\n[2] ヒットしなかった配列の抽出")
    print("-" * 40)
    print(f"入力ファイル: {complete_config['input_cds']}")
    print(f"出力リスト: {complete_config['output_list']}")
    print(f"出力CDS: {complete_config['output_cds']}")

    extracted_count = extract_non_hit_sequences(
        complete_config['input_cds'],
        hit_ids,
        complete_config['output_list'],
        complete_config['output_cds']
    )

    if extracted_count >= 0:
        print(f"\n抽出した配列数: {extracted_count}")
        print("=" * 60)
        print("処理が完了しました。")
    else:
        print("処理に失敗しました。", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
