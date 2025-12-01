"""
Script copied from https://github.com/spinalcordtoolbox/disc-labeling-hourglass
"""

import os
import re
import time
import json
from pathlib import Path
import subprocess

## Functions
def get_img_path_from_label_path(str_path):
    """
    This function does 2 things: ⚠️ Files need to be stored in a BIDS compliant dataset
        - Step 1: Remove label suffix (e.g. "_labels-disc-manual"). The suffix is always between the MRI contrast and the file extension.
        - Step 2: Remove derivatives path (e.g. derivatives/labels/). The first folders is always called derivatives but the second may vary (e.g. labels_soft)

    :param path: absolute path to the label img. Example: /<path_to_BIDS_data>/derivatives/labels/sub-amuALT/anat/sub-amuALT_T1w_labels-disc-manual.nii.gz
    :return: img path. Example: /<path_to_BIDS_data>/sub-amuALT/anat/sub-amuALT_T1w.nii.gz

    Copied from https://github.com/spinalcordtoolbox/disc-labeling-benchmark

    """
    # Load path
    path = Path(str_path)

    # Extract file extension
    ext = ''.join(path.suffixes)

    # Find contrast index
    path_list = path.name.replace(ext, '').split('_')
    suffixes_pos = [1 if len(part.split('-')) == 1 else 0 for part in path_list]
    contrast_idx = suffixes_pos.index(1) # Find suffix

    # Get img name
    img_name = '_'.join(path_list[:contrast_idx+1]) + ext
    
    # Create a list of the directories
    dir_list = str(path.parent).split('/')

    # Remove "derivatives" and "labels" folders
    derivatives_idx = dir_list.index('derivatives')
    dir_path = '/'.join(dir_list[0:derivatives_idx] + dir_list[derivatives_idx+2:])

    # Recreate img path
    img_path = os.path.join(dir_path, img_name)

    return img_path


def get_cont_path_from_other_cont(str_path, cont):
    """
    :param str_path: absolute path to the input nifti img. Example: /<path_to_BIDS_data>/sub-amuALT/anat/sub-amuALT_T1w.nii.gz
    :param cont: contrast of the target output image stored in the same data folder. Example: T2w
    :return: path to the output target image. Example: /<path_to_BIDS_data>/sub-amuALT/anat/sub-amuALT_T2w.nii.gz

    """
    # Load path
    path = Path(str_path)

    # Extract file extension
    ext = ''.join(path.suffixes)

    # Remove input contrast from name
    path_list = path.name.split(ext)[0].split('_')
    suffixes_pos = [1 if len(part.split('-')) == 1 else 0 for part in path_list]
    contrast_idx = suffixes_pos.index(1) # Find suffix

    # New image name
    img_name = '_'.join(path_list[:contrast_idx]+[cont]+path_list[contrast_idx+1:]) + ext

    # Recreate img path
    img_path = os.path.join(str(path.parent), img_name)

    return img_path


##
def fetch_subject_and_session(filename_path):
    """
    Get subject ID, session ID and filename from the input BIDS-compatible filename or file path
    The function works both on absolute file path as well as filename
    :param filename_path: input nifti filename (e.g., sub-001_ses-01_T1w.nii.gz) or file path
    (e.g., /home/user/MRI/bids/derivatives/labels/sub-001/ses-01/anat/sub-001_ses-01_T1w.nii.gz
    :return: subjectID: subject ID (e.g., sub-001)
    :return: sessionID: session ID (e.g., ses-01)
    :return: filename: nii filename (e.g., sub-001_ses-01_T1w.nii.gz)
    :return: contrast: MRI modality (dwi or anat)
    :return: echoID: echo ID (e.g., echo-1)
    :return: acquisition: acquisition (e.g., acq_sag)
    Copied from https://github.com/spinalcordtoolbox/manual-correction
    """

    _, filename = os.path.split(filename_path)              # Get just the filename (i.e., remove the path)
    subject = re.search('sub-(.*?)[_/]', filename_path)     # [_/] means either underscore or slash
    subjectID = subject.group(0)[:-1] if subject else ""    # [:-1] removes the last underscore or slash

    session = re.search('ses-(.*?)[_/]', filename_path)     # [_/] means either underscore or slash
    sessionID = session.group(0)[:-1] if session else ""    # [:-1] removes the last underscore or slash

    echo = re.search('echo-(.*?)[_]', filename_path)     # [_/] means either underscore or slash
    echoID = echo.group(0)[:-1] if echo else ""    # [:-1] removes the last underscore or slash

    acq = re.search('acq-(.*?)[_]', filename_path)     # [_/] means either underscore or slash
    acquisition = acq.group(0)[:-1] if acq else ""    # [:-1] removes the last underscore or slash
    # REGEX explanation
    # . - match any character (except newline)
    # *? - match the previous element as few times as possible (zero or more times)

    contrast = 'dwi' if 'dwi' in filename_path else 'anat'  # Return contrast (dwi or anat)

    return subjectID, sessionID, filename, contrast, echoID, acquisition


