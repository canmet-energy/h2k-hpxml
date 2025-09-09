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
    """Configure pytest markers and platform-aware filtering."""
    config.addinivalue_line(
        "markers",
        "baseline_generation: mark test as baseline generation (requires --run-baseline flag)",
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test (validates against baseline)"
    )

    # Platform-aware test filtering (unless --force-all is specified)
    if not config.getoption("--force-all"):
        # Only apply platform filtering if no explicit marker expression is provided
        if not config.getoption("-m") and not config.getoption("--markers"):
            if sys.platform == "win32":
                # On Windows, skip Linux-specific tests
                config.option.markexpr = "not linux"
            elif sys.platform in ["linux", "linux2", "darwin"]:
                # On Linux/Unix, skip Windows-specific tests
                config.option.markexpr = "not windows"


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle baseline generation tests and add platform information."""
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

    # Add platform information to test collection for debugging
    platform_info = f"Running on {sys.platform}"
    if config.option.markexpr:
        platform_info += f" with marker filter: {config.option.markexpr}"

    # Print platform info during collection if verbose
    if config.option.verbose >= 1:
        print(f"\n{platform_info}")


def pytest_sessionstart(session):
    """Print platform information at session start if requested."""
    config = session.config

    if config.getoption("--platform-info"):
        print("\nPlatform Information:")
        print(f"  System: {sys.platform}")
        print(f"  Python: {sys.version.split()[0]}")
        if config.option.markexpr:
            print(f"  Test filter: {config.option.markexpr}")
        else:
            print("  Test filter: None (running all tests)")

    if config.getoption("--force-all"):
        # Clear any automatic platform filtering
        config.option.markexpr = ""


@pytest.fixture(scope="session")
def check_openstudio_bindings():
    """Ensure OpenStudio Python bindings are available before running tests."""
    try:
        import openstudio
    except ImportError:
        pytest.skip("OpenStudio Python bindings are not installed.")
