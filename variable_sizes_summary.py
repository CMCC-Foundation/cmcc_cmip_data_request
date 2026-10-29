#!/usr/bin/env python
"""
CMCC CMIP7 Selected Variables Volume Calculator.

Reads 'dr-cmip7-full/cmcc_data_selected.csv', calculates estimated annual 
data volume (GB/year) per variable, and prints a formatted summary table by realm.
"""

import csv
import math
import os, sys
import re
import warnings
from collections import defaultdict

# --------------------------------------------------------------------------- #
# Integrated Volume Calculation Core                                          #
# --------------------------------------------------------------------------- #
SPATIAL_DEFAULTS = {
    "atmos": (48600, 1, 58),
    "land": (48600, 1, 1),
    "ocean": (360, 291, 75),
    "ocnBgchem": (360, 291, 75),
    "seaIce": (360, 291, 1),
}


OTHER_DIMS = {
    "gridlatitude": 291, 
    "rho": 75, "sdepth": 20, "soilpools": 5, "spectband": 10,
    "alevel": 58, "alevhalf": 59, "olevel": 75, "olevhalf": 75,
}


def parse_time_steps(frequency):
    """Converts CMIP7 frequency strings into total timesteps per year."""
    freq = (frequency or "").lower().strip()
    if not freq:
        return 12

    if "subhr" in freq:
        m = re.search(r"(\d+)subhr", freq)
        mins = int(m.group(1)) if m else 30
        return int(365 * 24 * (60 / mins))
    if freq.endswith("hr") or "hr" in freq:
        m = re.search(r"(\d+)hr", freq)
        hrs = int(m.group(1)) if m else 1
        return int((365 * 24) / hrs)
    if "day" in freq or freq == "1d":
        return 365
    if "mon" in freq or freq == "1m":
        return 12
    if "yr" in freq or "dec" in freq:
        return 1
    if "fx" in freq:
        return 1

    return 12


def get_variable_size(var_info, dreq_dim_sizes, time_dims, realm="atmos", compression=1.0, return_gb=True):
    """
    Computes annual data volume for a single variable.

    Parameters:
        var_info (dict): Variable record containing 'dimensions', 'frequency', etc.
        dreq_dim_sizes (dict): Dimension sizes extracted from the Data Request API.
        time_dims (dict): Map of temporal axis names.
        realm (str): Modeling realm for spatial grid fallback.
        compression (float): Data compression factor (default 1.0).
        return_gb (bool): Returns size in GB/year if True, else in bytes.
    """
    dims_str = var_info.get("dimensions", "") or ""
    dim_list = dims_str.split()

    nx, ny, nz_default = SPATIAL_DEFAULTS.get(realm, SPATIAL_DEFAULTS["atmos"])

    spatial_points = 1

    for d in dim_list:
        d_lower = d.lower()
        if re.match(r'^time', d):
            continue
        elif d == 'latitude': 
            spatial_points = spatial_points * ny
        elif d == 'longitude':
            spatial_points = spatial_points * nx
        elif d in dreq_dim_sizes:
            other_dim = dreq_dim_sizes[d]
            if isinstance(other_dim, str):
                if d in OTHER_DIMS.keys():
                    other_dim = OTHER_DIMS[d]
                else:
                    print('cannot set dimension for ' + d )
                    sys.exit()
            spatial_points = spatial_points * other_dim

    freq = var_info.get("frequency", "")
    timesteps = parse_time_steps(freq)

    bytes_per_year = spatial_points * timesteps * 4 * compression

    if return_gb:
        return bytes_per_year / (1024.0 ** 3)
    return bytes_per_year


# --------------------------------------------------------------------------- #
# Data Request Dimension Extraction                                           #
# --------------------------------------------------------------------------- #
def extract_dreq_dimensions(version="v1.2.2.5"):
    """Extracts dimension sizes and temporal dimension mappings from the Data Request API."""
    import data_request_api.content.dreq_content as dc
    import data_request_api.query.dreq_query as dq

    time_dims = {}
    dreq_dim_sizes = {}

    dc.retrieve(version)
    content = dc.load(version)
    base = dq.create_dreq_tables_for_request(content, version)

    table_keys = {str(k).lower(): k for k in base.keys()}

    coord_key = table_keys.get("coordinates and dimensions")
    temp_key = table_keys.get("temporal shape")
    freq_key = table_keys.get("cmip7 frequency") or table_keys.get("frequency")
    spat_key = table_keys.get("spatial shape")

    if all([coord_key, temp_key, freq_key, spat_key]):
        dreq_tables = {
            "coordinates and dimensions": base[coord_key],
            "temporal shape": base[temp_key],
            "frequency": base[freq_key],
            "spatial shape": base[spat_key],
        }
        dreq_dim_sizes = dq.get_dimension_sizes(dreq_tables)

        coord_table = dreq_tables["coordinates and dimensions"]
        for rec in dreq_tables["temporal shape"].records.values():
            if hasattr(rec, "dimensions") and rec.dimensions:
                link = rec.dimensions[0]
                try:
                    dim_rec = coord_table.get_record(link) if hasattr(coord_table, "get_record") else coord_table.records.get(link)
                    dim_name = getattr(dim_rec, "name", "None")
                except Exception:
                    dim_name = "None"
            else:
                dim_name = "None"
            time_dims[dim_name] = getattr(rec, "name", "None")

    return dreq_dim_sizes, time_dims


# --------------------------------------------------------------------------- #
# Main Processing Workflow                                                    #
# --------------------------------------------------------------------------- #
def main():
    csv_file = os.path.join("dr-cmip7-full", "cmcc_data_selected.csv")
    dreq_version = "v1.2.2.5"

    if not os.path.exists(csv_file):
        print(f"Error: Selected variables file not found at '{csv_file}'")
        return

    print(f"Loading Data Request dimension sizes ({dreq_version})...")
    dreq_dim_sizes, time_dims = extract_dreq_dimensions(version=dreq_version)

    realm_totals = defaultdict(float)
    realm_counts = defaultdict(int)
    total_volume = 0.0
    total_count = 0

    print(f"Reading '{csv_file}' and calculating variable sizes...\n")
    with open(csv_file, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            compound_name = row.get("compound_name", "").strip()
            realm = row.get("realm", "atmos").strip()

            if not compound_name:
                continue

            try:
                gb_per_year = get_variable_size(
                    var_info=row,
                    dreq_dim_sizes=dreq_dim_sizes,
                    time_dims=time_dims,
                    realm=realm,
                    compression=1.0,
                    return_gb=True,
                )
            except Exception as e:
                print(f"Warning: Failed size calculation for '{compound_name}' ({e})")
                gb_per_year = 0.0

            realm_totals[realm] += gb_per_year
            realm_counts[realm] += 1
            total_volume += gb_per_year
            total_count += 1

    # Print Summary Report
    print("=" * 60)
    print("         CMCC CMIP7 SELECTED VARIABLES SIZE SUMMARY         ")
    print("=" * 60)
    print(f"{'Realm':<15} | {'Var Count':<10} | {'Volume (GB/yr)':<18} | {'Volume (TB/yr)':<15}")
    print("-" * 60)

    for realm in sorted(realm_totals.keys()):
        gb = realm_totals[realm]
        tb = gb / 1024.0
        cnt = realm_counts[realm]
        print(f"{realm:<15} | {cnt:<10} | {gb:<18.2f} | {tb:<15.4f}")

    print("-" * 60)
    total_tb = total_volume / 1024.0
    print(f"{'TOTAL':<15} | {total_count:<10} | {total_volume:<18.2f} | {total_tb:<15.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
