from arraylake import Client

client = Client()
repo = client.get_repo("gablab/aaron-kanzer-cli-test")

repo.new_branch("aaron-sample-branch")
repo.checkout(ref="aaron-sample-branch")

import numpy as np
atlantic_group = repo.root_group.create_group("atlantic_1")
atlantic_group.attrs["title"] = "Atlantic Ocean"
temperature_array = atlantic_group.create(
    "temperature",
    shape=100, chunks=10, dtype="f4", fill_value=np.nan
)
temperature_array.attrs["name"] = "Atlantic Ocean Temperature"
temperature_array.attrs["units"] = "degrees Celsius"

commit_id = repo.commit("trying a new branch")


# root = repo.root_group
# varnames = {
#     "atm": ["pr", "co2", "tas"],
#     "land": ["rootd", "tasmin", "tasmax"],
# }
#
# attrs = {
#     "pr": {"standard_name": "precipitation_flux"},
#     "co2": {"standard_name": "mole_fraction_of_carbon_dioxide_in_air"},
#     "tas": {"standard_name": "air_temperature", "cell_methods": "time:mean"},
#     "tasmin": {"standard_name": "air_temperature", "cell_methods": "time:min"},
#     "tasmax": {"standard_name": "air_temperature", "cell_methods": "time:max"},
#     "rootd": {"standard_name": "root_depth", "units": "m"},
# }
#
# for mip in ["CMIP", "ScenarioMIP"]:
#     for model in ["model1", "model2"]:
#         for experiment_id in ["historical"]:
#             for stream in ["atm_daily", "land_daily", "land_monthly"]:
#                 if mip == "ScenarioMIP" and stream != "atm_daily":
#                     continue
#                 for grid_id in ["native", "latlon"]:
#                     if grid_id == "latlon" and model == "model2":
#                         continue
#                     frequency = "mon" if "mon" in stream else "day"
#                     component, _ = stream.split("_")
#                     path = f"{mip}/{model}/{experiment_id}/{stream}/{grid_id}"
#                     group = root.create_group(path, overwrite=True)
#
#                     for variable in varnames[component]:
#                         path = f"{mip}/{model}/{experiment_id}/{stream}/{grid_id}/{variable}"
#                         array = root.create_dataset(
#                             path,
#                             shape=(4, 64, 128),
#                             overwrite=True,
#                             fill_value=np.nan,
#                             dtype=np.float64,
#                         )
#                         if variable in attrs:
#                             array.attrs.update(attrs[variable])
#                             array.attrs.update(
#                                 {
#                                     "frequency": frequency,
#                                     "grid": grid_id,
#                                     "experiment_id": experiment_id,
#                                     "_ARRAY_DIMENSIONS": ["time", "nlat", "nlon"]
#                                     if grid_id == "native"
#                                     else ["time", "latitude", "longitude"],
#                                 }
#                             )
# repo.commit("demo dataset commit")

# print(repo.tree())
# repo.commit("My third commit")

# import xarray as xr
#
# air_temp = xr.tutorial.open_dataset("air_temperature").chunk("1mb")
# rasm = xr.tutorial.open_dataset("rasm").chunk("1mb")
#
# air_temp.to_zarr(repo.store, group='air_temperature', zarr_version=3, mode='w')
# rasm.to_zarr(repo.store, group='rasm', zarr_version=3, mode='w')
#

