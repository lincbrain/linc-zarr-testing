from arraylake import Client
import os
import numpy as np

os.environ["ZARR_V3_EXPERIMENTAL_API"] = "1"

# client = Client()
# repo = client.get_repo("gablab/aaronkanzer")
#
# # repo.checkout(ref="zarr-test")
# zarr_group = repo.root_group.create_group(name="zarr-group")
# zarr_group.attrs['title'] = "Zarr Demo"

import s3fs
import zarr

# Initialize the S3 file system
s3 = s3fs.S3FileSystem(anon=False)  # Set anon=False if you need authentication

# Specify your S3 bucket and Zarr store path
bucket = 'arraylake-sandbox'
zarr_store_path = 'zarr/9f342f9b-e589-4bbc-8ebd-665d0123af77/'

# Create a Zarr store using s3fs
store = s3fs.S3Map(root=f'{bucket}/{zarr_store_path}', s3=s3, check=False)

# Or open the Zarr store using zarr directly for simple arrays
zarr_group = zarr.open(store, mode='r')

dataset = zarr_group["0"]

# Here we're reading a 10x10x10 block from the start of the dataset
data_subset = dataset[0, 0, :10, :10, :10]

# Iterate over the subset
for element in data_subset:
    print(element)
