# Automatic segmentation of spinal canal

This repo countains the code to perform inference with the spinal canal segmentation model, and the code to train it. 

# Requirements

If you want to perform only the inference you should use the [Spinal Cord Toolbox](https://spinalcordtoolbox.com/stable/) and follow the instructions [here](). 
Otherwise if you would rather work with the code, you should install nnUNetv2 by following the instructions [here](https://github.com/DIAGNijmegen/nnUNet_v2). 

## Warning
Whatever you do you should install SCT as it's needed for preprocessing of your data. 

# Inference

In order to perform inference you need to use SCT or download the model weights at [link]() and launch the inference using nnUNet.  

# Training 

In order to train the model in a similar manner as what was done in the paper you need to: 
Run the download_dataset.sh script: this script will read the `ressources/canal.json` file and automatically download the data for training and testing. 

```bash 
bash scripts/download_dataset.sh
```

## Warning
For it to work you need to modify `DATASETS_PATH` in  `ressources/canal.json` using your local configuration. 

After downloading the datasets you need to preprocess the data in a manner compatible with nnUNet by running: 
```bash 
bash scripts/prepare_datasets.sh 
```

After doing that you can start training using:
```bash 
bash scripts/train.sh
``` 