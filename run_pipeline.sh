#!/bin/bash

# Script to execute the entire pipeline
# Usage: ./run_pipeline.sh <config_file> [--start-step <step>] [--end-step <step>]
# Example: ./run_pipeline.sh config.yaml
#          ./run_pipeline.sh config.yaml --start-step 5
#          ./run_pipeline.sh config.yaml --start-step gmap_hit --end-step primer3_run

set -e  # Stop on error

#-----------------------------------------------------------
# Directory for status management
#-----------------------------------------------------------
STATUS_DIR=".pipeline_status"

#-----------------------------------------------------------
# Step name definitions
#-----------------------------------------------------------
STEP_NAMES=(
    "translation"      # 0: Materials - Translation processing
    "blastp_db"        # 1: BLASTP - Build DB
    "blastp_run"       # 2: BLASTP - Run
    "blastp_nohit"     # 3: BLASTP - Extract no-hits
    "blastp_extract"   # 4: BLASTP - Extract no-hit CDS
    "gmap_db"          # 5: GMAP - Build DB
    "gmap_run"         # 6: GMAP - Run GMAP (generate GFF3)
    "gmap_hit"         # 7: GMAP - Create hit list
    "gmap_complete"    # 8: GMAP - Create complete list
    "primer3_input"    # 9: Primer3 - Generate input file
    "primer3_run"      # 10: Primer3 - Run
    "primer3_fasta"    # 11: Primer3 - Create FASTA
    "blastn_db"        # 12: Primer3 - Build BLASTN DB
    "blastn_run"       # 13: Primer3 - Run BLASTN
    "primer3_extract"  # 14: Primer3 - Extract hit regions
    "primer3_list"     # 15: Primer3 - Create primer list
    "primer3_annotate" # 16: Primer3 - Append original IDs
)

