#!/bin/bash

# パイプライン全体を実行するスクリプト
# 使用方法: ./run_pipeline.sh <config_file> [--start-step <step>] [--end-step <step>]
# 例: ./run_pipeline.sh config.yaml
#     ./run_pipeline.sh config.yaml --start-step 5
#     ./run_pipeline.sh config.yaml --start-step gmap_hit --end-step primer3_run

set -e  # エラー時に停止

#-----------------------------------------------------------
# ステータス管理用ディレクトリ
#-----------------------------------------------------------
STATUS_DIR=".pipeline_status"

#-----------------------------------------------------------
# ステップ名の定義
#-----------------------------------------------------------
STEP_NAMES=(
    "translation"      # 0: Materials - 翻訳処理
    "blastp_db"        # 1: BLASTP - DB構築
    "blastp_run"       # 2: BLASTP - 実行
    "blastp_nohit"     # 3: BLASTP - ノーヒット抽出
    "blastp_extract"   # 4: BLASTP - ノーヒットCDS抽出
    "gmap_db"          # 5: GMAP - DB構築
    "gmap_run"         # 6: GMAP - GMAP実行（GFF3生成）
    "gmap_hit"         # 7: GMAP - ヒットリスト作成
    "gmap_complete"    # 8: GMAP - 完全リスト作成
    "primer3_input"    # 9: Primer3 - 入力ファイル生成
    "primer3_run"      # 10: Primer3 - 実行
    "primer3_fasta"    # 11: Primer3 - FASTA作成
    "blastn_db"        # 12: Primer3 - BLASTN DB構築
    "blastn_run"       # 13: Primer3 - BLASTN実行
    "primer3_extract"  # 14: Primer3 - ヒット領域抽出
    "primer3_list"     # 15: Primer3 - プライマーリスト作成
)

