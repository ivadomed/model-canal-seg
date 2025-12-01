import os
import argparse
import SimpleITK as sitk
import numpy as np
from scipy.ndimage import label


def keep_largest_connected_component_array(seg):
    seg_bin = (seg > 0).astype(np.uint8)
    labeled, num_labels = label(seg_bin)

    if num_labels == 0:
        return seg_bin  # no components found

    component_sizes = np.bincount(labeled.ravel())
    component_sizes[0] = 0  # ignore background

    largest_id = np.argmax(component_sizes)
    lcc = (labeled == largest_id).astype(np.uint8)

    return lcc


def process_folder(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    nii_files = [f for f in os.listdir(input_dir) if f.endswith(".nii.gz")]

    if not nii_files:
        print("No .nii.gz files found in input directory.")
        return

    for filename in nii_files:
        in_path = os.path.join(input_dir, filename)
        out_path = os.path.join(output_dir, filename)

        print(f"Processing: {filename}")

        seg_itk = sitk.ReadImage(in_path)
        seg = sitk.GetArrayFromImage(seg_itk)

        lcc = keep_largest_connected_component_array(seg)

        out_itk = sitk.GetImageFromArray(lcc)
        out_itk.CopyInformation(seg_itk)
        sitk.WriteImage(out_itk, out_path)

    print(f"\nDone! Output saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Keep only the largest connected component of NIfTI segmentation files."
    )

    parser.add_argument(
        "--input-dir", type=str, required=True,
        help="Folder containing .nii.gz files to process."
    )
    parser.add_argument(
        "--output-dir", type=str, required=True,
        help="Where processed files will be saved."
    )

    args = parser.parse_args()

    process_folder(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
