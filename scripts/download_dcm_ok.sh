#!/bin/bash

# This script get the datasets require to train the model from:
#   https://github.com/OpenNeuroDatasets/ds005616.git
#   https://github.com/spine-generic/data-multi-subject

# BASH SETTINGS
# ======================================================================================================================

# Uncomment for full verbose
# set -v

# Immediately exit if error
set -e

# Exit if user presses CTRL+C (Linux) or CMD+C (OSX)
trap "echo Caught Keyboard Interrupt within script. Exiting now.; exit" INT

# SCRIPT STARTS HERE
# ======================================================================================================================

# Set CANALSEG and CANALSEG_DATA if not set
CANALSEG="$(realpath "${CANALSEG:-model-canal-seg}")"
CANALSEG_DATA="$(realpath "${CANALSEG_DATA:-data}")"

# Fetch path to data list
data_json="$CANALSEG_DATA/dcm_ok_vert.json"
# Set the paths to the BIDS data folders
bids="$CANALSEG_DATA/dcm-oklahoma"

# Make sure $CANALSEG_DATA/bids exists and enter it
mkdir -p "$bids"
CURR_DIR="$(realpath .)"
cd "$bids"

datasets=(
    git@data.neuro.polymtl.ca:datasets/whole-spine.git
    https://github.com/spine-generic/data-multi-subject.git
    git@data.neuro.polymtl.ca:datasets/dcm-zurich.git
)

sources=(
    data.neuro
    data.neuro
    OpenNeuro
)

#commits=(
#    1.1.2
#    ba0131b7599a644c3488890e35b37cfc38ba5791
#)




keys=(
    IMAGE
    LABEL
)

# Download necessary data from git annex
for key in "${keys[@]}"; do
    for path in $(jq -r --arg k "$key" '.TRAINING[][$k]' "$data_json"); do
        echo "Getting $path"
        IFS='/' read -r rep_path rel_path <<< "$path"
        git -C "$rep_path" annex get "$rel_path"
    done
done

for key in "${keys[@]}"; do
    for path in $(jq -r --arg k "$key" '.TESTING[][$k]' "$data_json"); do
        echo "Getting $path"
        IFS='/' read -r rep_path rel_path <<< "$path"
        git -C "$rep_path" annex get "$rel_path"
    done
done

# Return to the original working directory
cd "$CURR_DIR"