MAX_STEP=$((${#STEP_NAMES[@]} - 1))

#-----------------------------------------------------------
# ヘルプ表示関数
#-----------------------------------------------------------
show_help() {
    echo "使用方法: $0 <config_file> [--start-step <step>] [--end-step <step>] [options]"
    echo ""
    echo "オプション:"
    echo "  --start-step <step>  開始ステップを指定（番号または名前）"
    echo "  --end-step <step>    終了ステップを指定（番号または名前）"
    echo "  --force              完了済みステップも確認なしで再実行"
    echo "  --skip-completed     完了済みステップを確認なしでスキップ"
    echo "  --check-only         スクリプトと外部ツールの存在確認のみ行う"
    echo "  --clean-status       ステータスファイルをクリアして終了"
    echo "  --show-status        各ステップの完了状況を表示して終了"
    echo "  --help               このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 config.yaml                              # 全ステップ実行"
    echo "  $0 config.yaml --start-step 5              # Step 5から最後まで"
    echo "  $0 config.yaml --start-step gmap_hit       # gmap_hitから最後まで"
    echo "  $0 config.yaml --start-step 3 --end-step 6 # Step 3〜6のみ"
    echo "  $0 config.yaml --skip-completed            # 完了済みを自動スキップ"
    echo "  $0 config.yaml --force                     # 全て再実行"
    echo "  $0 config.yaml --check-only               # 環境チェックのみ"
    echo "  $0 --clean-status                          # ステータスをクリア"
    echo ""
    echo "利用可能なステップ:"
    for i in "${!STEP_NAMES[@]}"; do
        printf "  %2d: %s\n" "$i" "${STEP_NAMES[$i]}"
    done
    exit 0
}

#-----------------------------------------------------------
# ステータス管理関数
#-----------------------------------------------------------
# マーカーファイルのパスを取得
get_marker_file() {
    local step_num=$1
    echo "${STATUS_DIR}/step_${step_num}_${STEP_NAMES[$step_num]}.complete"
}

# ステップが完了済みかチェック
is_step_completed() {
    local step_num=$1
    local marker_file
    marker_file=$(get_marker_file "$step_num")
    [ -f "$marker_file" ]
}

# ステップを完了済みとしてマーク
mark_step_completed() {
    local step_num=$1
    local marker_file
    marker_file=$(get_marker_file "$step_num")
    mkdir -p "$STATUS_DIR"
    date "+%Y-%m-%d %H:%M:%S" > "$marker_file"
}

# ステータスディレクトリをクリア
clean_status() {
    if [ -d "$STATUS_DIR" ]; then
        rm -rf "$STATUS_DIR"
        echo "ステータスファイルをクリアしました"
    else
        echo "ステータスファイルは存在しません"
    fi
    exit 0
}

# 各ステップの完了状況を表示
show_status() {
    echo "パイプラインステータス:"
    echo "------------------------------------------------------------"
    for i in "${!STEP_NAMES[@]}"; do
        local marker_file
        marker_file=$(get_marker_file "$i")
        if [ -f "$marker_file" ]; then
            local completed_at
            completed_at=$(cat "$marker_file")
            printf "  [完了] %2d: %-20s (%s)\n" "$i" "${STEP_NAMES[$i]}" "$completed_at"
        else
            printf "  [未完] %2d: %s\n" "$i" "${STEP_NAMES[$i]}"
        fi
    done
    exit 0
}

# 完了済みステップの実行確認（ユーザーに問い合わせ）
# 戻り値: 0=スキップ, 1=実行
check_and_ask_skip() {
    local step_num=$1

    # 完了済みでなければ実行
    if ! is_step_completed "$step_num"; then
        return 1
    fi

    # --force モードなら再実行
    if [ "$FORCE_MODE" = true ]; then
        return 1
    fi

    # --skip-completed モードならスキップ
    if [ "$SKIP_COMPLETED_MODE" = true ]; then
        echo "  → 完了済みのためスキップします"
        return 0
    fi

    # ユーザーに確認
    local marker_file
    marker_file=$(get_marker_file "$step_num")
    local completed_at
    completed_at=$(cat "$marker_file")

    echo "  このステップは既に完了しています (完了日時: $completed_at)"
    read -p "  スキップしますか？ [Y/n]: " answer
    case "$answer" in
        [Nn]*) return 1 ;;  # 再実行
        *)     return 0 ;;  # スキップ
    esac
}

#-----------------------------------------------------------
# ステップ名を番号に変換する関数
#-----------------------------------------------------------
step_to_number() {
    local step=$1
    # 数字の場合はそのまま返す
    if [[ "$step" =~ ^[0-9]+$ ]]; then
        if [ "$step" -ge 0 ] && [ "$step" -le "$MAX_STEP" ]; then
            echo "$step"
            return 0
        else
            echo "エラー: ステップ番号 '$step' は範囲外です (0-$MAX_STEP)" >&2
            return 1
        fi
    fi
    # 名前の場合は対応する番号を探す
    for i in "${!STEP_NAMES[@]}"; do
        if [ "${STEP_NAMES[$i]}" = "$step" ]; then
            echo "$i"
            return 0
        fi
    done
    echo "エラー: 不明なステップ名 '$step'" >&2
    echo "利用可能なステップ: ${STEP_NAMES[*]}" >&2
    return 1
}

#-----------------------------------------------------------
# 引数パース
#-----------------------------------------------------------
CONFIG_FILE=""
START_STEP=0
END_STEP=$MAX_STEP
FORCE_MODE=false
SKIP_COMPLETED_MODE=false
CHECK_ONLY_MODE=false

while [ $# -gt 0 ]; do
    case "$1" in
        --help|-h)
            show_help
            ;;
        --clean-status)
            clean_status
            ;;
        --show-status)
            show_status
            ;;
        --force)
            FORCE_MODE=true
            shift
            ;;
        --skip-completed)
            SKIP_COMPLETED_MODE=true
            shift
            ;;
        --check-only)
            CHECK_ONLY_MODE=true
            shift
            ;;
        --start-step)
            if [ -z "$2" ]; then
                echo "エラー: --start-step には値が必要です" >&2
                exit 1
            fi
            START_STEP=$(step_to_number "$2") || exit 1
            shift 2
            ;;
        --end-step)
            if [ -z "$2" ]; then
                echo "エラー: --end-step には値が必要です" >&2
                exit 1
            fi
            END_STEP=$(step_to_number "$2") || exit 1
            shift 2
            ;;
        -*)
            echo "エラー: 不明なオプション '$1'" >&2
            echo "ヘルプを表示するには: $0 --help" >&2
            exit 1
            ;;
        *)
            if [ -z "$CONFIG_FILE" ]; then
                CONFIG_FILE=$1
            else
                echo "エラー: 設定ファイルは1つだけ指定してください" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# --force と --skip-completed は同時に指定できない
