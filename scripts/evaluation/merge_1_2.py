import os
import nibabel as nib
import numpy as np
import argparse
from tqdm import tqdm

def merge_labels(input_folder, output_folder, target_label=1, source_label=2):
    """
    Merges source_label into target_label in all .nii.gz files in input_folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = [f for f in os.listdir(input_folder) if f.endswith('.nii.gz')]
    print(f"Found {len(files)} files. Merging label {source_label} into {target_label}...")

    for f in tqdm(files):
        img_path = os.path.join(input_folder, f)
        out_path = os.path.join(output_folder, f)

        # Load NIfTI file
        img = nib.load(img_path)
        data = img.get_fdata()

        # Perform the merge: everywhere it's source_label, make it target_label
        data[data == source_label] = target_label

        # Create new NIfTI image with same affine and header
        new_img = nib.Nifti1Image(data.astype(np.uint8), img.affine, img.header)
        
        # Save
        nib.save(new_img, out_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge labels in nnU-Net segmentation masks.")
    parser.add_argument("--input", type=str, required=True, help="Path to labelsTr folder")
    parser.add_argument("--output", type=str, required=True, help="Where to save merged masks")
    parser.add_argument("--target", type=int, default=1, help="The label ID to keep (default: 1)")
    parser.add_argument("--source", type=int, default=2, help="The label ID to merge into target (default: 2)")

    args = parser.parse_args()
    merge_labels(args.input, args.output, args.target, args.source)