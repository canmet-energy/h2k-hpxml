import pytest


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--run-baseline",
        action="store_true",
        default=False,
        help="Enable baseline generation tests (WARNING: overwrites golden files)",
    )


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "baseline_generation: mark test as baseline generation (requires --run-baseline flag)",
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test (validates against baseline)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle baseline generation tests."""
    if config.getoption("--run-baseline"):
        # Remove skip marker from baseline generation tests
        for item in items:
            if "baseline_generation" in item.keywords:
                # Remove the skip marker by creating a new list without skip markers
                item.own_markers = [mark for mark in item.own_markers if not (mark.name == "skip")]
    else:
        # Ensure baseline generation tests are skipped
        skip_baseline = pytest.mark.skip(
            reason="Need --run-baseline flag to run baseline generation"
        )
        for item in items:
            if "baseline_generation" in item.keywords:
                item.add_marker(skip_baseline)


@pytest.fixture(scope="session")
def check_openstudio_bindings():
    """Ensure OpenStudio Python bindings are available before running tests."""
    try:
        import openstudio
    except ImportError:
        pytest.skip("OpenStudio Python bindings are not installed.")