if [ "$FORCE_MODE" = true ] && [ "$SKIP_COMPLETED_MODE" = true ]; then
    echo "エラー: --force と --skip-completed は同時に指定できません" >&2
    exit 1
fi

# 設定ファイルの指定確認
if [ -z "$CONFIG_FILE" ]; then
    echo "エラー: 設定ファイルが指定されていません" >&2
    echo "使用方法: $0 <config_file> [--start-step <step>] [--end-step <step>]" >&2
    exit 1
fi

# 範囲の妥当性チェック
if [ "$START_STEP" -gt "$END_STEP" ]; then
    echo "エラー: 開始ステップ ($START_STEP) は終了ステップ ($END_STEP) 以下である必要があります" >&2
    exit 1
fi

#-----------------------------------------------------------
# ステップ実行判定関数
#-----------------------------------------------------------
should_run_step() {
    local step_num=$1
    [ "$step_num" -ge "$START_STEP" ] && [ "$step_num" -le "$END_STEP" ]
}

# 設定ファイルの存在確認
if [ ! -f "$CONFIG_FILE" ]; then
    echo "エラー: 設定ファイル '$CONFIG_FILE' が見つかりません"
    exit 1
fi

# 開始時刻
PIPELINE_START_TIME=$(date +%s)
echo "============================================================"
echo "パイプライン開始: $(date)"
echo "設定ファイル: $CONFIG_FILE"
if [ "$START_STEP" -eq 0 ] && [ "$END_STEP" -eq "$MAX_STEP" ]; then
    echo "実行ステップ: 全ステップ (0-$MAX_STEP)"
else
    echo "実行ステップ: $START_STEP (${STEP_NAMES[$START_STEP]}) 〜 $END_STEP (${STEP_NAMES[$END_STEP]})"
fi
echo "============================================================"

# ベースディレクトリ（スクリプトの場所）
BASE_DIR=$(dirname "$(readlink -f "$0")")
cd "$BASE_DIR"

#-----------------------------------------------------------
# 必要なスクリプトファイルの存在確認
#-----------------------------------------------------------
REQUIRED_SCRIPTS=(
    "Materials/step0_translation.py"
    "BLASTP/build_blastp_db.py"
    "BLASTP/run_blastp.py"
    "BLASTP/pick_nohit_genes.py"
    "BLASTP/extract_nohit.fa.py"
    "GMAP/build_gmap_db.py"
    "GMAP/run_gmap.py"
    "GMAP/make_hit_list.py"
    "GMAP/make_complete_list.py"
    "Primer3/make_primer3_input.py"
    "Primer3/run_primer3.py"
    "Primer3/createFasta.py"
    "Primer3/build_blastn_db.py"
    "Primer3/run_blastn_short.py"
    "Primer3/run_extract_hit_regions.py"
    "Primer3/run_make_primer_list.py"
)

MISSING_SCRIPTS=()
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ ! -f "$BASE_DIR/$script" ]; then
        MISSING_SCRIPTS+=("$script")
    fi
done

