#!/usr/bin/env python
"""
Combined CMCC CMIP7 Request Generator & Raw Variable List Mapper.

1. Parses internal selection CSV (optionally filtering/excluding variable groups).
2. Queries the Data Request API to build and output 'dr-cmip7-full/cmcc_data_request.csv'.
3. Maps compound names against 'cmip7-lookup/*_lookup.csv' tables.
4. Saves selected mapped variables to 'dr-cmip7-full/cmcc_data_selected.csv'.
5. Generates '<realm>_raw_list.txt' files organized by realm, frequency, and cell method.
"""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict
import yaml

# --------------------------------------------------------------------------- #
# Constants & Realm Mappings                                                  #
# --------------------------------------------------------------------------- #
ALIASES = {
    "omip_geometry_physics": ["omip_scalars_high_priority"],
    "hydro_modelling_PET_daily": ["WaterResourcesPET_daily"],
}

REALM_TO_LOOKUP = {
    "atmos": "atm", "aerosol": "atm", "atmosChem": "atm",
    "land": "lnd", "landIce": "lnd",
    "ocean": "ocn", "ocnBgchem": "ocnbgc",
    "seaIce": "ice",
}

LOOKUP_FAMILIES = ["atm", "ice", "lnd", "ocn", "ocnbgc"]


# --------------------------------------------------------------------------- #
# Main Workflow                                                               #
# --------------------------------------------------------------------------- #
def main():
    """Executes the complete end-to-end data request processing and raw variable list generation pipeline."""
    parser = argparse.ArgumentParser(
        description="CMCC CMIP7 Data Request Generator & Mapper"
    )
    parser.add_argument(
        "config_path",
        help="Path to the YAML configuration file",
    )
    args = parser.parse_args()

    # Load top-level configuration parameters from YAML
    cfg = load_config(args.config_path)

    # Derive output_dir from config_path basename without extension
    output_dir = os.path.splitext(os.path.basename(args.config_path))[0]
    print(f"Output directory: '{output_dir}'\n")

    print(f"1. Parsing selection CSV '{cfg['input_csv']}'...")
    selection = parse_cmcc_csv(cfg['input_csv'], exclude_groups=cfg['exclude_groups'], select_groups=cfg['select_groups'])

    print(f"2. Loading Data Request ({cfg['dreq_version']})...")
    _DR, meta_by_uid, groups, dreq_dim_sizes, time_dims = load_dr(cfg['dreq_version'])

    print("3. Building variables table...")
    var_rows = build_variables_table(selection, meta_by_uid, groups)

    filename = "cmcc_data_request.csv"
    print(f"4. Writing intermediate CSV to '{output_dir}/{filename}'...")
    variables_path = write_intermediate_csv(var_rows, output_dir, filename)

    print("5. Loading lookup tables...")
    lookup_dict = load_lookup_tables(cfg['lookup_dir'])

    print("6. Processing raw variable mappings...")
    output_dict, selected_variables = process_variables(variables_path, lookup_dict)

    filename = "cmcc_data_selected.csv"
    print(f"Saving selected variables CSV to '{output_dir}/{filename}'...")
    write_intermediate_csv(selected_variables, output_dir, filename)

    print(f"7. Writing list of model variables for each realm to '{output_dir}'...")
    write_model_variables_realm(output_dict, outdir=output_dir)


