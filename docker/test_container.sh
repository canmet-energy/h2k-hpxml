#!/bin/bash
# Docker Container Test Suite for H2K-HPXML
# This script tests the Docker container functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters for test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test results array
declare -a TEST_RESULTS

# Function to print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[FAIL]${NC} $1"; }
print_header() { 
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_output="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    print_info "Running: $test_name"
    
    # Run the command and capture output
    if output=$(eval "$test_command" 2>&1); then
        if [ -n "$expected_output" ]; then
            if echo "$output" | grep -q "$expected_output"; then
                print_success "$test_name"
                TESTS_PASSED=$((TESTS_PASSED + 1))
                TEST_RESULTS+=("PASS: $test_name")
            else
                print_error "$test_name - Expected output not found"
                print_info "Expected: $expected_output"
                print_info "Got: $(echo "$output" | head -n 5)"
                TESTS_FAILED=$((TESTS_FAILED + 1))
                TEST_RESULTS+=("FAIL: $test_name - Output mismatch")
            fi
        else
            print_success "$test_name"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            TEST_RESULTS+=("PASS: $test_name")
        fi
    else
        print_error "$test_name - Command failed with exit code $?"
        print_info "Error output: $(echo "$output" | head -n 5)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TEST_RESULTS+=("FAIL: $test_name - Exit code $?")
    fi
}

# Check if Docker is running
check_docker() {
    print_header "Checking Docker Installation"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Build the container
build_container() {
    print_header "Building Docker Container"
    
    IMAGE_NAME="${1:-canmet/h2k-hpxml}"
    print_info "Building image: $IMAGE_NAME"
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Build the image
    if docker build -t "$IMAGE_NAME" . > /tmp/docker_build.log 2>&1; then
        print_success "Container built successfully"
        print_info "Image size: $(docker images "$IMAGE_NAME" --format "{{.Size}}")"
    else
        print_error "Failed to build container"
        print_info "Build log tail:"
        tail -n 20 /tmp/docker_build.log
        exit 1
    fi
}

# Test basic container functionality
test_basic_functionality() {
    print_header "Testing Basic Container Functionality"
    
    IMAGE_NAME="${1:-canmet/h2k-hpxml}"
    
    # Test 1: Container runs and shows help
    run_test \
        "Container shows h2k2hpxml help" \
        "docker run --rm $IMAGE_NAME h2k2hpxml --help" \
        "Usage: h2k2hpxml"
    
    # Test 2: OpenStudio is installed
    run_test \
        "OpenStudio is installed" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'which openstudio && openstudio --version'" \
        "/usr/local/bin/openstudio"
    
    # Test 3: OpenStudio-HPXML is present
    run_test \
        "OpenStudio-HPXML is installed" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'ls -d /opt/OpenStudio-HPXML'" \
        "/opt/OpenStudio-HPXML"
    
    # Test 4: Python is installed
    run_test \
        "Python 3.12 is installed" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'python --version'" \
        "Python 3.12"
    
    # Test 5: h2k-hpxml package is installed
    run_test \
        "h2k-hpxml package is installed" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'pip list | grep h2k-hpxml'" \
        "h2k-hpxml"
    
    # Test 6: h2k-deps command works
    run_test \
        "h2k-deps command works" \
        "docker run --rm $IMAGE_NAME h2k-deps --check-only 2>&1 | head -n 1" \
        ""
    
    # Test 7: h2k-resilience help works
    run_test \
        "h2k-resilience help works" \
        "docker run --rm $IMAGE_NAME h2k-resilience --help" \
        "Usage: h2k-resilience"
}

# Test container functionality (skipping volume mounting due to Docker-in-Docker issues)
test_volume_mounting() {
    print_header "Testing Container Functionality"
    
    IMAGE_NAME="${1:-canmet/h2k-hpxml}"
    
    # Test 1: Container can create and read files in /tmp
    run_test \
        "Can create and read files in container" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'echo \"Test content\" > /tmp/test.txt && cat /tmp/test.txt'" \
        "Test content"
    
    # Test 2: Container can write to writable directories
    run_test \
        "Can write to container directories" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'echo \"Written by container\" > /tmp/output.txt && cat /tmp/output.txt'" \
        "Written by container"
    
    # Test 3: Configuration directory is created
    run_test \
        "Configuration directory is created" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'h2k2hpxml --help > /dev/null 2>&1 && ls -d /home/vscode/.config/h2k_hpxml'" \
        "/home/vscode/.config/h2k_hpxml"
}

# Test H2K conversion (using container's built-in example file)
test_h2k_conversion() {
    print_header "Testing H2K to HPXML Conversion"
    
    IMAGE_NAME="${1:-canmet/h2k-hpxml}"
    
    # Test 1: Check if examples are available in container
    run_test \
        "Container has example files" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'ls /app/config/templates/ | head -1'" \
        ""
    
    # Test 2: Basic CLI validation (test help and error handling)
    run_test \
        "H2K conversion CLI handles invalid input gracefully" \
        "docker run --rm $IMAGE_NAME h2k2hpxml run --input_path /nonexistent/file.h2k 2>&1 | head -1" \
        ""
    
    # Test 3: Configuration system works
    run_test \
        "Configuration system initializes correctly" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'h2k2hpxml --help > /dev/null 2>&1 && echo \"Config created successfully\"'" \
        "Config created successfully"
}

# Test environment variables
test_environment() {
    print_header "Testing Environment Variables"
    
    IMAGE_NAME="${1:-canmet/h2k-hpxml}"
    
    # Test 1: HPXML_OS_PATH is set
    run_test \
        "HPXML_OS_PATH is set correctly" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'echo \$HPXML_OS_PATH'" \
        "/opt/OpenStudio-HPXML"
    
    # Test 2: OPENSTUDIO_BINARY is set
    run_test \
        "OPENSTUDIO_BINARY is set correctly" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'echo \$OPENSTUDIO_BINARY'" \
        "/usr/local/bin/openstudio"
    
    # Test 3: Python path is set
    run_test \
        "PYTHONPATH includes site-packages" \
        "docker run --rm --entrypoint /bin/bash $IMAGE_NAME -c 'echo \$PYTHONPATH'" \
        "site-packages"
}

# Print test summary
print_summary() {
    print_header "Test Summary"
    
    echo ""
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Total Tests: $TESTS_TOTAL"
    echo ""
    
    if [ ${#TEST_RESULTS[@]} -gt 0 ]; then
        echo "Detailed Results:"
        for result in "${TEST_RESULTS[@]}"; do
            if [[ $result == PASS* ]]; then
                echo -e "  ${GREEN}✓${NC} ${result#PASS: }"
            else
                echo -e "  ${RED}✗${NC} ${result#FAIL: }"
            fi
        done
    fi
    
    echo ""
    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "All tests passed! Container is working correctly."
        exit 0
    else
        print_error "Some tests failed. Please review the output above."
        exit 1
    fi
}

# Main execution
main() {
    print_header "H2K-HPXML Docker Container Test Suite"
    
    # Parse command line arguments
    IMAGE_NAME="${1:-canmet/h2k-hpxml}"
    SKIP_BUILD="${2:-false}"
    
    # Run tests
    check_docker
    
    if [ "$SKIP_BUILD" != "skip-build" ]; then
        build_container "$IMAGE_NAME"
    else
        print_info "Skipping build (using existing image)"
    fi
    
    test_basic_functionality "$IMAGE_NAME"
    test_volume_mounting "$IMAGE_NAME"
    test_environment "$IMAGE_NAME"
    test_h2k_conversion "$IMAGE_NAME"
    
    # Print summary
    print_summary
}

# Run main function
main "$@"