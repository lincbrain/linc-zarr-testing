from arraylake import Client
import os
import s3fs
import zarr
from zarr_constants import S3_ZARR_PATH, S3_BUCKET
from git_reproducibility import get_unique_identifier
from datetime import datetime


def print_event(event_name):
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{event_name}: {formatted_time}")


os.environ["ZARR_V3_EXPERIMENTAL_API"] = "1"

client = Client()
repo = client.get_repo("gablab/aaronkanzer")
print_event("Get Arraylake Client")

arraylake_branch_name = "march-8"
try:
    repo.new_branch(arraylake_branch_name)
except:
    print(f'Branch {arraylake_branch_name} already exists')

# repo.checkout(ref=arraylake_branch_name, for_writing=True)

## TODO: Write some instructions for how to go back in time and checkout a given commit in a given branch
# repo.checkout('65ddebeee0a8c739300e3feb', for_writing=True)
print_event("Checkout Branch")

zarr_group = repo.root_group
zarr_group.attrs['title'] = "Zarr Versioning Proof of Concept"
zarr_group.attrs['author'] = "Aaron Kanzer"

print_event("Checkout Zarr and Open")

old_value = repo.root_group.another_new_zarr_test[0, 0, :10, :10, :10]
print(repo.root_group.another_new_zarr_test[0, 0, :10, :10, :10])
repo.root_group.another_new_zarr_test[0, 0, :10, :10, :10] = repo.root_group.another_new_zarr_test[0, 0, :10, :10, :10] + 20
new_value = repo.root_group.another_new_zarr_test[0, 0, :10, :10, :10]

print_event(f"New subset value: {new_value} -- ")

repo.commit(f'{get_unique_identifier(arraylake_branch_name)} Old: {old_value}, New: {new_value}')

# Sample code to create a new grouping -- need to change group_name per run of script
# group_names = list(zarr_group)
# group_name = "friday-feb-25"
# if group_name not in group_names:
#     new_array = zarr_group.create(
#         group_name,
#         shape=(1, 1, 1024, 1024, 17574),
#         chunks=(1, 1, 256, 256, 256),
#         dtype="uint16",
#         fill_value=0
#     )

#### More sample code for a more robust alteration
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
