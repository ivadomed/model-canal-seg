#!/bin/bash

# This script get the datasets required to train the model

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
data_json="$CANALSEG_DATA/canal.json"
# Set the paths to the BIDS data folders
bids="$CANALSEG_DATA"/bids

# Make sure $CANALSEG_DATA/bids exists and enter it
mkdir -p "$bids"
CURR_DIR="$(realpath .)"
cd "$bids"

datasets=(
    git@data.neuro.polymtl.ca:datasets/whole-spine.git
    https://github.com/spine-generic/data-multi-subject.git
    git@data.neuro.polymtl.ca:datasets/dcm-zurich.git
    git@data.neuro.polymtl.ca:datasets/spider-challenge-2023.git
)

commits=(
    0dc272e65dabfced28a0d1c93b389ef7c2b3d9dd
    ba0131b7599a644c3488890e35b37cfc38ba5791
    98d6f828748711fb1284ec50b6d65c8fcee185db
    d9be04cfb27da100fe03d968e220cccebbbc9a3f
)

# Clone datasets and checkout on the right branch
for i in "${!datasets[@]}"; do
    ds=${datasets[i]}
    commit=${commits[i]}
    dsn=$(basename $ds .git)

    # Clone the dataset from the specified repository
    git clone "$ds"

    # Enter the dataset directory
    cd "$dsn"

    ## Checkout on the commit
    git checkout "$commit"

    # Move back to the parent directory to process the next dataset
    cd ..
done

cd ..  # Move back to data directory
# Check if canal.json exists
if [[ -f canal.json ]]; then
    echo "canal.json found — skipping canal_seg generation."
else
    echo "canal.json not found — generating canal_seg.txt and running init_data_config.py"


    # Find canal segmentation labels (excluding MTS), sort them, save to text file
    find ~+ -type f -name "*_label-canal_seg.nii.gz" | grep -v "MTS" | sort > canal.txt

    # Run your data config script
    python "$CANALSEG/scripts/init_data_config.py" --txt canal.txt --type LABEL
fi

cd "$bids"

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
