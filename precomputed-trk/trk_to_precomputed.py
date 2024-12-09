import numpy as np
from cloudvolume import CloudVolume
from cloudvolume.lib import mkdir
from dipy.io.streamline import load_trk
import psutil
import time

# Function to log resource utilization
def log_resource_usage(stage):
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"[{stage}] CPU Usage: {cpu_percent}%")
    print(f"[{stage}] Memory Usage: {memory.percent}% ({memory.used / (1024**2):.2f} MB used / {memory.total / (1024**2):.2f} MB total)")

# Start timing
start_time = time.time()

# Path to the .trk file
trk_file = 'sub-I58_sample-hemi_desc-CSD_tractography.smalltest.trk'

# Load streamlines and header
print("Loading streamlines...")
sft = load_trk(trk_file, reference='same')
log_resource_usage("After Loading Streamlines")

# Access all streamlines
all_streamlines = sft.streamlines

# Calculate memory usage for each streamline
streamline_memory = []
for streamline in all_streamlines:
    num_points = len(streamline)  # Number of points in the streamline
    memory_bytes = 4 + (num_points * 3 * 4)  # 4 bytes for integer + 3 floats per point
    streamline_memory.append(memory_bytes)

# Print metrics
total_memory_usage = sum(streamline_memory)
print(f"Total number of streamlines: {len(all_streamlines)}")
print(f"Total memory usage (bytes): {total_memory_usage} ({total_memory_usage / (1024**2):.2f} MB)")
log_resource_usage("After Calculating Streamline Memory")

# Output directory for precomputed format
output_dir = './precomputed_streamlines_1'
mkdir(output_dir)

# Define CloudVolume info
info = CloudVolume.create_new_info(
    num_channels=1,                     # Single channel for streamlines
    layer_type='segmentation',          # Use 'segmentation' or 'lines'
    data_type='float32',                # Coordinate data
    encoding='raw',                     # No compression for simplicity
    resolution=[1, 1, 1],               # Resolution in nanometers (adjust to your data)
    voxel_offset=[0, 0, 0],             # Starting point in the volume
    chunk_size=[64, 64, 64],            # Size of chunks
    volume_size=[1024, 1024, 1024],     # Full dataset size
)

vol = CloudVolume(f'file://{output_dir}', info=info, non_aligned_writes=True)
vol.commit_info()  # Write the info file
log_resource_usage("After Creating CloudVolume Info")

# Transform Streamlines into Chunks
volume_size = np.array([1024, 1024, 1024])  # Defined volume size
voxel_streamlines = []
for streamline in all_streamlines:
    streamline = np.array(streamline)  # Ensure NumPy array
    if streamline.ndim == 2:  # Ensure valid streamline
        voxel_streamline = streamline - np.min(streamline, axis=0)  # Normalize
        voxel_streamline = np.clip(voxel_streamline, 0, volume_size - 1)  # Clip to bounds
        voxel_streamlines.append(voxel_streamline)

# Initialize volume
vol[:, :, :] = 0  # Pre-fill chunks with zeros
log_resource_usage("After Pre-filling Volume")

# Write streamlines into chunks
print("Writing streamlines into chunks...")
for idx, streamline in enumerate(voxel_streamlines):
    for point in streamline:
        voxel_point = np.floor(point).astype(int)  # Convert to voxel coordinates
        x, y, z = np.clip(voxel_point, 0, volume_size - 1)  # Clip to bounds
        vol[x, y, z] = idx + 1  # Assign an ID to the streamline
log_resource_usage("After Writing Streamlines")

# End timing
end_time = time.time()
elapsed_time = end_time - start_time

# Final metrics
print(f"Script completed in {elapsed_time:.2f} seconds.")
log_resource_usage("Final Resource Utilization")