# --------------------------------------------------------------------------- #
# Helper Configuration Loader                                                 #
# --------------------------------------------------------------------------- #
def load_config(config_path):
    """Loads top-level configuration parameters from a YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg


# --------------------------------------------------------------------------- #
# Data Request Extraction Functions                                            #
# --------------------------------------------------------------------------- #
def extract_dreq_dimensions(version):
    """Extracts dimension sizes and temporal dimension mappings from the Data Request API for a given version."""
    from data_request_api.content import dump_transformation as dt
    from data_request_api.query import dreq_query as dq

    time_dims = {}
    dreq_dim_sizes = {}

    try:
        content_dic = dt.get_transformed_content(version=version)
        base = dq.create_dreq_tables_for_request(content_dic, version)
        dreq_tables = {
            "coordinates and dimensions": base["Coordinates and Dimensions"],
            "temporal shape": base["Temporal Shape"],
            "frequency": base["CMIP7 Frequency"],
            "spatial shape": base["Spatial Shape"],
        }
        dreq_dim_sizes = dq.get_dimension_sizes(dreq_tables)

        for rec in dreq_tables["temporal shape"].records.values():
            if hasattr(rec, "dimensions") and rec.dimensions:
                link = rec.dimensions[0]
                dim_name = dreq_tables["coordinates and dimensions"].get_record(link).name
            else:
                dim_name = "None"
            time_dims[dim_name] = rec.name
    except Exception as e:
        print(f"Warning: Failed to extract dreq dimensions ({e})")

    return dreq_dim_sizes, time_dims


def clean_group_token(tok):
    """Extracts a clean group ID and optional parenthetical note from a raw string token."""
    tok = tok.strip()
    if not tok:
        return None, ""
    note = ""
    m = re.search(r"\(([^)]*)\)", tok)
    if m:
        note = m.group(1).strip()
        tok = (tok[: m.start()] + tok[m.end():]).strip()
    m = re.match(r"^([A-Za-z][A-Za-z0-9_]*)(.*)$", tok)
    if not m:
        return None, (note + " " + tok).strip()
    gid, rest = m.group(1), m.group(2).strip(" .,")
    if rest:
        note = (note + " " + rest).strip()
    return gid, note


def parse_cmcc_csv(csv_path, exclude_groups=None, select_groups=None):
    """Parses the internal CMCC selection CSV and returns selected variable groups with notes."""
    exclude_groups = [str(g).lower() for g in (exclude_groups or [])]
    select_groups = [str(g).lower() for g in (select_groups or [])]

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    hdr_idx = next(
        (i for i, r in enumerate(rows) if any("CMCC priority" in c for c in r)),
        1,
    )

    out = []
    for r in rows[hdr_idx + 1:]:
        if len(r) < 5:
            continue
        opp, prio, vg = r[2].strip(), r[3].strip().lower(), r[4]
        if not opp:
            continue

        groups, seen = [], set()
        for raw_tok in re.split(r"[,\n]", vg):
            gid, note = clean_group_token(raw_tok)
            if gid is None:
                continue
            if gid.lower() in exclude_groups:
                continue
            if select_groups and gid.lower() not in select_groups:
                continue
            if gid and gid.lower() not in seen:
                seen.add(gid.lower())
                groups.append((gid, note))

        out.append({"opportunity": opp, "priority": prio, "groups": groups, "raw": vg.strip()})
    return out


def load_dr(version):
    """Loads the Data Request content, variable metadata, dimension sizes, and temporal dimensions for a given API version."""
    from data_request_api.content import dreq_content as dc
    from data_request_api.content import dump_transformation as dt
    from data_request_api.query import data_request as dr
    from data_request_api.query import dreq_query as dq

    content_dic = dt.get_transformed_content(version=version)
    DR = dr.DataRequest.from_separated_inputs(**content_dic)

    dc.retrieve(version)
    content = dc.load(version)

    meta_by_name = dq.get_variables_metadata(content, version, verbose=False)
    meta_by_name.pop("Header", None)

    meta_by_uid = {}
    for name, info in meta_by_name.items():
        info = dict(info)
        info["_unique_name"] = name
        meta_by_uid[info["uid"]] = info

    groups = {}
    for g in DR.get_variable_groups():
        nm = getattr(g, "name", None)
        nm = str(nm) if nm is not None else str(g)
        groups[_norm(nm)] = (nm, g)

    dreq_dim_sizes, time_dims = extract_dreq_dimensions(version)

    return DR, meta_by_uid, groups, dreq_dim_sizes, time_dims


def _norm(s):
    """Normalizes string keys by stripping whitespace and converting to lowercase."""
    return re.sub(r"\s+", "", str(s)).lower()


def time_operation(meta):
    """Determines time frequency operation ('ave', 'inst', 'max', 'min', 'clim', 'unknown') from metadata."""
    cm = (meta.get("cell_methods") or "").lower()
    ts = (meta.get("temporal_shape") or "").lower()
    if "time: point" in cm or ts.endswith("point"):
        return "inst"
    if "maximum" in cm:
        return "max"
    if "minimum" in cm:
        return "min"
    if "clim" in ts or "climatology" in cm:
        return "clim"
    if "time:" in cm or ts.endswith("intv") or ts.startswith("time"):
        return "ave"
    if ts == 'none' and meta['frequency'] == 'fx':
        return "fixed"
    return "unknown"


def tier_of(group_name):
    """Extracts the tier designation string (e.g. 'tier1') from a group name."""
    m = re.search(r"tier[_ ]?([0-9])", str(group_name), re.I)
    return f"tier{m.group(1)}" if m else ""


def build_variables_table(selection, meta_by_uid, groups):
    """Matches selected groups against DR metadata and constructs aggregated variable records."""
    aliases_norm = {_norm(k): v for k, v in ALIASES.items()}
    var_rows = {}

    for entry in selection:
        opp, prio = entry["opportunity"], entry["priority"]
        for gid, note in entry["groups"]:
            key = _norm(gid)
            targets = []
            if key in groups:
                targets = [groups[key]]
            elif key in aliases_norm:
                for real in aliases_norm[key]:
                    rk = _norm(real)
                    if rk in groups:
                        targets.append(groups[rk])

            for matched_name, gobj in targets:
                for var in gobj.get_variables():
                    uid = getattr(var, "uid", None)
                    meta = meta_by_uid.get(uid)
                    if meta is None or meta.get("region") != "glb":
                        continue

                    name = meta["_unique_name"]
                    rec = var_rows.get(name)
                    if rec is None:
                        c6c = meta.get("cmip6_compound_name", "") or ""
                        rec = {
                            "compound_name": name,
                            "out_name": meta.get("out_name", ""),
                            "cmip6_name": c6c.split(".")[-1] if c6c else "",
                            "cmip6_compound_name": c6c,
                            "frequency": meta.get("frequency", ""),
                            "realm": (meta.get("modeling_realm", "") or "").split(" ")[0],
                            "realm_all": meta.get("modeling_realm"),
                            "time_oper": time_operation(meta),
                            "cell_methods": meta.get("cell_methods", ""),
                            "cmip6_table": meta.get("cmip6_table", ""),
                            "long_name": meta.get("long_name", ""),
                            "dimensions": meta.get("dimensions", ""),
                            "tiers": set(),
                            "groups": set(),
                            "opportunities": set(),
                            "priorities": set(),
                        }
                        var_rows[name] = rec

                    if tier_of(matched_name):
                        rec["tiers"].add(tier_of(matched_name))
                    rec["groups"].add(matched_name)
                    rec["opportunities"].add(opp)
                    rec["priorities"].add(prio)

    return var_rows


def write_intermediate_csv(var_rows, outdir, filename):
    """Writes compiled variable metadata to intermediate CSV file in the target directory."""
    os.makedirs(outdir, exist_ok=True)
    var_path = os.path.join(outdir, filename)
    fields = [
        "compound_name", "cmip6_name", "out_name", "cmip6_compound_name",
        "frequency", "time_oper", "realm", "realm_all", "cmip6_table",
        "long_name", "dimensions", "tiers", "groups", "opportunities", "priorities",
        "cell_methods"
    ]

    def _format_field(val):
        """Converts sets/lists to sorted semicolon-joined strings; leaves strings as-is."""
        if isinstance(val, (set, list)):
            return ";".join(sorted(str(x) for x in val if x))
        return "" if val is None else str(val)

    # Support dict or list inputs
    rows_iter = var_rows.values() if isinstance(var_rows, dict) else var_rows
    rows = sorted(
        rows_iter,
        key=lambda r: (
            _format_field(r.get("realm")),
            _format_field(r.get("frequency")),
            _format_field(r.get("cmip6_name") or r.get("out_name"))
        )
    )

    with open(var_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for r in rows:
            w.writerow([
                _format_field(r.get("compound_name")),
                _format_field(r.get("cmip6_name")),
                _format_field(r.get("out_name")),
                _format_field(r.get("cmip6_compound_name")),
                _format_field(r.get("frequency")),
                _format_field(r.get("time_oper")),
                _format_field(r.get("realm")),
                _format_field(r.get("realm_all")),
                _format_field(r.get("cmip6_table")),
                _format_field(r.get("long_name")),
                _format_field(r.get("dimensions")),
                _format_field(r.get("tiers")),
                _format_field(r.get("groups")),
                _format_field(r.get("opportunities")),
                _format_field(r.get("priorities")),
                _format_field(r.get("cell_methods")),
            ])
    return var_path


# --------------------------------------------------------------------------- #
# Post-Processing & Raw List Generation                                       #
# --------------------------------------------------------------------------- #
def load_lookup_tables(lookup_dir):
    """Loads realm lookup CSV tables into a realm-indexed dictionary, skipping 'DISCARD' entries."""
    lookup_dict = {fam: {} for fam in LOOKUP_FAMILIES}
    for fam in LOOKUP_FAMILIES:
        filepath = os.path.join(lookup_dir, f"{fam}_lookup.csv")
        if not os.path.exists(filepath):
            continue
        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                var = (row.get("variable") or "").strip()
                model_val = (row.get("model") or "").strip()
                if var and model_val != "DISCARD":
                    lookup_dict[fam][var] = model_val
    return lookup_dict


def process_variables(variables_csv_path, lookup_dict):
    """Maps variables from intermediate CSV against lookup tables into an output structure per realm, frequency, and cell."""
    output_dict = {fam: defaultdict(lambda: defaultdict(list)) for fam in LOOKUP_FAMILIES}
    if not os.path.exists(variables_csv_path):
        return output_dict, {}

    selected_variables = {}
    with open(variables_csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            compound_name = row.get("compound_name", "").strip()
            raw_realm = row.get("realm", "").strip()
            cell = row.get("time_oper", "").strip()
            freq = row.get("frequency", "").strip()

            if not compound_name or not raw_realm or not cell or not freq:
                continue

            # extract variable name discarding output frequency and domain
            parts = compound_name.split(".")
            base_var = ".".join(parts[:-2]).strip() if len(parts) > 2 else compound_name

            lookup_realm = REALM_TO_LOOKUP.get(raw_realm)
            if not lookup_realm or lookup_realm not in lookup_dict:
                continue

            if base_var in lookup_dict[lookup_realm]:
                model_val = lookup_dict[lookup_realm][base_var]
                output_dict[lookup_realm][freq][cell].extend([x.strip() for x in model_val.split(',')])
                selected_variables[compound_name] = row

    for realm, freqs in output_dict.items():
        for freq, cells in freqs.items():
            for cell, model_val in cells.items():
                output_dict[realm][freq][cell] = sorted(set(model_val))

    formatted_output = {
        fam: {freq_key: dict(cell_map) for freq_key, cell_map in freqs.items()}
        for fam, freqs in output_dict.items()
    }

    return formatted_output, selected_variables


def write_model_variables_realm(output_dict, outdir):
    """Writes structured output dictionary content into realm-specific '<realm>_raw_list.txt' files."""
    os.makedirs(outdir, exist_ok=True)
    for realm, freqs in output_dict.items():
        filepath = os.path.join(outdir, f"{realm}_raw_list.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            for freq, cells in freqs.items():
                f.write(f"{freq}\n")
                for cell, model_val in cells.items():
                    f.write(f"operation: {cell}\n")
                    f.write(", ".join(model_val) + "\n")
                f.write(f"\n")
        print(f"Wrote {filepath}")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)

    main()
