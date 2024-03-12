from arraylake import Client

client = Client()
repo = client.get_repo("gablab/aaron-kanzer-cli-test")

import xarray as xr

air_temp = xr.tutorial.open_dataset("air_temperature").chunk("1mb")
rasm = xr.tutorial.open_dataset("rasm").chunk("1mb")

air_temp.to_zarr(repo.store, group='air_temperature', zarr_version=3, mode='w')
rasm.to_zarr(repo.store, group='rasm', zarr_version=3, mode='w')

commit_id = repo.commit("My second commit 🥹")
