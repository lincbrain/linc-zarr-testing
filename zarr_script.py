from arraylake import Client
import os
import s3fs
import zarr

os.environ["ZARR_V3_EXPERIMENTAL_API"] = "1"

client = Client()
repo = client.get_repo("gablab/aaronkanzer")

# Specify your S3 bucket and Zarr store path
bucket = 'arraylake-sandbox'
zarr_store_path = 'zarr/9f342f9b-e589-4bbc-8ebd-665d0123af77/'

# repo.checkout(ref="zarr-test")
zarr_group = repo.root_group
zarr_group.attrs['title'] = "Zarr Demo"
zarr_group.attrs['author'] = "Aaron"

# Initialize the S3 file system
s3 = s3fs.S3FileSystem(anon=False)  # Set anon=False if you need authentication

# Create a Zarr store using s3fs
store = s3fs.S3Map(root=f'{bucket}/{zarr_store_path}', s3=s3, check=False)

# Or open the Zarr store using zarr directly for simple arrays
zarr_store = zarr.open(store, mode='a')

# Use part for data example
dataset = zarr_store["0"]  # <zarr.core.Array '/0' (1, 1, 2048, 2048, 17574) uint16>

# Ran initially
# new_array = zarr_group.create(
#     "new_zarr_test",  # The name of the new dataset you're creating
#     shape=(1, 1, 2048, 2048, 17574),  # The shape of the new dataset
#     chunks=(1, 1, 256, 256, 256),  # The chunk size for the new dataset, adjust as needed
#     dtype="uint16",  # Data type, matching 'uint16' as in your described array
#     fill_value=0  # Fill value, using 0 as a sensible default for uint16 data
# )

# Get array to alter
new_array = zarr_group.get("new_zarr_test")

for element in new_array:
    print(element)
    break

# Define the chunk size for processing; you might adjust this based on your available memory
chunk_size = (1, 1, 256, 256, 256)  # Example chunk size, adjust as needed


new_array.attrs['title'] = "Test for meeting"

repo.commit("Add +1 to each value in the Zarr array")

# Iterate over the subset
for element in new_array:
    print(element)
    break
