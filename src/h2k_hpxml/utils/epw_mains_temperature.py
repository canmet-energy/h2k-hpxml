"""Derive water heater inlet (mains) temperature from EPW files.

Uses the Burch & Christensen mains water temperature algorithm from
OpenStudio-HPXML ``weather.rb`` (``calc_mains_temperatures``), matching the
``MainsDailyTemps`` / ``MainsAnnualTemp`` values consumed by OS-HPXML DHW calcs.
"""

from __future__ import annotations

import math
from pathlib import Path

from .logging import get_logger

logger = get_logger(__name__)

EPW_HEADER_ROWS = 8


def epw_path_from_weather_file(weather_file: str) -> Path:
    """Return the EPW path for a weather file basename or path without extension."""
    path = Path(weather_file)
    if path.suffix.lower() == ".epw":
        return path
    # Append .epw; do not use with_suffix() — CWEC basenames contain dots
    # (e.g. CAN_ON_Ottawa.Intl.AP.716280_CWEC2020) and with_suffix would
    # replace the station-id segment instead of adding the extension.
    return Path(f"{weather_file}.epw")


def celsius_to_fahrenheit(temp_c: float) -> float:
    return temp_c * 9.0 / 5.0 + 32.0


def calc_mains_annual_temp_f(
    annual_avg_drybulb_f: float,
    monthly_avg_drybulbs_f: list[float],
    latitude: float,
    n_days: int,
) -> float:
    """Replicate OS-HPXML ``WeatherFile#calc_mains_temperatures`` annual average."""
    deg_rad = math.pi / 180.0
    tmains_ratio = 0.4 + 0.01 * (annual_avg_drybulb_f - 44.0)
    tmains_lag = 35.0 - (annual_avg_drybulb_f - 44.0)
    sign = 1 if latitude < 0 else -1
    max_diff_monthly = max(monthly_avg_drybulbs_f) - min(monthly_avg_drybulbs_f)

    daily_temps = []
    for day in range(1, n_days + 1):
        temp_f = annual_avg_drybulb_f + 6.0 + tmains_ratio * max_diff_monthly / 2.0 * math.sin(
            deg_rad * (0.986 * (day - 15.0 - tmains_lag) + sign * 90.0)
        )
        daily_temps.append(max(32.0, temp_f))

    return sum(daily_temps) / n_days


def read_epw_mains_annual_temp_f(epw_path: str | Path) -> float:
    """
    Parse an EPW file and return the annual average water heater inlet temperature (F).

    Raises:
        FileNotFoundError: If the EPW file does not exist.
        ValueError: If the EPW file cannot be parsed.
    """
    path = Path(epw_path)
    if not path.is_file():
        raise FileNotFoundError(f"EPW file not found: {path}")

    latitude = None
    hourly_dry_bulbs_c: list[float] = []
    monthly_sums = [0.0] * 12
    monthly_counts = [0] * 12

    with path.open(encoding="utf-8", errors="replace") as epw_file:
        for row_index, line in enumerate(epw_file):
            if row_index == 0:
                parts = [part.strip() for part in line.split(",")]
                if len(parts) < 8:
                    raise ValueError(f"Invalid EPW location header in {path}")
                latitude = float(parts[6])
                continue

            if row_index < EPW_HEADER_ROWS:
                continue

            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 7:
                continue

            try:
                month = int(parts[1])
                dry_bulb_c = float(parts[6])
            except ValueError as exc:
                raise ValueError(f"Invalid EPW data row {row_index + 1} in {path}") from exc

            hourly_dry_bulbs_c.append(dry_bulb_c)
            monthly_sums[month - 1] += dry_bulb_c
            monthly_counts[month - 1] += 1

    if latitude is None or not hourly_dry_bulbs_c:
        raise ValueError(f"No EPW weather data found in {path}")

    if any(count == 0 for count in monthly_counts):
        raise ValueError(f"Incomplete monthly EPW data in {path}")

    n_days = max(len(hourly_dry_bulbs_c) // 24, 1)

    hourly_dry_bulbs_f = [celsius_to_fahrenheit(temp_c) for temp_c in hourly_dry_bulbs_c]
    annual_avg_drybulb_f = sum(hourly_dry_bulbs_f) / len(hourly_dry_bulbs_f)
    monthly_avg_drybulbs_f = [
        celsius_to_fahrenheit(monthly_sums[i] / monthly_counts[i]) for i in range(12)
    ]

    mains_annual_f = calc_mains_annual_temp_f(
        annual_avg_drybulb_f, monthly_avg_drybulbs_f, latitude, n_days
    )
    logger.debug(
        "EPW mains inlet temperature for %s: %.2f F (annual avg drybulb %.2f F)",
        path.name,
        mains_annual_f,
        annual_avg_drybulb_f,
    )
    return mains_annual_f
