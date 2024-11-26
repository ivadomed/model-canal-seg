# this script defines a post processing pipeline 
# since the model aims to segment the pinal canal which is a connected component
# we can use the largest connected component as the final segmentation

# the function keep_largest_connected_component() takes a binary image as input and returns the largest connected component

# the function process_segmentation_file() loads a NIfTI file, applies the post-processing and saves the result
# the function process_segmentation_folder() processes all NIfTI files in a folder

import numpy as np
import nibabel as nib
from scipy.ndimage import label
import os
import argparse

# flake8: noqa

def keep_largest_connected_component(segmentation):
    """
    Keeps the largest connected component in a binary image.

    Parameters:
        segmentation (numpy.ndarray): binary image (3D).

    Returns:
        numpy.ndarray: binary image with only the largest connected component.
    """
    # label connected components in the binary image
    labeled_array, num_features = label(segmentation)

    changed = False

    # if there are multiple connected components
    if num_features > 1:
        # count the size of each connected component
        component_sizes = np.bincount(labeled_array.ravel())
        print('component_sizes:', component_sizes)

        # ignore the background (component 0)
        component_sizes[0] = 0

        # find the largest connected component
        largest_component = component_sizes.argmax()
        print('largest_component:', largest_component)

        # create a binary mask with only the largest connected component
        largest_component_mask = (labeled_array == largest_component).astype(np.uint8)
        print('new image components:', np.bincount(largest_component_mask.ravel()))

        changed = True

        return largest_component_mask, changed
    else:
        print('No post-processing needed')
        # if there is only one connected component, return the original image
        return segmentation, changed


def process_segmentation_file(input_file, output_file):
    """
    Loads a NIfTI file, applies the post-processing and saves the result.

    Parameters:
        input_file (str): path to the input NIfTI file (before post-processing).
        output_file (str): path to the output NIfTI file (after post-processing).
    """
    print('Processing:', input_file)
    img = nib.load(input_file)
    segmentation = img.get_fdata()
    # apply the post-processing
    cleaned_segmentation, change = keep_largest_connected_component(segmentation)

    if change == True:
        # save the cleaned segmentation
        print('Saving:', output_file)
        cleaned_img = nib.Nifti1Image(cleaned_segmentation, img.affine)
        nib.save(cleaned_img, output_file)


def process_segmentation_folder(input_folder, output_folder, overwrite=False):
    """
    Processes all NIfTI files in a folder.
    """
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.nii.gz'):
            input_file = os.path.join(input_folder, file_name)

            if not overwrite and os.path.exists(os.path.join(output_folder, file_name)):
                output_file = os.path.join(output_folder, file_name.replace('.nii.gz', '_cleaned.nii.gz'))
                process_segmentation_file(input_file, output_file)
            else:
                output_file = os.path.join(output_folder, file_name)
                process_segmentation_file(input_file, output_file)

parser = argparse.ArgumentParser(description="Script to post-process a segmentation")
parser.add_argument('--input', type=str, required=True, help="Input path")
parser.add_argument('--output', type=str, required=True, help="Output path")

args = parser.parse_args()

input_path = args.input
output_path = args.output

# apply the post-processing to all NIfTI files in the input folder
if os.path.isdir(input_path):
    process_segmentation_folder(input_path, output_path)
elif os.path.isfile(input_path):
    process_segmentation_file(input_path, output_path)