import os
from multiprocessing import Pool, Manager
from tqdm import tqdm
from nipype.interfaces.ants.segmentation import N4BiasFieldCorrection

def create_dir(path):
    """Create a directory if it doesn't exist."""
    if not os.path.isdir(path):
        os.makedirs(path)

def bias_field_correction_with_progress(src_dst_tuple, progress_queue):
    """Perform N4 Bias Field Correction and update progress."""
    src_path, dst_path = src_dst_tuple
    try:
        # Set up N4BiasFieldCorrection instance
        n4 = N4BiasFieldCorrection()
        n4.inputs.input_image = src_path
        n4.inputs.output_image = dst_path

        # Set up the parameters for the N4ITK algorithm
        n4.inputs.dimension = 3  # 3D image
        n4.inputs.n_iterations = [100, 100, 60, 40]  # Number of iterations at different scales
        n4.inputs.shrink_factor = 3  # Downsample factor
        n4.inputs.convergence_threshold = 1e-4  # Threshold for convergence
        n4.inputs.bspline_fitting_distance = 300  # Distance for B-spline fitting

        # Run the bias field correction process
        n4.run()

        # After successful bias field correction, delete the original file
        os.remove(src_path)

    except RuntimeError as e:
        print(f"Failed on: {src_path}. Error: {e}")

    # Update the progress queue
    progress_queue.put(1)

def gather_files(dir_name):
    """Gather all .nii files in a directory."""
    tasks = []
    for file_name in os.listdir(dir_name):
        if file_name.endswith('.nii'):
            # Full path for source and destination files
            src_file = os.path.join(dir_name, file_name)
            dst_file = os.path.join(dir_name, file_name.replace('.nii', '_N4_Bias_Corr.nii'))

            # Ensure the destination directory exists
            create_dir(os.path.dirname(dst_file))

            # Append the task (source, destination) tuple
            tasks.append((src_file, dst_file))
    return tasks

if __name__ == '__main__':
    # Directories containing images
    dirs = ['AD', 'CN']

    # Gather all tasks from all directories
    all_tasks = []
    for dir_name in dirs:
        all_tasks.extend(gather_files(dir_name))

    # Progress tracking
    total_files = len(all_tasks)
    print(f"Total files to process: {total_files}")

    # Use multiprocessing with a progress bar
    with Manager() as manager:
        progress_queue = manager.Queue()

        def track_progress_bar(queue, total):
            """Track progress using tqdm."""
            with tqdm(total=total, desc="Processing Files", unit="file") as pbar:
                for _ in range(total):
                    queue.get()
                    pbar.update(1)

        # Start the progress tracker in a separate process
        with Pool(processes=1) as tracker_pool:
            tracker = tracker_pool.apply_async(track_progress_bar, args=(progress_queue, total_files))

            # Process files in parallel
            with Pool(processes=os.cpu_count()) as pool:
                pool.starmap(bias_field_correction_with_progress, [(task, progress_queue) for task in all_tasks])

            tracker.get()  # Wait for the progress tracker to finish
