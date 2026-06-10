import json
import os
import argparse
from collections import OrderedDict

def generate_dataset_json(target_path, modalities, labels, dataset_name, release):
    """
    Generates a dataset.json file for nnU-Net v2 based on the folder content.
    """
    imagesTr_dir = os.path.join(target_path, "imagesTr")
    
    if not os.path.exists(imagesTr_dir):
        print(f"Error: Could not find {imagesTr_dir}. Check your path.")
        return

    # nnU-Net v2 looks for the file ending. Standard is .nii.gz
    # We strip the _0000.nii.gz suffix to get unique case identifiers
    train_identifiers = [f for f in os.listdir(imagesTr_dir) if f.endswith('.nii.gz')]
    train_identifiers = sorted(list(set([f[:-12] for f in train_identifiers])))
    
    # Build the JSON structure
    json_dict = OrderedDict()
    json_dict['name'] = dataset_name
    json_dict['description'] = "nnU-Net dataset automatically generated via script"
    json_dict['reference'] = "None"
    json_dict['licence'] = "None"
    json_dict['release'] = release
    
    # Channel names: { "0": "CT", "1": "MRI" }
    json_dict['channel_names'] = {str(i): name for i, name in enumerate(modalities)}
    
    # Labels: { "background": 0, "label_name": 1 }
    # Note: For nnU-Net v2, the format is {"name": index}
    label_dict = {"background": 0}
    for i, label_name in enumerate(labels, start=1):
        label_dict[label_name] = i
    json_dict['labels'] = label_dict
    
    json_dict['numTraining'] = len(train_identifiers)
    json_dict['file_ending'] = ".nii.gz"
    
    # Save to the root of the dataset folder
    output_file = os.path.join(target_path, "dataset.json")
    with open(output_file, 'w') as f:
        json.dump(json_dict, f, indent=4, sort_keys=False)

    print(f"--- Dataset.json Generated ---")
    print(f"Location: {output_file}")
    print(f"Cases found: {len(train_identifiers)}")
    print(f"Modalities: {json_dict['channel_names']}")
    print(f"Labels: {json_dict['labels']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dataset.json for nnU-Net v2")
    
    # Required Arguments
    parser.add_argument("-i", "--input", type=str, required=True, 
                        help="Path to the dataset root (containing imagesTr)")
    
    # Flexible Arguments
    parser.add_argument("--modalities", nargs='+', default=["CT"], 
                        help="List of modalities in order (e.g., --modalities CT MRI)")
    parser.add_argument("--labels", nargs='+', required=True, 
                        help="List of labels excluding background (e.g., --labels Liver Tumor)")
    parser.add_argument("--name", type=str, default="Dataset001_Task", 
                        help="Name of the dataset")
    parser.add_argument("--release", type=str, default="1.0", 
                        help="Version release string")

    args = parser.parse_args()

    generate_dataset_json(
        target_path=args.input,
        modalities=args.modalities,
        labels=args.labels,
        dataset_name=args.name,
        release=args.release
    )