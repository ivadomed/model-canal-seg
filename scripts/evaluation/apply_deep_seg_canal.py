import os
import subprocess
import argparse

def main(input_folder, output_folder, recursive=False):
    os.makedirs(output_folder, exist_ok=True)

    # Collect all files
    files_to_process = []
    for root, _, files in os.walk(input_folder):
        for f in files:
            if f.endswith((".nii", ".nii.gz")):
                file_path = os.path.join(root, f)
                files_to_process.append(file_path)
        if not recursive:
            break

    # Process each file
    for file_path in files_to_process:
        # Relative path
        rel_path = os.path.relpath(file_path, input_folder)
        rel_dir = os.path.dirname(rel_path)

        # Clean filename (remove "_0000" before extension)
        base = os.path.basename(file_path)
        if base.endswith(".nii.gz"):
            base_noext = base[:-7]  # remove .nii.gz
            ext = ".nii.gz"
        else:
            base_noext, ext = os.path.splitext(base)
        base_noext = base_noext.replace("_0000", "")
        out_filename = base_noext + ext

        # Full output path
        out_path = os.path.join(output_folder, rel_dir, out_filename)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        # Command
        cmd = [
            "sct_deepseg",
            "sc_canal_t2",
            "-i", file_path,
            "-o", out_path,
        ]

        print(f"Running: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error processing {file_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch run sct_deepseg sc_canal_t2 on all files in a folder.")
    parser.add_argument("-i", help="Folder containing input files")
    parser.add_argument("-o", default="deepseg_canal_results", help="Folder to save results")
    parser.add_argument("--recursive", action="store_true", help="Search recursively in subfolders")
    args = parser.parse_args()

    main(args.i, args.o, args.recursive)
