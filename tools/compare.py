import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from h2k_hpxml.analysis import annual
from h2k_hpxml.config.manager import ConfigManager
from h2k_hpxml.config.translation_config import build_translation_config
from h2k_hpxml.core.translator import h2ktohpxml

# Use ConfigManager instead of direct INI parsing
config = ConfigManager()

source_h2k_path = Path(config.source_h2k_path)
hpxml_os_path = Path(config.hpxml_os_path)
dest_hpxml_path = config.get("paths", "dest_hpxml_path", "workflow/translated_h2ks/")

dest_compare_data = config.get_path("paths", "dest_compare_data")
if dest_compare_data is None:
    dest_compare_data = Path("./output/comparisons")
dest_compare_data.mkdir(parents=True, exist_ok=True)

flags = config.simulation_flags
print("flags", flags)

translation_config = build_translation_config(config)
translation_mode = translation_config["translation_mode"]
operating_condition = translation_config["operating_condition"]


# Determine whether to process as folder or single file
source_h2k_str = str(source_h2k_path)
if ".h2k" in source_h2k_str.lower():
    print("single file")
    h2k_files = [source_h2k_path]
else:
    print("folder")
    h2k_files = [source_h2k_path / name for name in os.listdir(source_h2k_path)]

print("h2k_files", h2k_files)


def run_hpxml_os(file="", path=""):
    path_to_log = hpxml_os_path / path / "run"
    success = False
    result = {}
    try:
        result = subprocess.run(
            f"openstudio workflow/run_simulation.rb -x {path}/{file} {flags}",
            cwd=hpxml_os_path,
            check=True,
            # capture_output=True,
            # text=True,
        )
        success = True

    except subprocess.CalledProcessError:
        print("Error in input file, check logs")

    return {"result": result, "success": success, "path_to_log": path_to_log}


compare_dict_out = {}

ashrae140_csv_string = ""

for filepath in h2k_files:
    filepath = Path(filepath)
    print("filepath", filepath)
    h2k_filename = filepath.name
    hpxml_filename = h2k_filename.replace(".h2k", ".xml").replace(".H2K", ".xml").replace(" ", "-")
    print(h2k_filename)

    hpxml_output_dir = hpxml_os_path / dest_hpxml_path
    hpxml_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with filepath.open(encoding="utf-8") as f:
            h2k_string = f.read()

        hpxml_string = h2ktohpxml(h2k_string, translation_config)

        hpxml_output_path = hpxml_output_dir / hpxml_filename
        hpxml_output_path.write_text(hpxml_string, encoding="utf-8")

        result = run_hpxml_os(hpxml_filename, dest_hpxml_path)

        print(result)
        os_results = annual.read_os_results(str(hpxml_output_dir), return_type="dict")

        if (os_results.get("Energy Use: Total (MBtu)", 0) == 0) & (translation_mode != "ASHRAE140"):
            # no results generated, check logs
            run_log = hpxml_output_dir / "run" / "run.log"
            logs_string = run_log.read_text(encoding="utf-8")

            compare_dict_out[h2k_filename] = logs_string
            continue

        if translation_mode == "ASHRAE140":
            h2k_results = {}
            weather_location = "unknown"
            hot_water_load_Lperday = 0

            ashrae_140_results = annual.get_ashrae_140_results(os_results)

            print("ashrae_140_results", ashrae_140_results)

            [_, testname, heatingCooling] = h2k_filename.split(" ")

            new_line = [
                f"{testname}{heatingCooling[0]}",
                str(ashrae_140_results["HeatingLoadMBtu"]),
                str(ashrae_140_results["CoolingLoadMBtu"]),
            ]

            # print(",".join(new_line))
            ashrae140_csv_string = ashrae140_csv_string + ",".join(new_line) + ",\n"

        else:
            h2k_results, weather_location, hot_water_load_Lperday = annual.read_h2k_results(
                str(filepath), operating_conditions=operating_condition
            )

        compare_dict = annual.compare_os_h2k_annual(h2k_results, os_results)
        compare_dict["location"] = weather_location
        compare_dict["hot_water_usage_Lperday_h2k"] = hot_water_load_Lperday

        compare_dict_out[h2k_filename] = compare_dict

    except Exception as error:
        compare_dict_out[h2k_filename] = {"error": f"{error}"}

print("DONE")
# print(ashrae140_csv_string)


compare_output = dest_compare_data / "systems_compare_data.json"
with compare_output.open("w", encoding="utf-8") as f:
    json.dump(compare_dict_out, f, indent=4)
print(f"Wrote comparison results to {compare_output}")
