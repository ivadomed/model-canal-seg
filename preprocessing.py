# Authors : Abel Salmona

# those are the function I applied to the data folders before lauching the nnUNet training

import os
import subprocess
from pathlib import Path

# reorientation of the images

# requires sct installed, not fast, will probably be changed soon for the next training

# apply to a directory
def apply_process_to_files(directory):
    # visits all files in the given directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            # calls an 'sct_image' and 'setorient' on each file
            try:
                subprocess.run([
                    'sct_image',
                    '-i', file_path,
                    '- setorient', 'LAS'
                ], check=True)
                print(f"sct_image setorientation applied with {file_path}")

                
            except subprocess.CalledProcessError as e:
                print(f"Error running sct setorientation: {e}")

# here I applied it to imagesTs, labelsTr and imagesTr
apply_process_to_files("C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/imagesTs")
apply_process_to_files("C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/labelsTr")
apply_process_to_files("C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/imagesTr")

# then to ensure that the direction and the origin of the images were the samed
# so qform and sform were the same between image and seg

# OTHER VERSION USING TORCHIO
import sys, argparse, textwrap
import multiprocessing as mp
from functools import partial
from tqdm.contrib.concurrent import process_map
from pathlib import Path
import nibabel as nib
import numpy as np
import torchio as tio

def _transform_seg2image(
        image_path,
        seg_path,
        output_seg_path,
        override=False,
    ):
    '''
    Wrapper function to handle IO.
    '''
    image_path = Path(image_path)
    seg_path = Path(seg_path)
    output_seg_path = Path(output_seg_path)

    # If the output image already exists and we are not overriding it, return
    if not override and output_seg_path.exists():
        return

    # Check if the segmentation file exists
    if not seg_path.is_file():
        output_seg_path.is_file() and output_seg_path.unlink()
        print(f'Error: {seg_path}, Segmentation file not found')
        return

    image = nib.load(image_path)
    seg = nib.load(seg_path)

    output_seg = transform_seg2image(image, seg)

    # Ensure correct segmentation dtype, affine and header
    output_seg = nib.Nifti1Image(
        np.asanyarray(output_seg.dataobj).round().astype(np.uint8),
        output_seg.affine, output_seg.header
    )
    output_seg.set_data_dtype(np.uint8)
    output_seg.set_qform(output_seg.affine)
    output_seg.set_sform(output_seg.affine)

    # Make sure output directory exists and save the segmentation
    output_seg_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(output_seg, output_seg_path)

def transform_seg2image(
        image,
        seg,
    ):
    '''
    Transform the segmentation to the image space to have the same origin, spacing, direction and shape as the image.

    Parameters
    ----------
    image : nibabel.Nifti1Image
        Image.
    seg : nibabel.Nifti1Image
        Segmentation.

    Returns
    -------
    nibabel.Nifti1Image
        Output segmentation.
    '''
    image_data = np.asanyarray(image.dataobj).astype(np.float64)
    seg_data = np.asanyarray(seg.dataobj).round().astype(np.uint8)

    # Make TorchIO images
    tio_img=tio.ScalarImage(tensor=image_data[None, ...], affine=image.affine)
    tio_seg=tio.LabelMap(tensor=seg_data[None, ...], affine=seg.affine)

    # Resample the segmentation to the image space
    tio_output_seg = tio.Resample(tio_img)(tio_seg)
    output_seg_data = tio_output_seg.data.numpy()[0, ...].astype(np.uint8)

    output_seg = nib.Nifti1Image(output_seg_data, image.affine, seg.header)

    return output_seg


# function to copy the header and affine of a file to another
def trouver_image_correspondante(nom_base, dossier_cible):
    # replace '_0000.nii.gz' by '.nii.gz' to find the corresponding file
    nom_cible = nom_base.replace('_0000.nii.gz', '.nii.gz')
    chemin_cible = os.path.join(dossier_cible, nom_cible)
    if os.path.exists(chemin_cible):
        return chemin_cible
    return None

# principal function
def register_seg_to_image(dossier_base, dossier_cible):
    # go through all files in the base directory
    for nom_fichier_base in os.listdir(dossier_base):
        if nom_fichier_base.endswith('_0000.nii.gz'):  
            chemin_base = os.path.join(dossier_base, nom_fichier_base)
            
            # find the corresponding image in the target folder
            chemin_cible = trouver_image_correspondante(nom_fichier_base, dossier_cible)
            
            if chemin_cible is not None:
                _transform_seg2image(chemin_base, chemin_cible, chemin_cible, override=True)
                print(f"Header et affine remplacés pour : {nom_fichier_base} -> {nom_fichier_base.replace('_0000.nii.gz', '.nii.gz')}")
            else:
                print(f"Aucune correspondance trouvée pour {nom_fichier_base}")

# apply to the training set
register_seg_to_image("C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/imagesTr", "C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/labelsTr")
