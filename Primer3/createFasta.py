#!/usr/bin/env python3
"""
Primer3出力からFASTAファイルを作成するスクリプト

使用方法:
    python3 createFasta.py config.yaml

設定ファイルのcreate_fastaセクションから設定を読み込み、
Primer3の出力ファイルからプライマー配列をFASTA形式で出力します。
"""

import re
import sys
import os
import yaml


def load_config(config_path: str) -> dict:
    """設定ファイルを読み込む"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_fasta(config: dict) -> None:
    """Primer3出力からFASTAファイルを作成する"""
    fasta_config = config.get('create_fasta', {})

    # 設定値の取得
    input_file = fasta_config.get('input_file', 'primer3_output.list')
    output_file = fasta_config.get('output_file', 'primer3.fa')

    # 入力ファイルの存在確認
    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイルが見つかりません: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"入力ファイル: {input_file}")
    print(f"出力ファイル: {output_file}")

    # プライマー配列のパターン
    left_pattern = re.compile(r'^(PRIMER_LEFT_\d+_SEQUENCE)=(\w+)$')
    right_pattern = re.compile(r'^(PRIMER_RIGHT_\d+_SEQUENCE)=(\w+)$')
    seq_id_pattern = re.compile(r'^SEQUENCE_ID=(.+)$')

    seq_id = None

    with open(input_file, 'r', encoding='utf-8') as fin:
        with open(output_file, 'w', encoding='utf-8') as fout:
            for line in fin:
                line = line.rstrip('\n')

                # SEQUENCE_IDの取得
                match = seq_id_pattern.match(line)
                if match:
                    seq_id = match.group(1)
                    continue

                # PRIMER_LEFT_*_SEQUENCEのマッチ
                match = left_pattern.match(line)
                if match:
                    primer_name = match.group(1)
                    sequence = match.group(2)
                    seq_len = len(sequence)
                    fout.write(f">{seq_id}::{primer_name}::{seq_len}\n")
                    fout.write(f"{sequence}\n")
                    continue

                # PRIMER_RIGHT_*_SEQUENCEのマッチ
                match = right_pattern.match(line)
                if match:
                    primer_name = match.group(1)
                    sequence = match.group(2)
                    seq_len = len(sequence)
                    fout.write(f">{seq_id}::{primer_name}::{seq_len}\n")
                    fout.write(f"{sequence}\n")
                    continue

    print(f"完了: {output_file} を作成しました")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 createFasta.py <config.yaml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"エラー: 設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    create_fasta(config)


if __name__ == '__main__':
    main()
