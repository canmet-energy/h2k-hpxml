import sys

import pytest


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--run-baseline",
        action="store_true",
        default=False,
        help="Enable baseline generation tests (WARNING: overwrites golden files)",
    )
    parser.addoption(
        "--force-all",
        action="store_true",
        default=False,
        help="Force run all tests regardless of platform (useful for CI/CD)",
    )
    parser.addoption(
        "--platform-info",
        action="store_true",
        default=False,
        help="Show platform detection information",
    )


def pytest_configure(config):
    """Configure pytest with custom options."""
    # Markers are now defined in pyproject.toml
    # Platform filtering is handled by @pytest.mark.skipif decorators
    pass


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle baseline generation tests."""
    # Handle baseline generation tests
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

    # Print platform info during collection if verbose
    if config.option.verbose >= 1:
        print(f"\nRunning on {sys.platform}")


def pytest_sessionstart(session):
    """Print platform information at session start if requested."""
    config = session.config

    if config.getoption("--platform-info"):
        print("\nPlatform Information:")
        print(f"  System: {sys.platform}")
        print(f"  Python: {sys.version.split()[0]}")


@pytest.fixture(scope="session")
def check_openstudio_bindings():
    """Ensure OpenStudio Python bindings are available before running tests."""
    try:
        import openstudio
    except ImportError:
        pytest.skip("OpenStudio Python bindings are not installed.")
