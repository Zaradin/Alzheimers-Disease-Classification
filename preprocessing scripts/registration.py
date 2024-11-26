import os
import subprocess
import gzip
import shutil
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Paths to directories and reference file
ad_dir = "AD"
cn_dir = "CN"
reference_file = "MNI152_T1_1mm.nii"

# Function to extract .nii from .gz file
def extract_gz_file(gz_file_path):
    # Determine the output file name
    extracted_file_path = gz_file_path.replace(".gz", "")
    
    # Extract the .gz file
    with gzip.open(gz_file_path, 'rb') as gz_file:
        with open(extracted_file_path, 'wb') as extracted_file:
            shutil.copyfileobj(gz_file, extracted_file)
    
    # Remove the .gz file after successful extraction
    os.remove(gz_file_path)
    return extracted_file_path

# Function to register a single .nii file
def register_file(file_path, ref_file, output_dir):
    # Prepare the output file path
    base_name = os.path.basename(file_path)
    output_gz_file = os.path.join(output_dir, base_name.replace(".nii", "_reg.nii.gz"))
    
    # Command to run flirt
    command = [
        "flirt", 
        "-in", file_path,
        "-ref", ref_file,
        "-out", output_gz_file,
        "-bins", "256",
        "-cost", "corratio",
        "-searchrx", "-90", "90",
        "-searchry", "-90", "90",
        "-searchrz", "-90", "90",
        "-dof", "12",
        "-interp", "spline"
    ]
    
    # Run the command
    subprocess.run(command, check=True)
    
    # Extract the .nii file from the .gz output
    extracted_file = extract_gz_file(output_gz_file)
    
    # Remove the original input file
    os.remove(file_path)
    
    return extracted_file

# Function to process all .nii files in a directory
def process_directory(input_dir, ref_file):
    # Create a list of .nii files in the directory
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(".nii")]
    output_dir = input_dir  # Keep output files in the same directory

    # Use multithreading to process files in parallel
    with ThreadPoolExecutor() as executor:
        list(tqdm(executor.map(lambda f: register_file(f, ref_file, output_dir), files), total=len(files), desc=f"Processing {input_dir}"))

# Main script
if __name__ == "__main__":
    process_directory(ad_dir, reference_file)
    process_directory(cn_dir, reference_file)
