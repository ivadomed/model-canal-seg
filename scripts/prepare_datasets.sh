#!/bin/bash

# This script prepares datasets for the TotalSpineSeg model in nnUNetv2 structure.
# The script execpt DATASET as the first positional argument to specify the dataset to prepare.
# It can be either 101, 102, 103 or all. If all is specified, it will prepare all datasets (101, 102, 103).
# By default, it will prepare datasets 101 and 102.
# The script also exepct -noaug parameter to not generate augmentations.

# The script excpects the following environment variables to be set:
#   TOTALSPINESEG: The path to the TotalSpineSeg repository.
#   TOTALSPINESEG_DATA: The path to the TotalSpineSeg data folder.
#   TOTALSPINESEG_JOBS: The number of CPU cores to use. Default is the number of CPU cores available.

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

# Set the path to the resources folder
RESSOURCES="$(realpath "${RESSOURCES:-ressources}")"

# Fetch path to data list
data_json="$RESSOURCES/canal.json"

# Get the number of CPUs
CORES=${SLURM_JOB_CPUS_PER_NODE:-$(lscpu -p | egrep -v '^#' | wc -l)}

# Set the number of jobs
JOBS=${CANALSEG_JOBS:-$CORES}

# Set nnunet params
nnUNet_raw="$CANALSEG_DATA"/nnUNet/raw

# Set the paths to the BIDS data folders
bids="$CANALSEG_DATA"/bids

SRC_DATASET=Dataset101_CanalSeg

### Prepare TRAIN set

echo "Make nnUNet raw folders"
mkdir -p "$nnUNet_raw"/$SRC_DATASET/imagesTr
mkdir -p "$nnUNet_raw"/$SRC_DATASET/labelsTr

# Move to bids directory
CURR_DIR="$(realpath .)"
cd "$bids"

# Copy images and labels and add nnUNet suffix _0000
echo "Copy images and labels with generated IDs"



i=0
for img in $(jq -r ".TRAINING | .[].IMAGE" "$data_json"); do
    base=$(basename "$img" .nii.gz)
    id=$(printf "%03d" $i)

    # Image filename: sub-name_0000.nii.gz → sub-name_000_0000.nii.gz
    img_name="${base}_${id}_0000.nii.gz"
    cp "$img" "$nnUNet_raw"/$SRC_DATASET/imagesTr/"$img_name"

    # Label filename: sub-name.nii.gz → sub-name_000.nii.gz
    label=$(jq -r ".TRAINING | .[] | select(.IMAGE==\"$img\") | .LABEL" "$data_json")
    label_name="${base}_${id}.nii.gz"
    cp "$label" "$nnUNet_raw"/$SRC_DATASET/labelsTr/"$label_name"

    i=$((i+1))
done

# Reorient images to canonical space
echo "Transform images to canonical space"
for f in "$nnUNet_raw"/$SRC_DATASET/imagesTr/*.nii.gz; do
    sct_image -i "$f" -setorient RAS -o "$f"
done

# Reorient labels to canonical space
echo "Transform labels to canonical space"
for f in "$nnUNet_raw"/$SRC_DATASET/labelsTr/*.nii.gz; do
    sct_image -i "$f" -setorient RAS -o "$f"
done

# Resample images to 1x1x1 mm
echo "Resample images to 1x1x1mm"
for f in "$nnUNet_raw"/$SRC_DATASET/imagesTr/*.nii.gz; do
    sct_resample -i "$f" -mm 1x1x1 -o "$f"
done

# Transform labels (nearest neighbor)
echo "Transform labels to image space"
for f in "$nnUNet_raw"/$SRC_DATASET/labelsTr/*.nii.gz; do
    sct_resample -i "$f" -mm 1x1x1 -x nn -o "$f"
done

### Prepare TEST set

echo "Creating test folders"
mkdir -p "$nnUNet_raw"/$SRC_DATASET/imagesTs
mkdir -p "$nnUNet_raw"/$SRC_DATASET/labelsTs

# Copy images and labels and add nnUNet suffix _0000
echo "Copy test images and labels with generated IDs"

i=0
for img in $(jq -r ".TESTING | .[].IMAGE" "$data_json"); do
    base=$(basename "$img" .nii.gz)
    id=$(printf "%03d" $i)

    # Image filename
    img_name="${base}_${id}_0000.nii.gz"
    cp "$img" "$nnUNet_raw"/$SRC_DATASET/imagesTs/"$img_name"

    # Label filename
    label=$(jq -r ".TESTING | .[] | select(.IMAGE==\"$img\") | .LABEL" "$data_json")
    label_name="${base}_${id}.nii.gz"
    cp "$label" "$nnUNet_raw"/$SRC_DATASET/labelsTs/"$label_name"

    i=$((i+1))
done


# Reorient images to canonical space
echo "Transform images to canonical space"
for f in "$nnUNet_raw"/$SRC_DATASET/imagesTs/*.nii.gz; do
    sct_image -i "$f" -setorient RAS -o "$f"
done

# Reorient labels to canonical space
echo "Transform labels to canonical space"
for f in "$nnUNet_raw"/$SRC_DATASET/labelsTs/*.nii.gz; do
    sct_image -i "$f" -setorient RAS -o "$f"
done

# Resample images to 1x1x1 mm
echo "Resample images to 1x1x1mm"
for f in "$nnUNet_raw"/$SRC_DATASET/imagesTs/*.nii.gz; do
    sct_resample -i "$f" -mm 1x1x1 -o "$f"
done

# Transform labels (nearest neighbor)
echo "Transform labels to image space"
for f in "$nnUNet_raw"/$SRC_DATASET/labelsTs/*.nii.gz; do
    sct_resample -i "$f" -mm 1x1x1 -x nn -o "$f"
done


# Move back
cd "$CURR_DIR"