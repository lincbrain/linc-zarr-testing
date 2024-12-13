import numpy as np
import os
import json
from dipy.io.streamline import load_trk
import nibabel as nib
import psutil
import time
from nibabel.affines import apply_affine

# Function to log resource utilization
def log_resource_usage(stage):
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"[{stage}] CPU Usage: {cpu_percent}%")
    print(f"[{stage}] Memory Usage: {memory.percent}% ({memory.used / (1024**2):.2f} MB used / {memory.total / (1024**2):.2f} MB total)")

# Convert data to JSON serializable format
def convert_to_native(data):
    if isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, (np.float32, np.float64)):
        return float(data)
    elif isinstance(data, (np.int32, np.int64)):
        return int(data)
    elif isinstance(data, dict):
        return {k: convert_to_native(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_native(v) for v in data]
    else:
        return data

# Start timing
start_time = time.time()

# Load NIfTI file to get spatial properties
nifti_file = 'sub-I58_sample-hemi_desc-preproc_dwi_FA.nii.gz'
nifti = nib.load(nifti_file)
voxel_size = nifti.header.get_zooms()[:3]  # Get voxel dimensions
volume_shape = nifti.shape[:3]  # Volume dimensions
affine = nifti.affine  # Affine transformation matrix
inverse_affine = np.linalg.inv(affine)  # Inverse affine
print(f"Voxel size: {voxel_size}, Volume shape: {volume_shape}, Affine: \n{affine}")

# Load streamlines
trk_file = 'sub-I58_sample-hemi_desc-CSD_tractography.smalltest.trk'
print("Loading streamlines...")
sft = load_trk(trk_file, reference='same')
all_streamlines = sft.streamlines
print(f"Total number of streamlines: {len(all_streamlines)}")
log_resource_usage("After Loading Streamlines")

# Output directory
output_dir = './precomputed_annotations'
os.makedirs(output_dir, exist_ok=True)
annotations_by_id_dir = os.path.join(output_dir, 'annotations_by_id')
spatial_dir = os.path.join(output_dir, 'spatial0')
os.makedirs(annotations_by_id_dir, exist_ok=True)
os.makedirs(spatial_dir, exist_ok=True)

# Define grid shape and chunk size dynamically
grid_density = 4  # Number of chunks along each axis
chunk_size = [dim // grid_density for dim in volume_shape]
grid_shape = [grid_density] * 3

# Define the info file
info = {
    "@type": "neuroglancer_annotations_v1",
    "dimensions": {
        "x": [voxel_size[0], "mm"],
        "y": [voxel_size[1], "mm"],
        "z": [voxel_size[2], "mm"]
    },
    "lower_bound": [0, 0, 0],
    "upper_bound": list(volume_shape),
    "annotation_type": "LINE",
    "properties": [],
    "relationships": [],
    "by_id": {
        "key": "annotations_by_id"
    },
    "spatial": [
        {
            "key": "spatial0",
            "grid_shape": grid_shape,
            "chunk_size": chunk_size,
            "limit": 50000  # Increased to handle larger annotations
        }
    ]
}
# Save info file
with open(os.path.join(output_dir, 'info'), 'w') as f:
    json.dump(convert_to_native(info), f)

# Initialize variables for spatial index
spatial_index = {f"{x}_{y}_{z}": [] for x in range(grid_shape[0]) for y in range(grid_shape[1]) for z in range(grid_shape[2])}

# Create annotations
streamline_id = 1

for streamline_idx, streamline in enumerate(all_streamlines):
    streamline = np.array(streamline)

    # Convert streamline coordinates to NIfTI voxel space
    streamline_voxels = apply_affine(inverse_affine, streamline)
    streamline_voxels = np.clip(streamline_voxels, 0, np.array(volume_shape) - 1)  # Clip to bounds

    # Debug: Print transformed points for the first 5 streamlines
    if streamline_idx < 5:  # Print for first 5 streamlines only
        print(f"Streamline {streamline_idx + 1} (first point physical): {streamline[0]}")
        print(f"Streamline {streamline_idx + 1} (first point voxel): {streamline_voxels[0]}")

    # Divide streamline into line segments
    for i in range(len(streamline_voxels) - 1):
        start = streamline_voxels[i]
        end = streamline_voxels[i + 1]

        # Determine grid cell
        cell_x = int(start[0] // chunk_size[0])
        cell_y = int(start[1] // chunk_size[1])
        cell_z = int(start[2] // chunk_size[2])
        cell_key = f"{cell_x}_{cell_y}_{cell_z}"

        # Add annotation to spatial index
        spatial_index[cell_key].append({
            "id": streamline_id,
            "pointA": start.tolist(),
            "pointB": end.tolist()
        })

        # Save annotation by ID
        annotation = {
            "id": streamline_id,
            "pointA": start.tolist(),
            "pointB": end.tolist()
        }
        with open(os.path.join(annotations_by_id_dir, str(streamline_id)), 'w') as f:
            json.dump(convert_to_native(annotation), f)

        streamline_id += 1

# Save spatial index files
for cell_key, annotations in spatial_index.items():
    cell_file = os.path.join(spatial_dir, cell_key)
    with open(cell_file, 'w') as f:
        json.dump({"annotations": [a["id"] for a in annotations]}, f)

log_resource_usage("After Formatting Annotations")

# Final metrics
end_time = time.time()
print(f"Script completed in {end_time - start_time:.2f} seconds.")
log_resource_usage("Final Resource Utilization")