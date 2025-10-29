"""
Unit tests for the CLI convert module functionality.
"""

import pytest

from h2k_hpxml.api import _build_simulation_flags


class TestBuildSimulationFlags:
    """Test cases for build_simulation_flags function."""

    def test_basic_boolean_flags(self):
        """Test basic boolean flags are handled correctly."""
        flags = _build_simulation_flags(
            add_component_loads=True,
            debug=False,
            skip_validation=True,
            output_format="csv",
            timestep=(),
            daily=(),
            hourly=(),
            monthly=(),
            add_stochastic_schedules=False,
            add_timeseries_output_variable=(),
        )

        assert "--add-component-loads" in flags
        assert "--debug" not in flags
        assert "--skip-validation" in flags
        assert "--output-format csv" in flags
        assert "--add-stochastic-schedules" not in flags

    def test_empty_tuples(self):
        """Test that empty tuples don't add any flags."""
        flags = _build_simulation_flags(
            add_component_loads=False,
            debug=False,
            skip_validation=False,
            output_format="csv",
            timestep=(),
            daily=(),
            hourly=(),
            monthly=(),
            add_stochastic_schedules=False,
            add_timeseries_output_variable=(),
        )

        assert "--timestep" not in flags
        assert "--daily" not in flags
        assert "--hourly" not in flags
        assert "--monthly" not in flags
        assert "--add-timeseries-output-variable" not in flags

    def test_single_output_categories(self):
        """Test single output categories are handled correctly."""
        flags = _build_simulation_flags(
            add_component_loads=False,
            debug=False,
            skip_validation=False,
            output_format="csv",
            timestep=("total",),
            daily=("fuels",),
            hourly=("ALL",),
            monthly=("emissions",),
            add_stochastic_schedules=False,
            add_timeseries_output_variable=("Zone Air Temperature",),
        )

        assert "--timestep total" in flags
        assert "--daily fuels" in flags
        assert "--hourly ALL" in flags
        assert "--monthly emissions" in flags
        assert "--add-timeseries-output-variable Zone Air Temperature" in flags

    def test_multiple_output_categories(self):
        """Test multiple output categories are handled correctly."""
        flags = _build_simulation_flags(
            add_component_loads=False,
            debug=False,
            skip_validation=False,
            output_format="csv",
            timestep=("total", "fuels", "enduses"),
            daily=(),
            hourly=("loads", "temperatures"),
            monthly=(),
            add_stochastic_schedules=False,
            add_timeseries_output_variable=("Zone Air Temperature", "Zone Air Humidity"),
        )

        assert "--timestep total --timestep fuels --timestep enduses" in flags
        assert "--hourly loads --hourly temperatures" in flags
        assert (
            "--add-timeseries-output-variable Zone Air Temperature --add-timeseries-output-variable Zone Air Humidity"
            in flags
        )

    def test_none_values_handled_safely(self):
        """Test that None values don't cause errors."""
        flags = _build_simulation_flags(
            add_component_loads=True,
            debug=False,
            skip_validation=False,
            output_format="csv",
            timestep=None,
            daily=None,
            hourly=None,
            monthly=None,
            add_stochastic_schedules=False,
            add_timeseries_output_variable=None,
        )

        # Should not crash and should not contain any of these flags
        assert "--timestep" not in flags
        assert "--daily" not in flags
        assert "--hourly" not in flags
        assert "--monthly" not in flags
        assert "--add-timeseries-output-variable" not in flags

    def test_single_string_values_converted(self):
        """Test that single string values are converted to tuples."""
        flags = _build_simulation_flags(
            add_component_loads=False,
            debug=False,
            skip_validation=False,
            output_format="csv",
            timestep="total",  # Single string instead of tuple
            daily=(),
            hourly=(),
            monthly=(),
            add_stochastic_schedules=False,
            add_timeseries_output_variable="Zone Air Temperature",  # Single string
        )

        assert "--timestep total" in flags
        assert "--add-timeseries-output-variable Zone Air Temperature" in flags

    def test_integer_values_converted(self):
        """Test that integer values are converted to tuples (legacy compatibility)."""
        flags = _build_simulation_flags(
            add_component_loads=False,
            debug=False,
            skip_validation=False,
            output_format="csv",
            timestep=60,  # Integer instead of tuple
            daily=(),
            hourly=(),
            monthly=(),
            add_stochastic_schedules=False,
            add_timeseries_output_variable=(),
        )

        # Should handle gracefully, even though 60 is not a valid output category
        assert "--timestep 60" in flags

    def test_output_format_variations(self):
        """Test different output format options."""
        for fmt in ["csv", "json", "msgpack", "csv_dview"]:
            flags = _build_simulation_flags(
                add_component_loads=False,
                debug=False,
                skip_validation=False,
                output_format=fmt,
                timestep=(),
                daily=(),
                hourly=(),
                monthly=(),
                add_stochastic_schedules=False,
                add_timeseries_output_variable=(),
            )
            assert f"--output-format {fmt}" in flags

    def test_stochastic_schedules_flag(self):
        """Test stochastic schedules flag."""
        flags = _build_simulation_flags(
            add_component_loads=False,
            debug=False,
            skip_validation=False,
            output_format="csv",
            timestep=(),
            daily=(),
            hourly=(),
            monthly=(),
            add_stochastic_schedules=True,
            add_timeseries_output_variable=(),
        )

        assert "--add-stochastic-schedules" in flags

    def test_complex_real_world_scenario(self):
        """Test a complex real-world scenario with multiple flags."""
        flags = _build_simulation_flags(
            add_component_loads=True,
            debug=True,
            skip_validation=False,
            output_format="json",
            timestep=(),  # No timestep outputs for performance
            daily=("total", "fuels"),
            hourly=("ALL",),  # All hourly outputs
            monthly=("emissions", "loads"),
            add_stochastic_schedules=True,
            add_timeseries_output_variable=(
                "Zone Air Temperature",
                "Zone Mean Radiant Temperature",
            ),
        )

        # Verify all expected components are present
        assert "--add-component-loads" in flags
        assert "--debug" in flags
        assert "--output-format json" in flags
        assert "--daily total --daily fuels" in flags
        assert "--hourly ALL" in flags
        assert "--monthly emissions --monthly loads" in flags
        assert "--add-stochastic-schedules" in flags
        assert (
            "--add-timeseries-output-variable Zone Air Temperature --add-timeseries-output-variable Zone Mean Radiant Temperature"
            in flags
        )

        # Verify timestep is not present (empty tuple)
        assert "--timestep" not in flags

    def test_return_type_is_string(self):
        """Test that the function returns a string."""
        flags = _build_simulation_flags(
            add_component_loads=False,
            debug=False,
            skip_validation=False,
            output_format="csv",
            timestep=(),
            daily=(),
            hourly=(),
            monthly=(),
            add_stochastic_schedules=False,
            add_timeseries_output_variable=(),
        )

        assert isinstance(flags, str)
