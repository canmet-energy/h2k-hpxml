import csv
import os
import zipfile
import warnings

import requests
from filelock import FileLock
from unidecode import unidecode
import urllib3

# Suppress SSL warnings for weather file downloads
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ConfigManager will be passed as parameter to functions that need it

prov_terr_codes = {
    "BRITISH COLUMBIA": "BC",
    "ALBERTA": "AB",
    "SASKATCHEWAN": "SK",
    "MANITOBA": "MB",
    "ONTARIO": "ON",
    "QUEBEC": "QC",
    "NEW BRUNSWICK": "NB",
    "NOVA SCOTIA": "NS",
    "PRINCE EDWARD ISLAND": "PE",
    "NEWFOUNDLAND AND LABRADOR": "NL",
    "YUKON": "YT",
    "NORTHWEST TERRITORIES": "NT",
    "NUNAVUT": "NU",
}


def get_cwec_file(
    weather_region="ONTARIO",
    weather_location="LONDON",
    weather_folder=None,
    weather_vintage=None,
    weather_library=None,
    config_manager=None,
):
    # Use config_manager for defaults if provided
    if config_manager:
        if weather_folder is None:
            weather_folder = os.path.join(str(config_manager.hpxml_os_path), "weather")
        if weather_vintage is None:
            weather_vintage = config_manager.weather_vintage
        if weather_library is None:
            weather_library = config_manager.weather_library

    # Ensure we have required values
    if weather_folder is None:
        raise ValueError("weather_folder must be provided either directly or via config_manager")
    if weather_vintage is None:
        weather_vintage = "CWEC2020"  # Default fallback
    if weather_library is None:
        weather_library = "historic"  # Default fallback

    if not weather_region:
        raise ValueError("Weather region is not defined in the h2k file")
    if not weather_location:
        raise ValueError("Weather location is not defined  in the h2k file")

    weather_region = unidecode(weather_region).upper()
    weather_location = unidecode(weather_location).upper()
    weather_vintage = unidecode(weather_vintage).upper()
    weather_library = unidecode(weather_library).lower()

    # Read the csv file with the list of weather files from the resources directory

    weather_files_csv = os.path.join(
        os.path.dirname(__file__), "..", "resources", "weather", "h2k_weather_names.csv"
    )

    if not os.path.exists(weather_files_csv):
        raise FileNotFoundError(f"CSV file not found at {weather_files_csv}")

    with open(weather_files_csv) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        weather_files = list(csv_reader)
    province_english = weather_region
    city_english = weather_location

    # Look up the corresponding CWEC2020.zip value given the province and city
    zip_file = None
    for row in weather_files:
        if row["provinces_english"] == province_english and row["cities_english"] == city_english:
            zip_file = row["CWEC2020.zip"]
            break
    if zip_file is None:
        raise ValueError(
            f"Could not find a CWEC2020.zip file for {province_english} and {city_english}"
        )

    # Check to see if epw file already exists in the weather folder
    epw_file = os.path.join(os.path.join(weather_folder), f"{zip_file[:-4]}.epw")
    if os.path.exists(epw_file):
        print(f"Weather file already exists:  \t {epw_file}")
        return os.path.join(weather_folder, f"{zip_file[:-4]}")

    # Download the file from github
    github_url = "https://github.com/canmet-energy/btap_weather/raw/refs/heads/main/historic/"
    # Download file from github using the github_url and zip_file name
    file_url = f"{github_url}{zip_file}"
    local_filename = os.path.join(os.path.dirname(__file__), f"{zip_file}")

    # Define a lock file for the zip file
    lock_file = f"{local_filename}.lock"
    with FileLock(lock_file):
        # Download the file
        response = requests.get(file_url, verify=False)
        if response.status_code == 200:
            with open(local_filename, "wb") as f:
                f.write(response.content)
        else:
            raise Exception(
                f"Failed to download file from {file_url}, status code: {response.status_code}"
            )

        # Unzip the downloaded file
        with zipfile.ZipFile(local_filename, "r") as zip_ref:
            extract_path = os.path.join(weather_folder)
            for file in zip_ref.namelist():
                if file.endswith(".epw"):
                    zip_ref.extract(file, extract_path)
    return os.path.join(extract_path, f"{zip_file[:-4]}")


def get_climate_zone(hdd):
    if hdd < 3000:
        return "4"
    elif hdd >= 3000 & hdd < 4000:
        return "5"
    elif hdd >= 4000 & hdd < 5000:
        return "6"
    elif hdd >= 5000 & hdd < 6000:
        return "7a"
    elif hdd >= 6000 & hdd < 7000:
        return "7b"
    else:
        return "8"
