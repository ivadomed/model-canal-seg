#!/bin/bash

# to be runned with sct_run_batch using batch_config.json
# sct_run_batch -config batch_config.json 
# do not forget to put the path also in the batch_config.json file

# check if the user has provided a subject BIDS folder
if [ -z "$1" ]; then
  echo "Erreur : Vous devez fournir le chemin d'un dossier de sujet BIDS."
  exit 1
fi

# complete with the link of the bids global folder
global_folder="/home/ge.polymtl.ca/p121315/canal_analysis/test-dcm-brno"

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

# command to segment the spinal cord and other structures
sct_command="sct_deepseg -task totalspineseg"
# command to label the spinal cord
sct_command2="sct_label_vertebrae"


# goes through all the T2w files in the 'anat' sub-folder
for file in "$anat_dir"/*T2w.nii.gz; do
  # check if the file exists
  base_name=$(basename "$file" .nii.gz)
  seg_name="${base_name}_seg.nii.gz"
  seg_path="$anat_dir/$seg_name"

  if [ -f "$file" ]; then
    echo "Traitement du fichier : $file"
    
    # apply the segmentation of tss command
    $sct_command -i "$file"

    # apply the labeling command
    $sct_command2 -i "$file" -s "$seg_path" -c t2

    # apply labeling command

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

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*.cache" -type f -delete
echo "Tous les fichiers cache ont été supprimés."

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*straight.nii.gz" -type f -delete
echo "Tous les fichiers JSON ont été supprimés."

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*curve.nii.gz" -type f -delete
echo "Tous les fichiers JSON ont été supprimés."

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*ref.nii.gz" -type f -delete
echo "Tous les fichiers JSON ont été supprimés."

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*cord.nii.gz" -type f -delete
echo "Tous les fichiers JSON ont été supprimés."

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*canal.nii.gz" -type f -delete
echo "Tous les fichiers JSON ont été supprimés."

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*levels.nii.gz" -type f -delete
echo "Tous les fichiers JSON ont été supprimés."

# supression of JSON files in the base folder
echo "Suppression des fichiers JSON dans le dossier de base..."
find "$anat_dir" -name "*step1_output.nii.gz" -type f -delete
echo "Tous les fichiers JSON ont été supprimés."

