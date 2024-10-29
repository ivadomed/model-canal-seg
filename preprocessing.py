# Authors : Abel Salmona

# those are the function I applied to the data folders before lauching the nnUNet training

import os
from pathlib import Path
import sys, argparse, textwrap
import multiprocessing as mp
from functools import partial
from tqdm.contrib.concurrent import process_map
import nibabel as nib
import numpy as np
import torchio as tio

# reorientation of the images

def change_orientation(im_src, orientation, im_dst=None, inverse=False):
    """
    Copied from https://github.com/spinalcordtoolbox/spinalcordtoolbox/

    :param im_src: source image
    :param orientation: orientation string (SCT "from" convention)
    :param im_dst: destination image (can be the source image for in-place
                   operation, can be unset to generate one)
    :param inverse: if you think backwards, use this to specify that you actually
                    want to transform *from* the specified orientation, not *to* it.
    :return: an image with changed orientation

    .. note::
        - the resulting image has no path member set
        - if the source image is < 3D, it is reshaped to 3D and the destination is 3D
    """

    if len(im_src.data.shape) < 3:
        pass  # Will reshape to 3D
    elif len(im_src.data.shape) == 3:
        pass  # OK, standard 3D volume
    elif len(im_src.data.shape) == 4:
        pass  # OK, standard 4D volume
    elif len(im_src.data.shape) == 5 and im_src.header.get_intent()[0] == "vector":
        pass  # OK, physical displacement field
    else:
        raise NotImplementedError("Don't know how to change orientation for this image")

    im_src_orientation = im_src.orientation
    im_dst_orientation = orientation
    if inverse:
        im_src_orientation, im_dst_orientation = im_dst_orientation, im_src_orientation

    perm, inversion = _get_permutations(im_src_orientation, im_dst_orientation)

    if im_dst is None:
        im_dst = im_src.copy()
        im_dst._path = None

    im_src_data = im_src.data
    if len(im_src_data.shape) < 3:
        im_src_data = im_src_data.reshape(tuple(list(im_src_data.shape) + ([1] * (3 - len(im_src_data.shape)))))

    # Update data by performing inversions and swaps

    # axes inversion (flip)
    data = im_src_data[::inversion[0], ::inversion[1], ::inversion[2]]

    # axes manipulations (transpose)
    if perm == [1, 0, 2]:
        data = np.swapaxes(data, 0, 1)
    elif perm == [2, 1, 0]:
        data = np.swapaxes(data, 0, 2)
    elif perm == [0, 2, 1]:
        data = np.swapaxes(data, 1, 2)
    elif perm == [2, 0, 1]:
        data = np.swapaxes(data, 0, 2)  # transform [2, 0, 1] to [1, 0, 2]
        data = np.swapaxes(data, 0, 1)  # transform [1, 0, 2] to [0, 1, 2]
    elif perm == [1, 2, 0]:
        data = np.swapaxes(data, 0, 2)  # transform [1, 2, 0] to [0, 2, 1]
        data = np.swapaxes(data, 1, 2)  # transform [0, 2, 1] to [0, 1, 2]
    elif perm == [0, 1, 2]:
        # do nothing
        pass
    else:
        raise NotImplementedError()

    # Update header

    im_src_aff = im_src.hdr.get_best_affine()
    aff = nib.orientations.inv_ornt_aff(
        np.array((perm, inversion)).T,
        im_src_data.shape)
    im_dst_aff = np.matmul(im_src_aff, aff)

    im_dst.header.set_qform(im_dst_aff)
    im_dst.header.set_sform(im_dst_aff)
    im_dst.header.set_data_shape(data.shape)
    im_dst.data = data

    return im_dst

# requires sct installed, not fast, will probably be changed soon for the next training

# apply to a directory
def apply_process_to_files(directory):
    # visits all files in the given directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path.endswith('.nii.gz'):
                # load the image
                im = nib.load(file_path)
                # change the orientation
                im = change_orientation(im, 'LAS')
                # save the image
                nib.save(im, file_path)
                print(f"Orientation modifiée pour : {file_path}")
            # calls change_orientation on each file     

# here I applied it to imagesTs, labelsTr and imagesTr
apply_process_to_files("C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/imagesTs")
apply_process_to_files("C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/labelsTr")
apply_process_to_files("C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/imagesTr")


# then to ensure that the direction and the origin of the images were the samed
# so qform and sform were the same between image and seg

# OTHER VERSION USING TORCHIO

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