MAX_STEP=$((${#STEP_NAMES[@]} - 1))

#-----------------------------------------------------------
# Help display function
#-----------------------------------------------------------
show_help() {
    echo "Usage: $0 <config_file> [--start-step <step>] [--end-step <step>] [options]"
    echo ""
    echo "Options:"
    echo "  --start-step <step>  Specify start step (number or name)"
    echo "  --end-step <step>    Specify end step (number or name)"
    echo "  --force              Re-run completed steps without confirmation"
    echo "  --skip-completed     Skip completed steps without confirmation"
    echo "  --check-only         Only check for scripts and external tools"
    echo "  --clean-status       Clear status files in the current dir and exit"
    echo "  --reset              Reset all stages: remove */.pipeline_status/*.complete"
    echo "                       and *.version files recursively, then exit"
    echo "  --show-status        Show completion status of each step and exit"
    echo "  --help               Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 config.yaml                              # Run all steps"
    echo "  $0 config.yaml --start-step 5              # From Step 5 to the end"
    echo "  $0 config.yaml --start-step gmap_hit       # From gmap_hit to the end"
    echo "  $0 config.yaml --start-step 3 --end-step 6 # Steps 3 to 6 only"
    echo "  $0 config.yaml --skip-completed            # Auto-skip completed steps"
    echo "  $0 config.yaml --force                     # Re-run all steps"
    echo "  $0 config.yaml --check-only               # Environment check only"
    echo "  $0 --clean-status                          # Clear status (current dir only)"
    echo "  $0 --reset                                 # Reset all stages' status + version files"
    echo ""
    echo "Available steps:"
    for i in "${!STEP_NAMES[@]}"; do
        printf "  %2d: %s\n" "$i" "${STEP_NAMES[$i]}"
    done
    exit 0
}

#-----------------------------------------------------------
# Status management functions
#-----------------------------------------------------------
# Get marker file path
get_marker_file() {
    local step_num=$1
    echo "${STATUS_DIR}/step_${step_num}_${STEP_NAMES[$step_num]}.complete"
}

# Check if step is completed
is_step_completed() {
    local step_num=$1
    local marker_file
    marker_file=$(get_marker_file "$step_num")
    [ -f "$marker_file" ]
}

# Mark step as completed
mark_step_completed() {
    local step_num=$1
    local marker_file
    marker_file=$(get_marker_file "$step_num")
    mkdir -p "$STATUS_DIR"
    date "+%Y-%m-%d %H:%M:%S" > "$marker_file"
}

# Clear status directory
clean_status() {
    if [ -d "$STATUS_DIR" ]; then
        rm -rf "$STATUS_DIR"
        echo "Status files have been cleared"
    else
        echo "No status files exist"
    fi
    exit 0
}

# Reset pipeline execution state across all stages.
# Note: each stage keeps its own "$STATUS_DIR" under its own subdirectory
# (Materials/, BLASTP/, GMAP/, Primer3/, ...), so a recursive search from the
# script's base directory is required (the relative-path clean_status above
# only affects the invocation directory).
# Removes:
#   - step completion markers: */${STATUS_DIR}/*.complete (directories are kept)
#   - version marker files:    *.version
reset_status() {
    local base_dir
    base_dir=$(dirname "$(readlink -f "$0")")

    echo "Resetting pipeline status under: $base_dir"
    echo "------------------------------------------------------------"

    local complete_count version_count
    complete_count=$(find "$base_dir" -type f -name "*.complete" \
        -path "*/${STATUS_DIR}/*" -not -path "*/.git/*" | wc -l)
    version_count=$(find "$base_dir" -type f -name "*.version" \
        -not -path "*/.git/*" | wc -l)

    find "$base_dir" -type f -name "*.complete" \
        -path "*/${STATUS_DIR}/*" -not -path "*/.git/*" -print -delete
    find "$base_dir" -type f -name "*.version" \
        -not -path "*/.git/*" -print -delete

    echo "------------------------------------------------------------"
    echo "Removed ${complete_count} status marker(s) and ${version_count} version file(s)"
    echo "Reset complete"
    exit 0
}

# Show completion status of each step
show_status() {
    echo "Pipeline status:"
    echo "------------------------------------------------------------"
    for i in "${!STEP_NAMES[@]}"; do
        local marker_file
        marker_file=$(get_marker_file "$i")
        if [ -f "$marker_file" ]; then
            local completed_at
            completed_at=$(cat "$marker_file")
            printf "  [Done] %2d: %-20s (%s)\n" "$i" "${STEP_NAMES[$i]}" "$completed_at"
        else
            printf "  [Not done] %2d: %s\n" "$i" "${STEP_NAMES[$i]}"
        fi
    done
    exit 0
}

# Check whether to skip a completed step (prompt user)
# Return value: 0=skip, 1=run
check_and_ask_skip() {
    local step_num=$1

    # Run if not completed
    if ! is_step_completed "$step_num"; then
        return 1
    fi

    # Re-run in --force mode
    if [ "$FORCE_MODE" = true ]; then
        return 1
    fi

    # Skip in --skip-completed mode
    if [ "$SKIP_COMPLETED_MODE" = true ]; then
        echo "  -> Skipping because already completed"
        return 0
    fi

    # Ask user
    local marker_file
    marker_file=$(get_marker_file "$step_num")
    local completed_at
    completed_at=$(cat "$marker_file")

    echo "  This step has already been completed (completed at: $completed_at)"
    read -p "  Skip this step? [Y/n]: " answer
    case "$answer" in
        [Nn]*) return 1 ;;  # Re-run
        *)     return 0 ;;  # Skip
    esac
}

#-----------------------------------------------------------
# Function to convert step name to number
#-----------------------------------------------------------
step_to_number() {
    local step=$1
    # If numeric, return as-is
    if [[ "$step" =~ ^[0-9]+$ ]]; then
        if [ "$step" -ge 0 ] && [ "$step" -le "$MAX_STEP" ]; then
            echo "$step"
            return 0
        else
            echo "Error: Step number '$step' is out of range (0-$MAX_STEP)" >&2
            return 1
        fi
    fi
    # If name, find corresponding number
    for i in "${!STEP_NAMES[@]}"; do
        if [ "${STEP_NAMES[$i]}" = "$step" ]; then
            echo "$i"
            return 0
        fi
    done
    echo "Error: Unknown step name '$step'" >&2
    echo "Available steps: ${STEP_NAMES[*]}" >&2
    return 1
}

#-----------------------------------------------------------
# Argument parsing
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
        --reset)
            reset_status
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
                echo "Error: --start-step requires a value" >&2
                exit 1
            fi
            START_STEP=$(step_to_number "$2") || exit 1
            shift 2
            ;;
        --end-step)
            if [ -z "$2" ]; then
                echo "Error: --end-step requires a value" >&2
                exit 1
            fi
            END_STEP=$(step_to_number "$2") || exit 1
            shift 2
            ;;
        -*)
            echo "Error: Unknown option '$1'" >&2
            echo "For help, run: $0 --help" >&2
            exit 1
            ;;
        *)
            if [ -z "$CONFIG_FILE" ]; then
                CONFIG_FILE=$1
            else
                echo "Error: Please specify only one config file" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# --force and --skip-completed cannot be used together
if [ "$FORCE_MODE" = true ] && [ "$SKIP_COMPLETED_MODE" = true ]; then
    echo "Error: --force and --skip-completed cannot be used together" >&2
    exit 1
fi

# Check that config file is specified
if [ -z "$CONFIG_FILE" ]; then
    echo "Error: No config file specified" >&2
    echo "Usage: $0 <config_file> [--start-step <step>] [--end-step <step>]" >&2
    exit 1
fi

# Validate step range
if [ "$START_STEP" -gt "$END_STEP" ]; then
    echo "Error: Start step ($START_STEP) must be less than or equal to end step ($END_STEP)" >&2
    exit 1
fi

#-----------------------------------------------------------
# Step execution decision function
#-----------------------------------------------------------
should_run_step() {
    local step_num=$1
    [ "$step_num" -ge "$START_STEP" ] && [ "$step_num" -le "$END_STEP" ]
}

# Check that config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file '$CONFIG_FILE' not found"
    exit 1
fi

