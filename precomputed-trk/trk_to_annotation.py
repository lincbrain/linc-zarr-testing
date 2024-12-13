import numpy as np
import os
import struct
from dipy.io.streamline import load_trk
import nibabel as nib
import psutil
import time
from nibabel.affines import apply_affine
import json


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

# Function to log resource utilization
def log_resource_usage(stage):
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"[{stage}] CPU Usage: {cpu_percent}%")
    print(f"[{stage}] Memory Usage: {memory.percent}% ({memory.used / (1024**2):.2f} MB used / {memory.total / (1024**2):.2f} MB total)")

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
spatial_dir = os.path.join(output_dir, 'spatial0')
by_id_dir = os.path.join(output_dir, 'annotations_by_id')
os.makedirs(spatial_dir, exist_ok=True)
os.makedirs(by_id_dir, exist_ok=True)

# Define grid shape and chunk size dynamically
grid_density = 6  # Number of chunks along each axis
chunk_size = [dim // grid_density for dim in volume_shape]
grid_shape = [grid_density] * 3

# Create binary spatial files
spatial_index = {f"{x}_{y}_{z}": [] for x in range(grid_shape[0]) for y in range(grid_shape[1]) for z in range(grid_shape[2])}

annotation_count = 0  # Track total annotation count

for streamline_idx, streamline in enumerate(all_streamlines):
    streamline = np.array(streamline)

    # Convert streamline coordinates to NIfTI voxel space
    streamline_voxels = apply_affine(inverse_affine, streamline)
    streamline_voxels = np.clip(streamline_voxels, 0, np.array(volume_shape) - 1)  # Clip to bounds

    # Divide streamline into line segments
    for i in range(len(streamline_voxels) - 1):
        start = streamline_voxels[i]
        end = streamline_voxels[i + 1]

        # Determine grid cell
        cell_x = int(start[0] // chunk_size[0])
        cell_y = int(start[1] // chunk_size[1])
        cell_z = int(start[2] // chunk_size[2])
        cell_key = f"{cell_x}_{cell_y}_{cell_z}"

        # Create annotation data
        annotation = {
            "id": annotation_count,
            "pointA": start.tolist(),
            "pointB": end.tolist(),
        }

        # Save annotation to `by_id`
        by_id_file = os.path.join(by_id_dir, str(annotation_count))
        with open(by_id_file, 'w') as f:
            json.dump(convert_to_native(annotation), f)

        # Add annotation ID to spatial index
        spatial_index[cell_key].append(annotation_count)
        annotation_count += 1

# Save spatial index files in binary format
for cell_key, annotation_ids in spatial_index.items():
    cell_file = os.path.join(spatial_dir, cell_key)
    with open(cell_file, 'wb') as f:
        if len(annotation_ids) == 0:
            # Write an empty chunk
            f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')  # countLow=0, countHigh=0
        else:
            # Write number of annotations as countLow and countHigh
            f.write(struct.pack('<II', len(annotation_ids), 0))  # Little-endian uint32
            for annotation_id in annotation_ids:
                f.write(struct.pack('<Q', annotation_id))  # Write annotation ID as uint64
    print(f"Saved spatial index for {cell_key} with {len(annotation_ids)} annotations.")

# Save info file
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
            "limit": 50000
        }
    ]
}
info_file_path = os.path.join(output_dir, 'info')
with open(info_file_path, 'w') as f:
    json.dump(convert_to_native(info), f)
print(f"Saved info file at {info_file_path}")

log_resource_usage("After Formatting Annotations")

# Final metrics
end_time = time.time()
print(f"Script completed in {end_time - start_time:.2f} seconds.")
log_resource_usage("Final Resource Utilization")