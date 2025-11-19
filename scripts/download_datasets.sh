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
data_json="$CANALSEG/canalseg/resources/data/training_data.json"
# Set the paths to the BIDS data folders
bids="$CANALSEG_DATA"/bids

# Make sure $CANALSEG_DATA/bids exists and enter it
mkdir -p "$bids"
CURR_DIR="$(realpath .)"
cd "$bids"

datasets=(
    https://github.com/OpenNeuroDatasets/ds005616.git
    https://github.com/spine-generic/data-multi-subject.git
)

#commits=(
#    1.1.2
#    ba0131b7599a644c3488890e35b37cfc38ba5791
#)

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
    #git checkout "$commit"

    # Move back to the parent directory to process the next dataset
    cd ..
done

keys=(
    IMAGE
    LABEL_SPINE
    LABEL_CORD
    LABEL_CANAL
)

# Download necessary data from git annex
for key in "${keys[@]}"; do
    for path in $(jq -r ".TRAINING | .[].$key" "$data_json"); do
        IFS='/' read -r rep_path rel_path <<< "$path"
        git -C "$rep_path" annex get "$rel_path"
    done
done

for key in "${keys[@]}"; do
    for path in $(jq -r ".TESTING | .[].$key" "$data_json"); do
        IFS='/' read -r rep_path rel_path <<< "$path"
        git -C "$rep_path" annex get "$rel_path"
    done
done

# Return to the original working directory
cd "$CURR_DIR"
