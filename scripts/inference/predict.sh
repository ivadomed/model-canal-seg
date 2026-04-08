#!/bin/bash

# This script runs inference with the CanalSeg nnUNet model.
# It preprocesses input images to the required format, runs prediction,
# and resamples/reorients the output back to the native image space.
#
# Usage:
#   predict.sh <INPUT_IMAGE> [OUTPUT_LABEL] [FOLD]
#
# Arguments:
#   INPUT_IMAGE   Path to the input NIfTI image (.nii.gz)
#   OUTPUT_LABEL  Path for the output prediction (default: <input_basename>_label-canal_seg.nii.gz)
#   FOLD          nnUNet fold to use for inference (default: 0)
#
# Environment variables (optional overrides):
#   CANALSEG       Path to the model-canal-seg repository (default: model-canal-seg)
#   CANALSEG_DATA  Path to the data directory              (default: data)
#   CANALSEG_JOBS  Number of parallel jobs
#   CANALSEG_DEVICE  Device to use: cuda or cpu

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

# ---- Parse arguments ----
INPUT_IMAGE="${1:?ERROR: No input image provided. Usage: predict.sh <INPUT_IMAGE> [OUTPUT_LABEL] [FOLD]}"
INPUT_IMAGE="$(realpath "$INPUT_IMAGE")"

INPUT_BASENAME="$(basename "$INPUT_IMAGE" .nii.gz)"
OUTPUT_LABEL="${2:-${INPUT_BASENAME}_label-canal_seg.nii.gz}"
FOLD="${3:-0}"

# ---- Environment ----
CANALSEG="$(realpath "${CANALSEG:-model-canal-seg}")"
CANALSEG_DATA="$(realpath "${CANALSEG_DATA:-data}")"

CORES=${SLURM_JOB_CPUS_PER_NODE:-$(lscpu -p | egrep -v '^#' | wc -l)}
JOBS=${CANALSEG_JOBS:-$CORES}

# Cap nnUNet jobs by available memory (same logic as train.sh)
MEMGB=$(awk '/MemTotal/ {print int($2/1024/1024)}' /proc/meminfo)
JOBSNN=$(( JOBS < $((MEMGB / 8)) ? JOBS : $((MEMGB / 8)) ))
JOBSNN=$(( JOBSNN < 1 ? 1 : JOBSNN ))
JOBSNN=${CANALSEG_JOBSNN:-$JOBSNN}

DEVICE=${CANALSEG_DEVICE:-$(python3 -c "import torch; print('cuda' if torch.cuda.is_available() else 'cpu')")}

# ---- nnUNet settings (must match training) ----
nnUNetTrainer=${CANALSEG_TRAINER:-nnUNetTrainerDAExtGPU}
nnUNetPlanner=${CANALSEG_PLANNER:-nnUNetPlannerResEncL}
nnUNetPlans=${CANALSEG_PLANS:-nnUNetPlans}
configuration=3d_fullres
DATASET=${CANALSEG_DATASET:-101}

export nnUNet_raw="$CANALSEG_DATA"/nnUNet/raw
export nnUNet_preprocessed="$CANALSEG_DATA"/nnUNet/preprocessed
export nnUNet_results="$CANALSEG_DATA"/nnUNet/results

# ---- Derive dataset name from nnUNet_raw ----
d_name=$(basename "$(ls -d "$nnUNet_raw"/Dataset${DATASET}_* 2>/dev/null | head -1)" 2>/dev/null || true)
if [[ -z "$d_name" ]]; then
    echo "ERROR: Could not find Dataset${DATASET}_* in $nnUNet_raw"
    exit 1
fi

# ---- Temporary working directory ----
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

TMPDIR_IN="$TMPDIR/input"
TMPDIR_OUT="$TMPDIR/output"
mkdir -p "$TMPDIR_IN" "$TMPDIR_OUT"

