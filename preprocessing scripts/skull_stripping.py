import os
import subprocess
import gzip
import shutil
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Paths to directories
ad_dir = "AD"
cn_dir = "CN"

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

# Function to apply skull stripping to a single .nii file
def skull_strip_file(file_path, output_dir):
    # Prepare the output file path
    base_name = os.path.basename(file_path)
    output_gz_file = os.path.join(output_dir, base_name.replace(".nii", "_skull_stripped.nii.gz"))
    
    # Command to run bet
    command = [
        "bet", 
        file_path,
        output_gz_file,
        "-R",
        "-f", "0.3",
        "-g", "0"
    ]
    
    # Run the command
    subprocess.run(command, check=True)
    
    # Extract the .nii file from the .gz output
    extracted_file = extract_gz_file(output_gz_file)
    
    # Remove the original input file
    os.remove(file_path)
    
    return extracted_file

# Function to process all .nii files in a directory
def process_directory(input_dir):
    # Create a list of .nii files in the directory
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(".nii")]
    output_dir = input_dir  # Keep output files in the same directory

    # Use multithreading to process files in parallel
    with ThreadPoolExecutor() as executor:
        list(tqdm(executor.map(lambda f: skull_strip_file(f, output_dir), files), total=len(files), desc=f"Processing {input_dir}"))

# Main script
if __name__ == "__main__":
    process_directory(ad_dir)
    process_directory(cn_dir)
