# Automatic segmentation of spinal canal

This repository contains the code for deep learning-based segmentation of the spinal canal. 
The code is based on the [nnUNet framework](https://github.com/MIC-DKFZ/nnUNet).

The spinal canal as here been defined using the anatomical boundary of the dural sac. The model has been trained to segment both spinal cord and CSF inside the dural sac. 

## Model Overview

The model is a 3d nnUNet which was trained specifically on T2-weighted images and provides and provides a segmentation of the spinal canal. 