def fetch_contrast(str_path):
    '''
    Extract MRI contrast from a BIDS-compatible filename/filepath
    :param str_path: image file path or file name. (e.g sub-001_ses-01_T1w.nii.gz)
    '''
    # Load path
    path = Path(str_path)

    # Extract file extension
    ext = ''.join(path.suffixes)

    # Remove input contrast from name
    path_list = path.name.split(ext)[0].split('_')
    suffixes_pos = [1 if len(part.split('-')) == 1 else 0 for part in path_list]
    contrast_idx = suffixes_pos.index(1) # Find first suffix

    return path_list[contrast_idx]

##
def fetch_img_paths(config_data, split='TESTING'):
    # Get file paths based on split
    if 'DATASETS_PATH' in config_data.keys():
        paths = [os.path.join(config_data['DATASETS_PATH'], path) for path in config_data[split]]
    else:
        paths = config_data[split]
    # Check TYPE to get img_path
    if config_data['TYPE'] == 'IMAGE':
        return paths
    elif config_data['TYPE'] == 'LABEL':
        img_paths = []
        for path in paths:        
            img_paths.append(get_img_path_from_label_path(path))
        return img_paths
    else:
        raise ValueError('TYPE error: The TYPE can only be "IMAGE" or "LABEL"')

##
def get_seg_path_from_img_path(img_path, seg_suffix='_seg', derivatives_path='/derivatives/labels'):
    """
    This function returns the segmentaion path from an image path. Images need to be stored in a BIDS compliant dataset.

    :param img_path: String path to niftii image
    :param seg_suffix: Segmentation suffix
    :param derivatives_path: Relative path to derivatives folder where labels are stored (e.i. '/derivatives/labels')
    """
    # Extract information from path
    subjectID, sessionID, filename, contrast, echoID = fetch_subject_and_session(img_path)

    # Extract file extension
    path_obj = Path(img_path)
    ext = ''.join(path_obj.suffixes)

    # Create segmentation name
    seg_name = path_obj.name.split('.')[0] + seg_suffix + ext

    # Split path using "/" (TODO: check if it works for windows users)
    path_list = img_path.split('/')

    # Extract subject folder index
    sub_folder_idx = path_list.index(subjectID)

    # Reconstruct seg_path
    seg_path = os.path.join('/'.join(path_list[:sub_folder_idx]), derivatives_path, path_list[sub_folder_idx:-1], seg_name)
    return seg_path

def get_seg_path_from_label_path(label_path, seg_suffix='_seg'):
    """
    This function remove the label suffix to add the segmentation suffix
    """
    # Load path
    path = Path(label_path)

    # Extract file extension
    ext = ''.join(path.suffixes)

    # Find contrast index
    path_list = path.name.replace(ext, '').split('_')
    suffixes_pos = [1 if len(part.split('-')) == 1 else 0 for part in path_list]
    contrast_idx = suffixes_pos.index(1) # Find suffix

    # Get img name
    seg_name = '_'.join(path_list[:contrast_idx+1]) + seg_suffix + ext
    seg_path = path.parent / seg_name

    return str(seg_path)

