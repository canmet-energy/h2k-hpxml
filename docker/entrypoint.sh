#!/bin/bash
set -e

# H2K-HPXML Docker Entrypoint Script
# Handles CLI commands and sets up proper environment

# Set runtime flag for certificate installation
export CONTAINER_RUNTIME=true

# Install certificates at runtime if needed (skipped during build)
# Note: Certificate scripts are not copied to production containers
# Runtime certificate installation would need to be implemented separately if required

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Function to set up configuration
setup_config() {
    local config_dir="/data/.h2k-config"
    local config_file="$config_dir/conversionconfig.ini"
    
    # Create config directory if it doesn't exist
    mkdir -p "$config_dir"
    
    # Only create config if it doesn't exist
    if [ ! -f "$config_file" ]; then
        log_info "Creating configuration file at $config_file"
        
        # Copy template and configure paths
        cp /app/config/templates/conversionconfig.template.ini "$config_file"
        
        # The Python package will auto-detect OpenStudio and HPXML paths
        # Just set working directory paths
        sed -i "s|source_h2k_path = .*|source_h2k_path = /data|g" "$config_file"
        sed -i "s|output_hpxml_path = .*|output_hpxml_path = /data/output|g" "$config_file"
        sed -i "s|output_workflows_path = .*|output_workflows_path = /data/output/workflows|g" "$config_file"
        sed -i "s|output_comparisons_path = .*|output_comparisons_path = /data/output/comparisons|g" "$config_file"
        
        log_success "Configuration created"
    else
        log_info "Using existing configuration at $config_file"
    fi
    
    # Export config path for the application
    export H2K_CONFIG_PATH="$config_file"
}

# Function to ensure output directories exist
setup_output_dirs() {
    mkdir -p /data/output/hpxml
    mkdir -p /data/output/workflows
    mkdir -p /data/output/comparisons
    log_info "Output directories ready"
}

# Function to fix file permissions for mounted volumes
fix_permissions() {
    # Get the user ID from the mounted volume
    if [ -d "/data" ]; then
        local data_owner=$(stat -c "%u" /data 2>/dev/null || echo "1000")
        local data_group=$(stat -c "%g" /data 2>/dev/null || echo "1000")
        
        # If mounted as root (common in Docker), we need to be careful
        if [ "$data_owner" != "1000" ] && [ "$data_owner" != "0" ]; then
            log_warning "Volume mounted with UID $data_owner, running as UID 1000"
        fi
    fi
}

# Function to validate input file exists
validate_input() {
    local input_file="$1"
    
    if [ -z "$input_file" ]; then
        log_error "No input file specified"
        return 1
    fi
    
    if [ ! -f "$input_file" ]; then
        log_error "Input file not found: $input_file"
        log_info "Make sure the file is mounted into the container"
        log_info "Example: docker run -v /host/path:/data canmet/h2k-hpxml h2k2hpxml /data/file.h2k"
        return 1
    fi
    
    # Check file extension
    if [[ ! "$input_file" =~ \.(h2k|H2K)$ ]]; then
        log_warning "File does not have .h2k extension: $input_file"
    fi
    
    log_success "Input file validated: $input_file"
    return 0
}

# Function to show help for Docker usage
show_docker_help() {
    cat << 'EOF'

🐳 H2K-HPXML Docker Usage

Basic Commands:
  docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k
  docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-resilience /data/input.h2k

Volume Mounting:
  -v /host/input/path:/data           # Read/write access to host directory
  -v /host/input:/input:ro            # Read-only input directory  
  -v /host/output:/output             # Write-only output directory

Examples:
  # Convert H2K file in current directory
  docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/house.h2k

  # Separate input and output directories  
  docker run --rm \
    -v /path/to/input:/input:ro \
    -v /path/to/output:/output \
    canmet/h2k-hpxml h2k2hpxml /input/house.h2k --output /output/house.xml

  # Resilience analysis
  docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
    h2k-resilience /data/house.h2k --scenarios "outage_typical_year"

Environment Variables:
  H2K_LOG_LEVEL=DEBUG               # Enable debug logging
  H2K_CONFIG_PATH=/data/.h2k-config/conversionconfig.ini

Configuration:
  The container creates a configuration file at /data/.h2k-config/conversionconfig.ini
  This file is preserved between runs if you mount the /data volume.

EOF
}

# Function to ensure dependencies are installed
ensure_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if dependencies are already installed
    if [ -d "/app/deps/OpenStudio-HPXML" ] && [ -d "/app/deps/openstudio" ]; then
        log_success "Dependencies already installed"
        return 0
    fi
    
    log_warning "Dependencies not found. Installing on first run..."
    log_info "This may take a few minutes for the first container run."
    
    # Import h2k_hpxml which triggers ensure_dependencies()
    python -c "import h2k_hpxml" || {
        log_error "Failed to install dependencies"
        log_info "You may need to run 'h2k-deps --auto-install' manually"
        return 1
    }
    
    log_success "Dependencies installed successfully"
    return 0
}

# Main entrypoint logic
main() {
    log_info "H2K-HPXML Docker Container Starting..."
    
    # Set up environment
    fix_permissions
    setup_config
    setup_output_dirs
    
    # Ensure dependencies are installed
    ensure_dependencies || {
        log_error "Dependency installation failed"
        log_info "Try running: docker run --rm -v /app/deps:/app/deps canmet/h2k-hpxml h2k-deps --auto-install"
        exit 1
    }
    
    # If no arguments provided, show help
    if [ $# -eq 0 ]; then
        log_info "No command specified"
        show_docker_help
        exit 0
    fi
    
    # Handle special cases
    case "$1" in
        "help"|"--help"|"-h")
            show_docker_help
            exit 0
            ;;
        "bash"|"sh")
            log_info "Starting interactive shell..."
            exec /bin/bash
            ;;
        "h2k-deps")
            log_info "Running h2k-deps command..."
            # Let the Python package handle dependency management
            exec h2k-deps "${@:2}"
            ;;
    esac
    
    # Validate common CLI commands that need input files
    if [[ "$1" == "h2k2hpxml" || "$1" == "h2k-resilience" ]]; then
        if [ $# -ge 2 ]; then
            # Extract input file from arguments (second argument typically)
            local potential_input="$2"
            if [[ "$potential_input" != -* ]]; then  # Not a flag
                validate_input "$potential_input" || exit 1
            fi
        fi
    fi
    
    # Execute the command
    log_info "Executing: $*"
    
    # Change to /data directory for execution
    cd /data
    
    # Execute the command with all arguments
    exec "$@"
}

# Run main function with all arguments
main "$@"