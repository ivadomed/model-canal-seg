#!/bin/bash

# to be runned with sct_run_batch using batch_config.json
# sct_run_batch -config batch_config.json 

# check if the user has provided a subject BIDS folder
if [ -z "$1" ]; then
  echo "Erreur : Vous devez fournir le chemin d'un dossier de sujet BIDS."
  exit 1
fi

global_folder="C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/biomarker-analysis/test-dcm-brno"

# get the subject BIDS folder
subject_dir="$global_folder/$1"

# check if the subject BIDS folder exists
if [ ! -d "$subject_dir" ]; then
  echo "Erreur : Le dossier $subject_dir n'existe pas."
  exit 1
fi

# path to the 'anat' sub-folder
anat_dir="$subject_dir/anat"

# check if the 'anat' sub-folder exists
if [ ! -d "$anat_dir" ]; then
  echo "Erreur : Le sous-dossier 'anat' est introuvable dans $subject_dir."
  exit 1
fi

# command to segment the spinal cord
sct_command="sct_deepseg -task seg_sc_contrast_agnostic"

# goes through all the T2w files in the 'anat' sub-folder
for file in "$anat_dir"/*T2w.nii.gz; do
  # check if the file exists
  if [ -f "$file" ]; then
    echo "Traitement du fichier : $file"
    
    # apply the segmentation command
    $sct_command -i "$file"

    if [ $? -eq 0 ]; then
      echo "Segmentation réussie pour : $file"
    else
      echo "Erreur lors de la segmentation de : $file"
    fi
  fi
done

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*.json" -type f -delete
echo "Tous les fichiers JSON ont été supprimés."