##
def create_json(fname_nifti):
    """
    Create JSON sidecar with meta information
    :param fname_nifti: str: File path of the nifti image to associate with the JSON sidecar
    Based on https://github.com/spinalcordtoolbox/manual-correction
    """
    fname_json = fname_nifti.replace('.gz', '').replace('.nii', '.json')
    
    # Init new json dict
    json_dict = {'GeneratedBy': []}
    
    # Add new author with time and date
    json_dict['GeneratedBy'].append({'NAME': 'Discs labeling playground', 'Date': time.strftime('%Y-%m-%d %H:%M:%S')})
    with open(fname_json, 'w') as outfile: # w to overwrite the file
        json.dump(json_dict, outfile, indent=4)
        # Add last newline
        outfile.write("\n")
    print("JSON sidecar was created: {}".format(fname_json))

##
def generate_qc(img_path, label_path, qc_path):
    '''
    Generate QC report
    '''
    subprocess.run([
                    'sct_qc',
                    '-i', img_path,
                    '-s', label_path,
                    '-p', 'sct_label_vertebrae',
                    '-qc', qc_path
                    ])


from scipy import ndimage
import numpy as np


def dice_score(prediction, groundtruth, smooth=1.):
    numer = (prediction * groundtruth).sum()
    denor = (prediction + groundtruth).sum()
    # loss = (2 * numer + self.smooth) / (denor + self.smooth)
    dice = (2 * numer + smooth) / (denor + smooth)
    return dice


def lesion_wise_tp_fp_fn(truth, prediction, overlap_ratio=0.1):
    """
    Computes the true positives, false positives, and false negatives two masks. Masks are considered true positives
    if there is at least `overlap_ratio` overlap between the truth and the prediction.
    i.e. if overlap_ratio = 0.1, then at least 10% of the lesion voxels should overlap between the truth and 
    the prediction to be considered as true positive.
    Adapted from: https://github.com/npnl/atlas2_grand_challenge/blob/main/isles/scoring.py#L341

    Parameters
    ----------
    truth : array-like, bool
        3D array. If not boolean, will be converted.
    prediction : array-like, bool
        3D array with a shape matching 'truth'. If not boolean, will be converted.
    empty_value : scalar, float
        Optional. Value to which to default if there are no labels. Default: 1.0.

    Returns
    -------
    tp (int): 3D connected-component from the ground-truth image that overlaps at least on one voxel with the prediction image.
    fp (int): 3D connected-component from the prediction image that has no voxel overlapping with the ground-truth image.
    fn (int): 3d connected-component from the ground-truth image that has no voxel overlapping with the prediction image.

    Notes
    -----
    This function computes lesion-wise score by defining true positive lesions (tp), false positive lesions (fp) and
    false negative lesions (fn) using 3D connected-component-analysis.

    tp: 3D connected-component from the ground-truth image that overlaps at least on one voxel with the prediction image.
    fp: 3D connected-component from the prediction image that has no voxel overlapping with the ground-truth image.
    fn: 3d connected-component from the ground-truth image that has no voxel overlapping with the prediction image.
    """
    tp, fp, fn = 0, 0, 0

    # For each true lesion, check if at least a threshold overlap_ratio of the lesion voxels overlap with the prediction.
    # This determines true positives and false negatives (unpredicted lesions)
    labeled_ground_truth, num_truth_lesions = ndimage.label(truth.astype(bool))
    for idx_lesion in range(1, num_truth_lesions + 1):
        lesion = labeled_ground_truth == idx_lesion
        num_truth_lesion_voxels = np.sum(lesion)  # Total number of voxels in the GT lesion
        overlapping_voxels = np.sum(lesion * prediction)  # Number of GT voxels that overlap with the prediction
        # Check if at least 10% of the lesion voxels overlap with the prediction
        if overlapping_voxels / num_truth_lesion_voxels >= overlap_ratio:
            tp += 1
        else:
            fn += 1

    # For each predicted lesion, check if there is at least one overlapping voxel in the ground truth.
    labeled_prediction, num_pred_lesions = ndimage.label(prediction.astype(bool))
    for idx_lesion in range(1, num_pred_lesions+1):
        lesion = labeled_prediction == idx_lesion
        # num_pred_lesion_voxels = np.sum(lesion)
        # overlapping_voxels = np.sum(lesion & truth)
        # if overlapping_voxels / num_pred_lesion_voxels < self.overlap_ratio:
        #     fp += 1
        lesion_pred_sum = lesion + truth
        if(np.max(lesion_pred_sum) <= 1):  # No overlap
            fp += 1

    return tp, fp, fn

