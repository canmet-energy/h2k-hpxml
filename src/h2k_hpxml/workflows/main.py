import os

from h2k_hpxml.config import ConfigManager
from h2k_hpxml.core.translator import h2ktohpxml

# Load configuration using ConfigManager
config_manager = ConfigManager()

source_h2k_path = str(config_manager.source_h2k_path)
hpxml_os_path = str(config_manager.hpxml_os_path)
dest_hpxml_path = str(config_manager.dest_hpxml_path)

# Get translation mode with fallback
translation_mode = config_manager.get("translation", "mode", "SOC")


# print(config.get("nonh2k", "operable_window_avail_days"))

# if __name__ == "__main__":
#     print("name is main")
#     try:
#         sourcepath = sys.argv[1]
#     except IndexError:
#         pass
#     print("sourcepath: " + sourcepath)


# Determine whether to process as folder or single file
if ".h2k" in source_h2k_path.lower():
    # Single file
    # convert to array for consistent processing
    # print("single file")
    h2k_files = [source_h2k_path]
else:
    # Folder
    # List folder and append to source path
    # print("folder")
    h2k_files = [f"{source_h2k_path}/{x}" for x in os.listdir(source_h2k_path)]

print("H2k Files:", h2k_files)

for filepath in h2k_files:
    print("================================================")
    print("File Path: ", filepath)

    with open(filepath, encoding="utf-8") as f:
        h2k_string = f.read()

    hpxml_string = h2ktohpxml(h2k_string, {"translation_mode": translation_mode})

    # with open(f"./tests/files/{filepath.split("/")[-1].replace(".h2k",".xml")}", "w") as f:

    # Generate clean filename for HPXML output
    filename = filepath.split("/")[-1]
    filename = filename.replace(".h2k", ".xml").replace(".H2K", ".xml").replace(" ", "-")
    output_path = f"{hpxml_os_path}/{dest_hpxml_path}/{filename}"

    with open(output_path, "w") as f:
        f.write(hpxml_string)