# Start time
PIPELINE_START_TIME=$(date +%s)
echo "============================================================"
echo "Pipeline started: $(date)"
echo "Config file: $CONFIG_FILE"
if [ "$START_STEP" -eq 0 ] && [ "$END_STEP" -eq "$MAX_STEP" ]; then
    echo "Steps to run: All steps (0-$MAX_STEP)"
else
    echo "Steps to run: $START_STEP (${STEP_NAMES[$START_STEP]}) to $END_STEP (${STEP_NAMES[$END_STEP]})"
fi
echo "============================================================"

# Base directory (location of the script)
BASE_DIR=$(dirname "$(readlink -f "$0")")
cd "$BASE_DIR"

#-----------------------------------------------------------
# Check that all required script files exist
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
    "Primer3/add_original_id.py"
)

MISSING_SCRIPTS=()
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ ! -f "$BASE_DIR/$script" ]; then
        MISSING_SCRIPTS+=("$script")
    fi
done

if [ ${#MISSING_SCRIPTS[@]} -ne 0 ]; then
    echo "Error: The following required scripts were not found:"
    for missing in "${MISSING_SCRIPTS[@]}"; do
        echo "  - $missing"
    done
    exit 1
fi

echo "All required scripts have been verified"

# Compute path to config file
CONFIG_PATH=$(realpath "$CONFIG_FILE")

#-----------------------------------------------------------
# Check for external tools
# Check if they exist in PATH or at paths specified in config file
#-----------------------------------------------------------

# Function to get executables.<key> value from config file
get_config_executable() {
    local key=$1
    local value
    # Get the value of the specified key within the executables: section
    value=$(sed -n '/^executables:/,/^[^ ]/p' "$CONFIG_PATH" | grep "^  ${key}:" | sed 's/^[^:]*: *"\{0,1\}\([^"#]*\)"\{0,1\}.*/\1/' | tr -d ' ')
    echo "$value"
}

# Function to check if an executable is available
# Return value: 0=available, 1=not available
check_executable() {
    local name=$1
    local config_path

    # First look in PATH
    if command -v "$name" >/dev/null 2>&1; then
        return 0
    fi

    # If not in PATH, check config file
    config_path=$(get_config_executable "$name")
    if [ -n "$config_path" ] && [ "$config_path" != "$name" ]; then
        # Check if the path specified in config is executable
        if command -v "$config_path" >/dev/null 2>&1; then
            return 0
        elif [ -x "$config_path" ]; then
            return 0
        fi
    fi

    return 1
}

# List of required external tools
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
            MISSING_EXECUTABLES+=("$exe (specified in config: $config_path)")
        else
            MISSING_EXECUTABLES+=("$exe (not found in PATH and not specified in config)")
        fi
    fi
done

if [ ${#MISSING_EXECUTABLES[@]} -ne 0 ]; then
    echo "Error: The following external tools were not found:"
    for missing in "${MISSING_EXECUTABLES[@]}"; do
        echo "  - $missing"
    done
    echo ""
    echo "Resolution:"
    echo "  1. Install the tools and add them to PATH"
    echo "  2. Or specify the paths in the executables: section of the config file"
    exit 1
fi

echo "All external tools have been verified"

#-----------------------------------------------------------
# Exit here if in --check-only mode
#-----------------------------------------------------------
if [ "$CHECK_ONLY_MODE" = true ]; then
    echo ""
    echo "============================================================"
    echo "Environment check complete: All checks passed"
    echo "============================================================"
    exit 0
fi

#-----------------------------------------------------------
# Step 0: Materials - Translation processing
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
# Step 1: BLASTP - Build database
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
# Step 2: BLASTP - Run BLASTP
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
# Step 3: BLASTP - Extract no-hit genes
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
# Step 4: BLASTP - Extract no-hit CDS
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
# Step 5: GMAP - Build database
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
# Step 6: GMAP - Run GMAP (generate GFF3)
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
# Step 7: GMAP - Create hit list
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
# Step 8: GMAP - Create complete list
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
# Step 9: Primer3 - Generate input file
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
# Step 10: Primer3 - Run Primer3
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
# Step 11: Primer3 - Create FASTA
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
# Step 12: Primer3 - Build BLASTN database
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
# Step 13: Primer3 - Run BLASTN-short
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
# Step 14: Primer3 - Extract hit regions and create pairs
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
# Step 15: Primer3 - Create primer list
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
# Step 16: Primer3 - Append original IDs to unique_primer3.tab
#-----------------------------------------------------------
if should_run_step 16; then
    echo ""
    echo "[Step 16] Primer3: add_original_id.py"
    echo "------------------------------------------------------------"
    if ! check_and_ask_skip 16; then
        cd "$BASE_DIR/Primer3"
        python3 add_original_id.py "$CONFIG_PATH"
        mark_step_completed 16
    fi
fi

#-----------------------------------------------------------
# Complete
#-----------------------------------------------------------
PIPELINE_END_TIME=$(date +%s)
ELAPSED=$((PIPELINE_END_TIME - PIPELINE_START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "============================================================"
echo "Pipeline completed: $(date)"
echo "Total execution time: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo "============================================================"
