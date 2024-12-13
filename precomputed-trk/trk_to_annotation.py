import numpy as np
import os
import struct
from dipy.io.streamline import load_trk
import nibabel as nib
import psutil
import time
from nibabel.affines import apply_affine
import json
from concurrent.futures import ThreadPoolExecutor


def convert_to_native(data):
    """Convert data to JSON serializable format."""
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


def log_resource_usage(stage):
    """Log resource utilization."""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"[{stage}] CPU Usage: {cpu_percent}%")
    print(f"[{stage}] Memory Usage: {memory.percent}% "
          f"({memory.used / (1024 ** 2):.2f} MB used / {memory.total / (1024 ** 2):.2f} MB total)")


def calculate_orientation(pointA, pointB):
    """Calculate the orientation vector between two points."""
    vector = np.array(pointB) - np.array(pointA)
    norm = np.linalg.norm(vector)
    return (vector / norm).tolist() if norm > 0 else [0, 0, 0]


def process_streamline(streamline_idx, streamline, inverse_affine, volume_shape, chunk_size, spatial_index, by_id_dir):
    """Process a single streamline into annotations."""
    streamline = np.array(streamline)
    streamline_voxels = apply_affine(inverse_affine, streamline)

    if not np.isfinite(streamline_voxels).all():
        print(f"Warning: Non-finite values found in streamline {streamline_idx}")
        return 0

    streamline_voxels = np.clip(streamline_voxels, 0, np.array(volume_shape) - 1)

    annotation_count = 0
    for i in range(len(streamline_voxels) - 1):
        start = streamline_voxels[i]
        end = streamline_voxels[i + 1]
        cell_x = int(start[0] // chunk_size[0])
        cell_y = int(start[1] // chunk_size[1])
        cell_z = int(start[2] // chunk_size[2])
        cell_key = f"{cell_x}_{cell_y}_{cell_z}"

        annotation_id = streamline_idx * 10000 + i  # Unique ID for each annotation
        annotation = {
            "id": annotation_id,
            "pointA": start.tolist(),
            "pointB": end.tolist(),
            "properties": {"orientation": calculate_orientation(start, end)}
        }

        by_id_file = os.path.join(by_id_dir, str(annotation_id))
        with open(by_id_file, 'w') as f:
            json.dump(convert_to_native(annotation), f)

        spatial_index[cell_key].append(annotation_id)
        annotation_count += 1

    return annotation_count


def main():
    start_time = time.time()
    nifti_file = 'sub-I58_sample-hemi_desc-preproc_dwi_FA.nii.gz'
    nifti = nib.load(nifti_file)
    voxel_size = nifti.header.get_zooms()[:3]
    volume_shape = nifti.shape[:3]
    affine = nifti.affine
    inverse_affine = np.linalg.inv(affine)

    print(f"Voxel size: {voxel_size}, Volume shape: {volume_shape}, Affine: \n{affine}")

    trk_file = 'sub-I58_sample-hemi_desc-CSD_tractography.smalltest.trk'
    print("Loading streamlines...")
    sft = load_trk(trk_file, reference='same')
    all_streamlines = sft.streamlines
    print(f"Total number of streamlines: {len(all_streamlines)}")
    log_resource_usage("After Loading Streamlines")

    output_dir = './precomputed_annotations'
    os.makedirs(output_dir, exist_ok=True)
    spatial_dir = os.path.join(output_dir, 'spatial0')
    by_id_dir = os.path.join(output_dir, 'annotations_by_id')
    os.makedirs(spatial_dir, exist_ok=True)
    os.makedirs(by_id_dir, exist_ok=True)

    grid_density = 6
    chunk_size = [dim // grid_density for dim in volume_shape]
    grid_shape = [grid_density] * 3

    spatial_index = {f"{x}_{y}_{z}": [] for x in range(grid_shape[0]) for y in range(grid_shape[1]) for z in
                     range(grid_shape[2])}

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(
            process_streamline,
            range(len(all_streamlines)),
            all_streamlines,
            [inverse_affine] * len(all_streamlines),
            [volume_shape] * len(all_streamlines),
            [chunk_size] * len(all_streamlines),
            [spatial_index] * len(all_streamlines),
            [by_id_dir] * len(all_streamlines)
        )
    total_annotations = sum(results)

    for cell_key, annotation_ids in spatial_index.items():
        cell_file = os.path.join(spatial_dir, cell_key)
        with open(cell_file, 'wb') as f:
            f.write(struct.pack('<II', len(annotation_ids), 0))
            for annotation_id in annotation_ids:
                f.write(struct.pack('<Q', annotation_id))
        print(f"Saved spatial index for {cell_key} with {len(annotation_ids)} annotations.")

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
        "by_id": {"key": "annotations_by_id"},
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
    print(f"Total annotations: {total_annotations}")
    print(f"Script completed in {time.time() - start_time:.2f} seconds.")
    log_resource_usage("Final Resource Utilization")


if __name__ == "__main__":
    main()