def lesion_f1_score(truth, prediction, overlap_ratio=0.1):
    """
    Computes the lesion-wise F1-score between two masks by defining true positive lesions (tp), false positive lesions (fp)
    and false negative lesions (fn) using 3D connected-component-analysis.

    Masks are considered true positives if at least one voxel overlaps between the truth and the prediction.

    Returns
    -------
    f1_score : float
        Lesion-wise F1-score as float.
        Max score = 1
        Min score = 0
        If both images are empty (tp + fp + fn =0) = empty_value
    """
    empty_value = 1.0   # Value to which to default if there are no labels. Default: 1.0.

    if not np.any(truth) and not np.any(prediction):
        # Both reference and prediction are empty --> model learned correctly
        return 1.0
    elif np.any(truth) and not np.any(prediction):
        # Reference is not empty, prediction is empty --> model did not learn correctly (it's false negative)
        return 0.0
    # if the ref is empty and prediction is empty --> it's false positive
    elif not np.any(truth) and np.any(prediction):
        return 0.0
    # if both are not empty, it's true positive
    else:
        tp, fp, fn = lesion_wise_tp_fp_fn(truth, prediction, overlap_ratio)
        f1_score = empty_value

        # Compute f1_score
        denom = tp + (fp + fn)/2
        if(denom != 0):
            f1_score = tp / denom
        return f1_score

def lesion_ppv(truth, prediction, overlap_ratio=0.1):
    """
    Computes the lesion-wise positive predictive value (PPV) between two masks
    Returns
    -------
    ppv (float): Lesion-wise positive predictive value as float.
        Max score = 1
        Min score = 0
        If both images are empty (tp + fp + fn =0) = empty_value
    """
    if not np.any(truth) and not np.any(prediction):
        # Both reference and prediction are empty --> model learned correctly
        return 1.0
    elif np.any(truth) and not np.any(prediction):
        # Reference is not empty, prediction is empty --> model did not learn correctly (it's false negative)
        return 0.0
    # if the predction is not empty and ref is empty, it's false positive
    elif not np.any(truth) and np.any(prediction):
        return 0.0
    # if both are not empty, it's true positive
    else:
        tp, fp, _ = lesion_wise_tp_fp_fn(truth, prediction, overlap_ratio)
        ppv = 1.0

        # Compute ppv
        denom = tp + fp
        # denom should ideally not be zero inside this else as it should be caught by the empty checks above
        if(denom != 0):
            ppv = tp / denom
        return ppv

def lesion_sensitivity(truth, prediction, overlap_ratio=0.1):
    """
    Computes the lesion-wise sensitivity between two masks
    Returns
    -------
    sensitivity (float): Lesion-wise sensitivity as float.
        Max score = 1
        Min score = 0
        If both images are empty (tp + fp + fn =0) = empty_value
    """
    empty_value = 1.0   # Value to which to default if there are no labels. Default: 1.0.

    if not np.any(truth) and not np.any(prediction):
        # Both reference and prediction are empty --> model learned correctly
        return 1.0
    # if the predction is not empty and ref is empty, it's false positive
    # if both are not empty, it's true positive
    else:

        tp, _, fn = lesion_wise_tp_fp_fn(truth, prediction, overlap_ratio)
        sensitivity = empty_value

        # Compute sensitivity
        denom = tp + fn
        if(denom != 0):
            sensitivity = tp / denom
        return sensitivity


