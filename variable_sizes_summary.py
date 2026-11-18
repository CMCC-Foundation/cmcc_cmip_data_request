#!/usr/bin/env python
"""
CMCC CMIP7 Selected Variables Volume Calculator.

Reads configuration from a specified YAML file, derives the input directory from 
the configuration file's base name, calculates estimated annual data volume 
(GB/year) per variable, and prints a formatted summary table by realm.
"""

import argparse
import csv
import math
import os, sys
import re
import warnings
from collections import defaultdict
import yaml


# --------------------------------------------------------------------------- #
# Main Processing Workflow                                                    #
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(
        description="Calculate CMCC CMIP7 variable volume sizes based on a YAML config file."
    )
    parser.add_argument(
        "config",
        help="Path to the YAML configuration file",
    )
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found at '{args.config}'")
        sys.exit(1)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    # Derive input directory from the YAML file's base name (without extension)
    input_dir = os.path.splitext(os.path.basename(args.config))[0]
    print(f"Data volume sizes for : '{input_dir}'\n")
    
    version = cfg['dreq_version']
    spatial_defaults = cfg['spatial_defaults']
    other_dims = cfg['other_dims']

    # Convert list representations to tuples for consistency
    spatial_defaults = {k: tuple(v) for k, v in spatial_defaults.items()}

    # input file for this configuration
    csv_file = os.path.join(input_dir, "cmcc_data_selected.csv")

    if not os.path.exists(csv_file):
        print(f"Error: Selected variables file not found at '{csv_file}'")
        sys.exit(1)

    print(f"Loading Data Request dimension sizes ({version})...")
    dreq_dim_sizes, time_dims = extract_dreq_dimensions(version=version)

    realm_totals = defaultdict(float)
    realm_counts = defaultdict(int)
    total_volume = 0.0
    total_count = 0

    print(f"\nReading '{csv_file}' and calculating variable sizes...\n")
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
                    spatial_defaults=spatial_defaults,
                    other_dims=other_dims,
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

    print_summary_report(realm_totals, realm_counts, total_volume, total_count)


# --------------------------------------------------------------------------- #
# Integrated Volume Calculation Core                                          #
# --------------------------------------------------------------------------- #
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


def get_variable_size(
    var_info,
    dreq_dim_sizes,
    time_dims,
    spatial_defaults,
    other_dims,
    realm="atmos",
    compression=1.0,
    return_gb=True,
):
    """
    Computes annual data volume for a single variable.

    Parameters:
        var_info (dict): Variable record containing 'dimensions', 'frequency', etc.
        dreq_dim_sizes (dict): Dimension sizes extracted from the Data Request API.
        time_dims (dict): Map of temporal axis names.
        spatial_defaults (dict): Spatial dimension defaults by realm.
        other_dims (dict): Specific fallback sizes for custom spatial/vertical dimensions.
        realm (str): Modeling realm for spatial grid fallback.
        compression (float): Data compression factor (default 1.0).
        return_gb (bool): Returns size in GB/year if True, else in bytes.
    """
    dims_str = var_info.get("dimensions", "") or ""
    dim_list = dims_str.split()

    nx, ny, nz_default = spatial_defaults.get(
        realm, spatial_defaults.get("atmos", (48600, 1, 58))
    )

    spatial_points = 1

    for d in dim_list:
        d_lower = d.lower()
        if re.match(r"^time", d):
            continue
        elif d == "latitude":
            spatial_points = spatial_points * ny
        elif d == "longitude":
            spatial_points = spatial_points * nx
        elif d in dreq_dim_sizes:
            other_dim = dreq_dim_sizes[d]
            if isinstance(other_dim, str):
                if d in other_dims:
                    other_dim = other_dims[d]
                else:
                    print("cannot set dimension for " + d)
                    sys.exit()
            spatial_points = spatial_points * other_dim

    freq = var_info.get("frequency", "")
    timesteps = parse_time_steps(freq)

    bytes_per_year = spatial_points * timesteps * 4 * compression

    if return_gb:
        return bytes_per_year / (1024.0**3)
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
                    dim_rec = (
                        coord_table.get_record(link)
                        if hasattr(coord_table, "get_record")
                        else coord_table.records.get(link)
                    )
                    dim_name = getattr(dim_rec, "name", "None")
                except Exception:
                    dim_name = "None"
            else:
                dim_name = "None"
            time_dims[dim_name] = getattr(rec, "name", "None")

    return dreq_dim_sizes, time_dims


# --------------------------------------------------------------------------- #
# Reporting Helpers                                                           #
# --------------------------------------------------------------------------- #
def print_summary_report(realm_totals, realm_counts, total_volume, total_count):
    """Prints a formatted summary report table of volume usage by realm."""
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