if [ ${#MISSING_SCRIPTS[@]} -ne 0 ]; then
    echo "エラー: 以下の必要なスクリプトが見つかりません:"
    for missing in "${MISSING_SCRIPTS[@]}"; do
        echo "  - $missing"
    done
    exit 1
fi

echo "全ての必要なスクリプトを確認しました"

# 設定ファイルへの相対パスを計算
CONFIG_PATH=$(realpath "$CONFIG_FILE")

#-----------------------------------------------------------
# 外部ツールの存在確認
# PATHに存在するか、または設定ファイルで指定されたパスを確認
#-----------------------------------------------------------

# 設定ファイルからexecutables.<key>の値を取得する関数
get_config_executable() {
    local key=$1
    local value
    # executables:セクション内の指定キーの値を取得
    value=$(sed -n '/^executables:/,/^[^ ]/p' "$CONFIG_PATH" | grep "^  ${key}:" | sed 's/^[^:]*: *"\{0,1\}\([^"#]*\)"\{0,1\}.*/\1/' | tr -d ' ')
    echo "$value"
}

# 実行ファイルが利用可能かチェックする関数
# 戻り値: 0=利用可能、1=利用不可
check_executable() {
    local name=$1
    local config_path

    # まずPATHから探す
    if command -v "$name" >/dev/null 2>&1; then
        return 0
    fi

    # PATHになければ設定ファイルを確認
    config_path=$(get_config_executable "$name")
    if [ -n "$config_path" ] && [ "$config_path" != "$name" ]; then
        # 設定ファイルで指定されたパスが実行可能か確認
        if command -v "$config_path" >/dev/null 2>&1; then
            return 0
        elif [ -x "$config_path" ]; then
            return 0
        fi
    fi

    return 1
}

# 必要な外部ツールのリスト
REQUIRED_EXECUTABLES=(
    "makeblastdb"
    "blastp"
    "blastn"
    "gmap_build"
    "gmap"
    "primer3_core"
)

MISSING_EXECUTABLES=()
for exe in "${REQUIRED_EXECUTABLES[@]}"; do
    if ! check_executable "$exe"; then
        config_path=$(get_config_executable "$exe")
        if [ -n "$config_path" ] && [ "$config_path" != "$exe" ]; then
            MISSING_EXECUTABLES+=("$exe (設定ファイルで指定: $config_path)")
        else
            MISSING_EXECUTABLES+=("$exe (PATHに存在せず、設定ファイルでも未指定)")
        fi
    fi
done

if [ ${#MISSING_EXECUTABLES[@]} -ne 0 ]; then
    echo "エラー: 以下の外部ツールが見つかりません:"
    for missing in "${MISSING_EXECUTABLES[@]}"; do
        echo "  - $missing"
    done
    echo ""
    echo "対処方法:"
    echo "  1. ツールをインストールしてPATHを通す"
    echo "  2. または設定ファイルのexecutables:セクションでパスを指定する"
    exit 1
fi

echo "全ての外部ツールを確認しました"

#-----------------------------------------------------------
# --check-only モードの場合はここで終了
#-----------------------------------------------------------
if [ "$CHECK_ONLY_MODE" = true ]; then
    echo ""
    echo "============================================================"
    echo "環境チェック完了: 全てのチェックに合格しました"
    echo "============================================================"
    exit 0
fi

#-----------------------------------------------------------
# Step 0: Materials - 翻訳処理
#-----------------------------------------------------------
if should_run_step 0; then
    echo ""
    echo "[Step 0] Materials: step0_translation.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 0; then
        cd "$BASE_DIR/Materials"
        python3 step0_translation.py "$CONFIG_PATH"
        mark_step_completed 0
    fi
fi

#-----------------------------------------------------------
# Step 1: BLASTP - データベース構築
#-----------------------------------------------------------
if should_run_step 1; then
    echo ""
    echo "[Step 1] BLASTP: build_blastp_db.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 1; then
        cd "$BASE_DIR/BLASTP"
        python3 build_blastp_db.py "$CONFIG_PATH"
        mark_step_completed 1
    fi
fi

#-----------------------------------------------------------
# Step 2: BLASTP - BLASTP実行
#-----------------------------------------------------------
if should_run_step 2; then
    echo ""
    echo "[Step 2] BLASTP: run_blastp.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 2; then
        cd "$BASE_DIR/BLASTP"
        python3 run_blastp.py "$CONFIG_PATH"
        mark_step_completed 2
    fi
fi

#-----------------------------------------------------------
# Step 3: BLASTP - ヒットしない遺伝子の抽出
#-----------------------------------------------------------
if should_run_step 3; then
    echo ""
    echo "[Step 3] BLASTP: pick_nohit_genes.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 3; then
        cd "$BASE_DIR/BLASTP"
        python3 pick_nohit_genes.py "$CONFIG_PATH"
        mark_step_completed 3
    fi
fi

#-----------------------------------------------------------
# Step 4: BLASTP - ノーヒットCDS抽出
#-----------------------------------------------------------
if should_run_step 4; then
    echo ""
    echo "[Step 4] BLASTP: extract_nohit.fa.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 4; then
        cd "$BASE_DIR/BLASTP"
        python3 extract_nohit.fa.py "$CONFIG_PATH"
        mark_step_completed 4
    fi
fi

#-----------------------------------------------------------
# Step 5: GMAP - データベース構築
#-----------------------------------------------------------
if should_run_step 5; then
    echo ""
    echo "[Step 5] GMAP: build_gmap_db.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 5; then
        cd "$BASE_DIR/GMAP"
        python3 build_gmap_db.py "$CONFIG_PATH"
        mark_step_completed 5
    fi
fi

#-----------------------------------------------------------
# Step 6: GMAP - GMAP実行（GFF3生成）
#-----------------------------------------------------------
if should_run_step 6; then
    echo ""
    echo "[Step 6] GMAP: run_gmap.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 6; then
        cd "$BASE_DIR/GMAP"
        python3 run_gmap.py "$CONFIG_PATH"
        mark_step_completed 6
    fi
fi

#-----------------------------------------------------------
# Step 7: GMAP - ヒットリスト作成
#-----------------------------------------------------------
if should_run_step 7; then
    echo ""
    echo "[Step 7] GMAP: make_hit_list.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 7; then
        cd "$BASE_DIR/GMAP"
        python3 make_hit_list.py "$CONFIG_PATH"
        mark_step_completed 7
    fi
fi

#-----------------------------------------------------------
# Step 8: GMAP - 完全リスト作成
#-----------------------------------------------------------
if should_run_step 8; then
    echo ""
    echo "[Step 8] GMAP: make_complete_list.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 8; then
        cd "$BASE_DIR/GMAP"
        python3 make_complete_list.py "$CONFIG_PATH"
        mark_step_completed 8
    fi
fi

#-----------------------------------------------------------
# Step 9: Primer3 - 入力ファイル生成
#-----------------------------------------------------------
if should_run_step 9; then
    echo ""
    echo "[Step 9] Primer3: make_primer3_input.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 9; then
        cd "$BASE_DIR/Primer3"
        python3 make_primer3_input.py "$CONFIG_PATH"
        mark_step_completed 9
    fi
fi

#-----------------------------------------------------------
# Step 10: Primer3 - Primer3実行
#-----------------------------------------------------------
if should_run_step 10; then
    echo ""
    echo "[Step 10] Primer3: run_primer3.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 10; then
        cd "$BASE_DIR/Primer3"
        python3 run_primer3.py "$CONFIG_PATH"
        mark_step_completed 10
    fi
fi

#-----------------------------------------------------------
# Step 11: Primer3 - FASTA作成
#-----------------------------------------------------------
if should_run_step 11; then
    echo ""
    echo "[Step 11] Primer3: createFasta.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 11; then
        cd "$BASE_DIR/Primer3"
        python3 createFasta.py "$CONFIG_PATH"
        mark_step_completed 11
    fi
fi

#-----------------------------------------------------------
# Step 12: Primer3 - BLASTN データベース構築
#-----------------------------------------------------------
if should_run_step 12; then
    echo ""
    echo "[Step 12] Primer3: build_blastn_db.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 12; then
        cd "$BASE_DIR/Primer3"
        python3 build_blastn_db.py "$CONFIG_PATH"
        mark_step_completed 12
    fi
fi

#-----------------------------------------------------------
# Step 13: Primer3 - BLASTN-short実行
#-----------------------------------------------------------
if should_run_step 13; then
    echo ""
    echo "[Step 13] Primer3: run_blastn_short.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 13; then
        cd "$BASE_DIR/Primer3"
        python3 run_blastn_short.py "$CONFIG_PATH"
        mark_step_completed 13
    fi
fi

#-----------------------------------------------------------
# Step 14: Primer3 - ヒット領域抽出とペア作成
#-----------------------------------------------------------
if should_run_step 14; then
    echo ""
    echo "[Step 14] Primer3: run_extract_hit_regions.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 14; then
        cd "$BASE_DIR/Primer3"
        python3 run_extract_hit_regions.py "$CONFIG_PATH"
        mark_step_completed 14
    fi
fi

#-----------------------------------------------------------
# Step 15: Primer3 - プライマーリスト作成
#-----------------------------------------------------------
if should_run_step 15; then
    echo ""
    echo "[Step 15] Primer3: run_make_primer_list.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 15; then
        cd "$BASE_DIR/Primer3"
        python3 run_make_primer_list.py "$CONFIG_PATH"
        mark_step_completed 15
    fi
fi

#-----------------------------------------------------------
# 完了
#-----------------------------------------------------------
PIPELINE_END_TIME=$(date +%s)
ELAPSED=$((PIPELINE_END_TIME - PIPELINE_START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "============================================================"
echo "パイプライン完了: $(date)"
echo "総実行時間: ${HOURS}時間 ${MINUTES}分 ${SECONDS}秒"
echo "============================================================"