class MorphologyOps(object):
    """
    Class that performs the morphological operations needed to get notably
    connected component. To be used in the evaluation
    """

    def __init__(self, binary_img, connectivity):
        self.binary_map = np.asarray(binary_img, dtype=np.int8)
        self.connectivity = connectivity

    def border_map(self):
        """
        Create the border map defined as the difference between the original image 
        and its eroded version

        :return: border
        """
        eroded = ndimage.binary_erosion(self.binary_map)
        border = self.binary_map - eroded
        return border

    def border_map2(self):
        """
        Creates the border for a 3D image
        :return:
        """
        west = ndimage.shift(self.binary_map, [-1, 0, 0], order=0)
        east = ndimage.shift(self.binary_map, [1, 0, 0], order=0)
        north = ndimage.shift(self.binary_map, [0, 1, 0], order=0)
        south = ndimage.shift(self.binary_map, [0, -1, 0], order=0)
        top = ndimage.shift(self.binary_map, [0, 0, 1], order=0)
        bottom = ndimage.shift(self.binary_map, [0, 0, -1], order=0)
        cumulative = west + east + north + south + top + bottom
        border = ((cumulative < 6) * self.binary_map) == 1
        return border

    def foreground_component(self):
        return ndimage.label(self.binary_map)

    def list_foreground_component(self):
        labels, _ = self.foreground_component()
        list_ind_lab = []
        list_volumes = []
        list_com = []
        list_values = np.unique(labels)
        for f in list_values:
            if f > 0:
                tmp_lab = np.where(
                    labels == f, np.ones_like(labels), np.zeros_like(labels)
                )
                list_ind_lab.append(tmp_lab)
                list_volumes.append(np.sum(tmp_lab))
                list_com.append(ndimage.center_of_mass(tmp_lab))
        return list_ind_lab, list_volumes, list_com


def border_distance(truth, pred, pixdim, connectivity=1):
        """
        This functions determines the map of distance from the borders of the
        prediction and the reference and the border maps themselves

        :return: distance_border_ref, distance_border_pred, border_ref,
        border_pred
        """
        border_truth = MorphologyOps(truth, connectivity).border_map()
        border_pred = MorphologyOps(pred, connectivity).border_map()
        oppose_truth = 1 - truth
        oppose_pred = 1 - pred
        distance_truth = ndimage.distance_transform_edt(
            1 - border_truth, sampling=pixdim
        )
        distance_pred = ndimage.distance_transform_edt(
            1 - border_pred, sampling=pixdim
        )
        distance_border_pred = border_truth * distance_pred
        distance_border_truth = border_pred * distance_truth
        return distance_border_truth, distance_border_pred, border_truth, border_pred


def normalised_surface_distance(truth, prediction, pixdim, overlap_ratio=0.1, tau=1):
        """
        Calculates the normalised surface distance (NSD) between prediction and reference
        using the distance parameter :math:`{\\tau}`

        Stanislav Nikolov, Sam Blackwell, Alexei Zverovitch, Ruheena Mendes, Michelle Livne, Jeffrey De Fauw, Yojan Patel,
        Clemens Meyer, Harry Askham, Bernadino Romera-Paredes, et al. 2021. Clinically applicable segmentation of head
        and neck anatomy for radiotherapy: deep learning algorithm development and validation study. Journal of Medical
        Internet Research 23, 7 (2021), e26151.

        .. math::

            NSD(A,B)^{(\\tau)} = \dfrac{|S_{A} \cap Bord_{B,\\tau}| + |S_{B} \cup Bord_{A,\\tau}|}{|S_{A}| + S_{B}}

        :return: NSD
        """
        if not np.any(truth) and not np.any(prediction):
            # Both reference and prediction are empty --> model learned correctly --> distance is 0
            return 0.0
        
        dist_ref, dist_pred, border_ref, border_pred = border_distance(truth, prediction, pixdim)
        reg_ref = np.where(
            dist_ref <= tau, np.ones_like(dist_ref), np.zeros_like(dist_ref)
        )
        reg_pred = np.where(
            dist_pred <= tau, np.ones_like(dist_pred), np.zeros_like(dist_pred)
        )
        numerator = np.sum(border_pred * reg_ref) + np.sum(border_ref * reg_pred)
        denominator = np.sum(border_ref) + np.sum(border_pred)
        return numerator / denominator