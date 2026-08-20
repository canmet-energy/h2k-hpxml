"""Tests for heat pump switchover / lockout temperature mapping."""

import pytest

from h2k_hpxml.components.system_heat_pumps import ELECTRIC_LOCKOUT_DEADBAND_F
from h2k_hpxml.components.system_heat_pumps import _apply_restricted_defrost_backup_control
from h2k_hpxml.components.system_heat_pumps import _split_temperature_fields
from h2k_hpxml.components.system_heat_pumps import build_backup_temperature_fields


@pytest.mark.parametrize("switchover_type", ["balance", "unrestricted", None])
def test_balance_and_unrestricted_omit_temperature_fields(switchover_type):
    assert (
        build_backup_temperature_fields(switchover_type, 25.0, "natural gas") == {}
    )
    assert build_backup_temperature_fields(switchover_type, 25.0, "electricity") == {}


def test_fossil_backup_uses_switchover_temperature():
    fields = build_backup_temperature_fields("restricted", 30.0, "natural gas", "air-to-air")
    assert fields == {"BackupHeatingSwitchoverTemperature": 30.0}


def test_fossil_backup_separate_propane_uses_switchover():
    fields = build_backup_temperature_fields("restricted", 20.0, "propane", "mini-split")
    assert fields == {"BackupHeatingSwitchoverTemperature": 20.0}


def test_gshp_fossil_backup_uses_equal_lockouts_not_switchover():
    fields = build_backup_temperature_fields(
        "restricted", 25.0, "natural gas", "ground-to-air"
    )
    assert "BackupHeatingSwitchoverTemperature" not in fields
    assert fields == {
        "CompressorLockoutTemperature": 25.0,
        "BackupHeatingLockoutTemperature": 25.0,
    }


def test_electric_backup_uses_lockouts_with_deadband():
    temp = 17.6  # ~ -8C in F after conversion
    fields = build_backup_temperature_fields("restricted", temp, "electricity", "air-to-air")
    assert "BackupHeatingSwitchoverTemperature" not in fields
    assert fields["BackupHeatingLockoutTemperature"] == temp
    assert fields["CompressorLockoutTemperature"] == temp - ELECTRIC_LOCKOUT_DEADBAND_F
    assert (
        fields["BackupHeatingLockoutTemperature"] - fields["CompressorLockoutTemperature"]
        >= ELECTRIC_LOCKOUT_DEADBAND_F
    )


def test_electric_integrated_backup_same_as_separate():
    fields = build_backup_temperature_fields("restricted", 5.0, "electricity", "mini-split")
    assert fields == {
        "CompressorLockoutTemperature": 0.0,
        "BackupHeatingLockoutTemperature": 5.0,
    }


def test_split_temperature_fields_separates_compressor_and_backup():
    fields = build_backup_temperature_fields("restricted", 14.0, "electricity", "air-to-air")
    compressor, backup = _split_temperature_fields(fields)
    assert compressor == {"CompressorLockoutTemperature": 9.0}
    assert backup == {"BackupHeatingLockoutTemperature": 14.0}


def test_split_switchover_keeps_only_backup_side():
    fields = build_backup_temperature_fields("restricted", 30.0, "natural gas", "air-to-air")
    compressor, backup = _split_temperature_fields(fields)
    assert compressor == {}
    assert backup == {"BackupHeatingSwitchoverTemperature": 30.0}


def test_restricted_integrated_disables_defrost_backup_heat():
    hp = {
        "BackupType": "integrated",
        "extension": {"HeatingAutosizingFactor": 1},
    }
    result = _apply_restricted_defrost_backup_control(hp, "restricted")
    assert result["extension"]["BackupHeatingActiveDuringDefrost"] is False
    assert result["extension"]["HeatingAutosizingFactor"] == 1


def test_restricted_separate_keeps_defrost_default():
    hp = {"BackupType": "separate", "BackupSystem": {"@idref": "HeatingSystem1"}}
    result = _apply_restricted_defrost_backup_control(hp, "restricted")
    assert "extension" not in result


@pytest.mark.parametrize("switchover_type", ["balance", "unrestricted", None])
def test_non_restricted_integrated_keeps_defrost_default(switchover_type):
    hp = {"BackupType": "integrated", "extension": {}}
    result = _apply_restricted_defrost_backup_control(hp, switchover_type)
    assert "BackupHeatingActiveDuringDefrost" not in result["extension"]
