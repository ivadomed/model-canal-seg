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

# then to ensure that the direction and the origin of the images were the samed
# so qform and sform were the same between image and seg

import nibabel as nib

# function to copy the header and affine of a file to another
def trouver_image_correspondante(nom_base, dossier_cible):
    # replace '_0000.nii.gz' by '.nii.gz' to find the corresponding file
    nom_cible = nom_base.replace('_0000.nii.gz', '.nii.gz')
    chemin_cible = os.path.join(dossier_cible, nom_cible)
    if os.path.exists(chemin_cible):
        return chemin_cible
    return None

# principal function
def remplacer_header_et_affine(dossier_base, dossier_cible):
    # go through all files in the base directory
    for nom_fichier_base in os.listdir(dossier_base):
        if nom_fichier_base.endswith('_0000.nii.gz'):  
            chemin_base = os.path.join(dossier_base, nom_fichier_base)
            
            # find the corresponding image in the target folder
            chemin_cible = trouver_image_correspondante(nom_fichier_base, dossier_cible)
            
            if chemin_cible is not None:
                # load images with nibabel
                img_base = nib.load(chemin_base)
                img_cible = nib.load(chemin_cible)
                
                # extract the header and affine matrix of the base image
                new_header = img_base.header
                new_affine = img_base.affine
                
                # create a new image with the affine and header of the base image
                img_cible_modifiee = nib.Nifti1Image(img_cible.get_fdata(), new_affine, header=new_header)
                
                # save the modified image
                nib.save(img_cible_modifiee, chemin_cible)
                print(f"Header et affine remplacés pour : {nom_fichier_base} -> {nom_fichier_base.replace('_0000.nii.gz', '.nii.gz')}")
            else:
                print(f"Aucune correspondance trouvée pour {nom_fichier_base}")
