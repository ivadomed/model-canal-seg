"""
Evaluate nnUNet-like segmentation predictions, computing Dice scores globally
and by contrast (T1w, T2w, T2star).

Author: Pierre-Louis Benveniste (modified)
"""

import os
import numpy as np
import argparse
from pathlib import Path
import nibabel as nib
from tqdm import tqdm
from utils import dice_score


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", required=True, type=str)
    parser.add_argument("-l", required=True, type=str)
    parser.add_argument("-o", required=True, type=str)
    return parser.parse_args()


def get_contrast_from_name(name: str):
    """Extract contrast from file name."""
    name_lower = name.lower()
    if "t1w" in name_lower:
        return "T1w"
    if "t2w" in name_lower:
        return "T2w"
    if "t2star" in name_lower or "t2s" in name_lower:
        return "T2star"
    return "unknown"


def main():
    args = parse_args()
    pred_folder = Path(args.p)
    label_folder = Path(args.l)
    output_folder = Path(args.o)
    output_folder.mkdir(parents=True, exist_ok=True)

    predictions = list(pred_folder.rglob("*.nii.gz"))

    # Per-file dice
    dice_scores = {}

    # Per-contrast dice
    dice_by_contrast = {"T1w": [], "T2w": [], "T2star": [], "unknown": []}

    for pred in tqdm(predictions):
        label_path = label_folder / pred.name
        if not label_path.exists():
            print(f"⚠️ Warning: Missing label for {pred.name}")
            continue

        if not "-M" in label_path.name:
            print(f"⚠️ Warning: Label file {label_path.name} does not contain '-M', skipping.")
            continue

        pred_data = nib.load(str(pred)).get_fdata()
        label_data = nib.load(str(label_path)).get_fdata()

        # Dice score
        dice = dice_score(pred_data, label_data)
        dice_scores[pred.name] = dice

        # Contrast category
        contrast = get_contrast_from_name(pred.name)
        dice_by_contrast[contrast].append(dice)

    # Save per-file dice scores
    with open(output_folder / "dice_scores.txt", "w") as f:
        for key, value in dice_scores.items():
            f.write(f"{key}: {value}\n")

    # Save summary
    with open(output_folder / "scores_summary.txt", "w") as f:
        # Global
        all_dice = list(dice_scores.values())
        f.write(f"Global Dice: {np.mean(all_dice):.4f} ± {np.std(all_dice):.4f}\n\n")

        # Per contrast
        for contrast, values in dice_by_contrast.items():
            if len(values) == 0:
                f.write(f"{contrast}: No samples found\n")
            else:
                f.write(
                    f"{contrast}: {np.mean(values):.4f} ± {np.std(values):.4f} "
                    f"(n={len(values)})\n"
                )

    return None


if __name__ == "__main__":
    main()
