from arraylake import Client
import os
import s3fs
import zarr
from zarr_constants import S3_ZARR_PATH, S3_BUCKET
from git_reproducibility import get_unique_identifier
from datetime import datetime

current_time = datetime.now()

os.environ["ZARR_V3_EXPERIMENTAL_API"] = "1"

first_timestamp_str = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}.{int(current_time.microsecond / 1000)}"
client = Client()
repo = client.get_repo("gablab/aaronkanzer")
next_timestamp_str = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}.{int(current_time.microsecond / 1000)}"

# repo.checkout(ref="zarr-test")
zarr_group = repo.root_group
zarr_group.attrs['title'] = "Zarr Versioning Proof of Concept"
zarr_group.attrs['author'] = "Aaron Kanzer"

# Initialize the S3 file system
s3 = s3fs.S3FileSystem(anon=False)  # export AWS_PROFILE=mcgovern

# Create a Zarr store using s3fs
store = s3fs.S3Map(root=f'{S3_BUCKET}/{S3_ZARR_PATH}', s3=s3, check=False)  # <fsspec.mapping.FSMap object at 0x11da3f4f0>
zarr_store = zarr.open(store, mode='a')   # <zarr.hierarchy.Group '/'>

zarr_array_dataset = zarr_store["0"]  # <zarr.core.Array '/0' (1, 1, 2048, 2048, 17574) uint16>
subset = zarr_array_dataset[0, 0, :10, :10, :10]
old_value = subset[0, 0, 1]
subset[0, 0, 1] = subset[0, 0, 1] + 10
new_value = subset[0, 0, 1]
# group_names = list(zarr_group)
# group_name = "friday-feb-23"
# if group_name not in group_names:
#     new_array = zarr_group.create(
#         group_name,
#         shape=(1, 1, 1024, 1024, 17574),
#         chunks=(1, 1, 256, 256, 256),
#         dtype="uint16",
#         fill_value=0
#     )


repo.commit(f'{get_unique_identifier()} Old: {old_value}, New: {new_value}')

# Get array to alter
# new_array = zarr_group.get("new_zarr_test")
#
# for element in new_array:
#     print(element)
#     break
#
# first_chunk = new_array[0, 0, :2048, :2048, :2048]
#
# # Increment each value in the chunk by 1
# first_chunk += 1
#
# # Write the updated values back to the first chunk of the array
# new_array[0, 0, :2048, :2048, :2048] = first_chunk
#
#
# new_array.attrs['title'] = "Test for meeting"
#
# repo.commit("Add +1 to each value in the Zarr array")
#
# # Iterate over the subset
# for element in new_array:
#     print(element)
#     break