echo ""
echo "=========================================="
echo " CanalSeg Inference"
echo "=========================================="
echo "Input image    : $INPUT_IMAGE"
echo "Output label   : $OUTPUT_LABEL"
echo "Fold           : $FOLD"
echo "Dataset        : $d_name"
echo "Trainer        : $nnUNetTrainer"
echo "Plans          : $nnUNetPlans"
echo "Configuration  : $configuration"
echo "Device         : $DEVICE"
echo "Jobs (nnUNet)  : $JOBSNN"
echo "Tmp dir        : $TMPDIR"
echo "=========================================="
echo ""

# ======================================================================================================================
# STEP 1 — Copy and rename input with nnUNet suffix _0000
# ======================================================================================================================

echo "[1/5] Preparing input image..."
TMP_INPUT="$TMPDIR_IN/${INPUT_BASENAME}_0000.nii.gz"
cp "$INPUT_IMAGE" "$TMP_INPUT"

# ======================================================================================================================
# STEP 2 — Reorient to RAS canonical space
# ======================================================================================================================

echo "[2/5] Reorienting to RAS..."
# Record native orientation in SCT convention.
# nibabel's aff2axcodes() returns the direction of the *positive* voxel axes (e.g. RAS),
# whereas SCT's -setorient uses the *negative*-axis (radiological) convention — the
# opposite letter for each axis.  So nibabel RAS == SCT LPI, etc.
NATIVE_ORIENT=$(python3 - <<EOF
import nibabel as nib
img = nib.load("$INPUT_IMAGE")
flip = {"R": "L", "L": "R", "A": "P", "P": "A", "S": "I", "I": "S"}
orient = nib.aff2axcodes(img.affine)
print("".join(flip[c] for c in orient))
EOF
)
echo "      Native orientation: $NATIVE_ORIENT (SCT convention)"

sct_image -i "$TMP_INPUT" -setorient RAS -o "$TMP_INPUT"

# ======================================================================================================================
# STEP 3 — Resample to 1x1x1 mm isotropic
# ======================================================================================================================

echo "[3/5] Resampling to 1x1x1 mm..."
# Record native voxel sizes for later resampling back
NATIVE_RES=$(python3 - <<EOF
import nibabel as nib
img = nib.load("$INPUT_IMAGE")
zooms = img.header.get_zooms()[:3]
print("x".join(f"{z:.6f}" for z in zooms))
EOF
)
echo "      Native resolution: ${NATIVE_RES} mm"

sct_resample -i "$TMP_INPUT" -mm 1x1x1 -o "$TMP_INPUT"

# ======================================================================================================================
# STEP 4 — nnUNet inference
# ======================================================================================================================

echo "[4/5] Running nnUNet inference..."
nnUNetv2_predict \
    -d $DATASET \
    -i "$TMPDIR_IN" \
    -o "$TMPDIR_OUT" \
    -f $FOLD \
    -c $configuration \
    -tr $nnUNetTrainer \
    -p $nnUNetPlans \
    -npp $JOBSNN \
    -nps $JOBSNN \
    -device $DEVICE

# The prediction is written without the _0000 suffix
TMP_PRED="$TMPDIR_OUT/${INPUT_BASENAME}.nii.gz"

if [[ ! -f "$TMP_PRED" ]]; then
    echo "ERROR: Expected prediction not found at $TMP_PRED"
    echo "Contents of $TMPDIR_OUT:"
    ls "$TMPDIR_OUT"
    exit 1
fi

# ======================================================================================================================
# STEP 5 — Resample and reorient prediction back to native space
# ======================================================================================================================

echo "[5/5] Resampling prediction back to native space (${NATIVE_RES} mm) with nearest-neighbour interpolation..."
sct_resample -i "$TMP_PRED" -mm "$NATIVE_RES" -x nn -o "$TMP_PRED"

echo "      Reorienting prediction back to native orientation (${NATIVE_ORIENT}, SCT convention)..."
sct_image -i "$TMP_PRED" -setorient "$NATIVE_ORIENT" -o "$TMP_PRED"

# ======================================================================================================================
# Copy final prediction to output path
# ======================================================================================================================

cp "$TMP_PRED" "$OUTPUT_LABEL"

echo ""
echo "=========================================="
echo " Done! Prediction saved to: $OUTPUT_LABEL"
echo "=========================================="
echo ""