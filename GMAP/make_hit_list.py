#!/usr/bin/env python3
"""
GFF3ファイルからヒットリストを作成するスクリプト

使用方法:
    python3 make_hit_list.py config.yaml

設定ファイル（YAML形式）からパラメータを読み込み、
GFF3ファイルからcoverage/identityを抽出してヒットリストを作成します。

必要な設定項目:
    make_hit_list:
        targets:
            - prefix: GFF3ファイルのプレフィックス
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
        dict: make_hit_list設定
    """
    if 'make_hit_list' not in config:
        print("エラー: 設定ファイルに 'make_hit_list' セクションがありません。", file=sys.stderr)
        sys.exit(1)

    hit_config = config['make_hit_list']

    if 'targets' not in hit_config:
        print("エラー: 'targets' が設定ファイルにありません。", file=sys.stderr)
        sys.exit(1)

    if not isinstance(hit_config['targets'], list):
        print("エラー: 'targets' はリスト形式で指定してください。", file=sys.stderr)
        sys.exit(1)

    if len(hit_config['targets']) == 0:
        print("エラー: 'targets' に少なくとも1つの対象を指定してください。", file=sys.stderr)
        sys.exit(1)

    # 各ターゲットの検証
    for i, target in enumerate(hit_config['targets']):
        if 'prefix' not in target:
            print(f"エラー: targets[{i}] に 'prefix' がありません。", file=sys.stderr)
            sys.exit(1)

    return hit_config


def process_gff3(prefix):
    """
    GFF3ファイルを処理してヒットリストを作成する

    Args:
        prefix (str): GFF3ファイルのプレフィックス

    Returns:
        int: 抽出したヒット数
    """
    input_file = f"{prefix}.gff3"
    output_file = f"{prefix}_hit.tab"

    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイル '{input_file}' が見つかりません。", file=sys.stderr)
        return -1

    hit_count = 0

    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for line in infile:
                    line = line.strip()
                    dat = line.split("\t")

                    if len(dat) < 3:
                        continue

                    if "mRNA" in dat[2]:
                        m = re.search(r"ID=([a-zA-Z_.0-9]+)\.mrna", line)
                        if m:
                            gene_id = m.group(1)
                            m2 = re.search(r"coverage=([0-9.]+);identity=([0-9.]+)", line)
                            if m2:
                                coverage = m2.group(1)
                                identity = m2.group(2)
                                outfile.write(f"{gene_id}\t{coverage}\t{identity}\n")
                                hit_count += 1

        return hit_count

    except Exception as e:
        print(f"エラー: ファイル処理中にエラーが発生しました: {e}", file=sys.stderr)
        return -1


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='GFF3ファイルからヒットリストを作成する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python3 make_hit_list.py config.yaml
    python3 make_hit_list.py ../config.yaml

設定ファイルの例:
    make_hit_list:
        targets:
            - prefix: "SpeciesB"
            - prefix: "SpeciesC"
        """
    )

    parser.add_argument(
        'config_file',
        help='YAML形式の設定ファイルパス'
    )

    parser.add_argument(
        '--prefix', '-p',
        help='特定のプレフィックスのみ処理する'
    )

    args = parser.parse_args()

    # 設定ファイルの読み込み
    config = load_config(args.config_file)

    # 設定の妥当性チェック
    hit_config = validate_config(config)

    # 処理対象を決定
    targets = hit_config['targets']
    if args.prefix:
        targets = [t for t in targets if t['prefix'] == args.prefix]
        if not targets:
            print(f"エラー: プレフィックス '{args.prefix}' が設定ファイルに見つかりません。", file=sys.stderr)
            sys.exit(1)

    # 処理実行
    print(f"処理対象数: {len(targets)}")
    print("=" * 60)

    total_hits = 0
    for i, target in enumerate(targets):
        prefix = target['prefix']
        print(f"\n[{i+1}/{len(targets)}] 処理中: {prefix}")
        print("-" * 40)
        print(f"入力ファイル: {prefix}.gff3")
        print(f"出力ファイル: {prefix}_hit.tab")

        hit_count = process_gff3(prefix)

        if hit_count >= 0:
            print(f"抽出したヒット数: {hit_count}")
            total_hits += hit_count
        else:
            print("処理に失敗しました。")

    print()
    print("=" * 60)
    print(f"すべての処理が完了しました。合計ヒット数: {total_hits}")


if __name__ == '__main__':
    main()
