# Automatic segmentation of spinal canal

![Segmentation on whole-spine image viewed on axial and sagittal planes](https://github.com/ivadomed/model-canal-seg/blob/abels/assets/canal%20seg%20asset%20video.zip)

This repository contains the code for deep learning-based segmentation of the spinal canal. 
The code is based on the [nnUNet framework](https://github.com/MIC-DKFZ/nnUNet).

The spinal canal as here been defined using the anatomical boundary of the dural sac. The model has been trained to segment both spinal cord and CSF inside the dural sac. 

## Model Overview

The model is a 3d nnUNet which was trained specifically on T2-weighted images and provides and provides a segmentation of the spinal canal. 

## How to use the model

### Install dependencies

- [Spinal Cord Toolbox (SCT) v6.5](https://github.com/spinalcordtoolbox/spinalcordtoolbox/releases/tag/6.2) or higher -- follow the installation instructions [here](https://github.com/spinalcordtoolbox/spinalcordtoolbox?tab=readme-ov-file#installation)
- [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) 
- Python

Once the dependencies are installed, download the latest rootlets model:

```bash
sct_deepseg -install-task seg_spinal_rootlets_t2w
```

### Getting the rootlet segmentation

To segment a single image, run the following command: 

```bash
sct_deepseg -i <INPUT> -o <OUTPUT> -task canal_t2w 
```

For example:

```bash
sct_deepseg -i sub-001_T2w.nii.gz -o sub-001_T2w_canal_seg.nii.gz -task canal_t2w 