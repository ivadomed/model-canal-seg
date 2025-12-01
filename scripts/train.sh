#!/bin/bash

# This script train the CanalSeg nnUNet model.
# It get also optional parameters DATASET and FOLD.

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

# Set the datasets to work with - default is 101 102
DATASETS=${1:-101}

# Set the fold to work with - default is 0
FOLD=${2:-0}

# set CANALSEG and CANALSEG_DATA if not set
CANALSEG="$(realpath "${CANALSEG:-model-canal-seg}")"
CANALSEG_DATA="$(realpath "${CANALSEG_DATA:-data}")"

# Get the number of CPUs
CORES=${SLURM_JOB_CPUS_PER_NODE:-$(lscpu -p | egrep -v '^#' | wc -l)}

# Get memory in GB
MEMGB=$(awk '/MemTotal/ {print int($2/1024/1024)}' /proc/meminfo)

# Set the number of jobs
JOBS=${TOTALSPINESEG_JOBS:-$CORES}

# Set the number of jobs for the nnUNet
JOBSNN=$(( JOBS < $((MEMGB / 8)) ? JOBS : $((MEMGB / 8)) ))
JOBSNN=$(( JOBSNN < 1 ? 1 : JOBSNN ))
JOBSNN=${CANALSEG_JOBSNN:-$JOBSNN}

# Set the device to cpu if cuda is not available
DEVICE=${CANALSEG_DEVICE:-$(python3 -c "import torch; print('cuda' if torch.cuda.is_available() else 'cpu')")}

# Set nnunet params
export nnUNet_def_n_proc=$JOBSNN
export nnUNet_n_proc_DA=$JOBSNN
export nnUNet_raw="$CANALSEG_DATA"/nnUNet/raw
export nnUNet_preprocessed="$CANALSEG_DATA"/nnUNet/preprocessed
export nnUNet_results="$CANALSEG_DATA"/nnUNet/results
export nnUNet_exports="$CANALSEG_DATA"/nnUNet/exports

# Copy auglab trainer to nnunet folder
auglab_add_nnunettrainer -t nnUNetTrainerDAExtGPU

nnUNetTrainer=${3:-nnUNetTrainerDAExtGPU}
nnUNetPlanner=${4:-nnUNetPlannerResEncL}
nnUNetPlans=${5:-nnUNetPlans}
configuration=3d_fullres
data_identifier=nnUNetPlans_3d_fullres

echo ""
echo "Running with the following parameters:"
echo "nnUNet_raw=${nnUNet_raw}"
echo "nnUNet_preprocessed=${nnUNet_preprocessed}"
echo "nnUNet_results=${nnUNet_results}"
echo "nnUNet_exports=${nnUNet_exports}"
echo "nnUNetTrainer=${nnUNetTrainer}"
echo "nnUNetPlanner=${nnUNetPlanner}"
echo "nnUNetPlans=${nnUNetPlans}"
echo "configuration=${configuration}"
echo "data_identifier=${data_identifier}"
echo "JOBSNN=${JOBSNN}"
echo "DEVICE=${DEVICE}"
echo "DATASETS=${DATASETS[@]}"
echo "FOLD=${FOLD}"
echo ""

for d in ${DATASETS[@]}; do
    # Get the dataset name
    d_name=$(basename "$(ls -d "$nnUNet_raw"/Dataset${d}_*)")

    if [ ! -f "$nnUNet_preprocessed"/$d_name/dataset_fingerprint.json ]; then
        echo "Extracting fingerprint dataset $d_name"
        nnUNetv2_extract_fingerprint -d $d -np $JOBSNN --verify_dataset_integrity
    fi

    if [ ! -f "$nnUNet_preprocessed"/$d_name/${nnUNetPlans}.json ]; then
        echo "Planning dataset $d_name"
        nnUNetv2_plan_experiment -d $d -pl $nnUNetPlanner -overwrite_plans_name $nnUNetPlans
    fi

    # If already preprocess do not preprocess again
    if [[ ! -d "$nnUNet_preprocessed"/$d_name/$data_identifier || ! $(find "$nnUNet_raw"/$d_name/labelsTr -name "*.nii.gz" | wc -l) -eq $(find "$nnUNet_preprocessed"/$d_name/$data_identifier -name "*.npz" | wc -l) || ! $(find "$nnUNet_raw"/$d_name/labelsTr -name "*.nii.gz" | wc -l) -eq $(find "$nnUNet_preprocessed"/$d_name/$data_identifier -name "*.pkl" | wc -l) ]]; then
        nnUNetv2_preprocess -d $d -plans_name $nnUNetPlans -c $configuration -np $JOBSNN
    fi

    echo "Training dataset $d_name fold $FOLD"
    AUGLAB_PARAMS_GPU_JSON=$TOTALSPINESEG/totalspineseg/models/transforms_gpu.json nnUNetv2_train $d $configuration $FOLD -tr $nnUNetTrainer -p $nnUNetPlans --c -device $DEVICE

    echo "Export the model for dataset $d_name in "$nnUNet_exports""
    mkdir -p "$nnUNet_exports"
    mkdir -p "$nnUNet_results"/$d_name/ensembles
    nnUNetv2_export_model_to_zip -d $d -o "$nnUNet_exports"/${d_name}__${nnUNetTrainer}__${nnUNetPlans}__${configuration}__fold_$FOLD.zip -c $configuration -f $FOLD -tr $nnUNetTrainer -p $nnUNetPlans

    echo "Testing nnUNet model for dataset $d_name"
    mkdir -p "$nnUNet_results"/$d_name/${nnUNetTrainer}__${nnUNetPlans}__${configuration}/fold_${FOLD}/test
    nnUNetv2_predict -d $d -i "$nnUNet_raw"/$d_name/imagesTs -o "$nnUNet_results"/$d_name/${nnUNetTrainer}__${nnUNetPlans}__${configuration}/fold_${FOLD}/test -f $FOLD -c $configuration -tr $nnUNetTrainer -p $nnUNetPlans -npp $JOBSNN -nps $JOBSNN
    nnUNetv2_evaluate_folder "$nnUNet_raw"/$d_name/labelsTs "$nnUNet_results"/$d_name/${nnUNetTrainer}__${nnUNetPlans}__${configuration}/fold_${FOLD}/test -djfile "$nnUNet_results"/$d_name/${nnUNetTrainer}__${nnUNetPlans}__${configuration}/dataset.json -pfile "$nnUNet_results"/$d_name/${nnUNetTrainer}__${nnUNetPlans}__${configuration}/plans.json -np $JOBSNN

    p="$(realpath .)"
    cd "$nnUNet_results"
    zip "$nnUNet_exports"/${d_name}__${nnUNetTrainer}__${nnUNetPlans}__${configuration}__fold_$FOLD.zip $d_name/${nnUNetTrainer}__${nnUNetPlans}__${configuration}/fold_${FOLD}/test/summary.json
    cd "$p"

    echo "Export nnUNet dataset list for dataset $d_name"
    cd "$nnUNet_raw"/$d_name
    ls */ > "$nnUNet_results"/$d_name/dataset.txt
    cd "$nnUNet_results"
    zip "$nnUNet_exports"/${d_name}__${nnUNetTrainer}__${nnUNetPlans}__${configuration}__fold_$FOLD.zip $d_name/dataset.txt
    cd "$nnUNet_preprocessed"
    zip "$nnUNet_exports"/${d_name}__${nnUNetTrainer}__${nnUNetPlans}__${configuration}__fold_$FOLD.zip $d_name/splits_final.json
    cd "$p"

done
