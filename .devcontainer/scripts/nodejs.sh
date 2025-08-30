#!/bin/bash
# Node.js installation for devcontainer environment

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Install Node.js from official binary distribution
install_nodejs_binary() {
    log_info "Installing Node.js from official binary distribution..."
    
    local node_version="18.20.4"  # LTS version
    local node_arch="x64"
    local node_url="https://nodejs.org/dist/v${node_version}/node-v${node_version}-linux-${node_arch}.tar.xz"
    local install_dir="/usr/local"
    local temp_dir="/tmp/nodejs-install"
    
    # Create temporary directory
    mkdir -p "$temp_dir"
    cd "$temp_dir"
    
    # Configure curl for corporate network if in Docker build
    local curl_opts="-fsSL --connect-timeout 30"
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        curl_opts="$curl_opts -k"  # Skip SSL verification for corporate networks
        log_info "Using SSL workarounds for binary download"
    fi
    
    # Download Node.js binary with retry logic
    local download_success=false
    for attempt in 1 2 3; do
        log_info "Downloading Node.js binary (attempt $attempt/3)..."
        if curl $curl_opts -o "node.tar.xz" "$node_url"; then
            download_success=true
            break
        else
            log_warning "Download attempt $attempt failed, retrying..."
            sleep 3
        fi
    done
    
    if [ "$download_success" = false ]; then
        log_error "Failed to download Node.js binary after 3 attempts"
        return 1
    fi
    
    # Extract and install
    log_info "Extracting and installing Node.js..."
    tar -xJf node.tar.xz
    local extracted_dir=$(find . -maxdepth 1 -name "node-v*" -type d | head -n1)
    
    if [ -z "$extracted_dir" ]; then
        log_error "Failed to find extracted Node.js directory"
        return 1
    fi
    
    # Install Node.js files
    sudo cp -r "$extracted_dir"/* "$install_dir/"
    
    # Create symlinks if they don't exist
    sudo ln -sf "$install_dir/bin/node" /usr/bin/node
    sudo ln -sf "$install_dir/bin/npm" /usr/bin/npm
    sudo ln -sf "$install_dir/bin/npx" /usr/bin/npx
    
    # Clean up
    cd /
    rm -rf "$temp_dir"
    
    # Verify installation
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        local installed_version=$(node --version)
        local npm_version=$(npm --version)
        log_success "Node.js $installed_version and npm $npm_version installed successfully from binary"
        
        # Configure npm for corporate environment
        configure_npm_for_corporate
        export NODEJS_INSTALLED=true
        return 0
    else
        log_error "Node.js binary installation verification failed"
        return 1
    fi
}

# Install Node.js using NodeSource repository (for runtime)
install_nodejs_repository() {
    log_info "Installing Node.js using NodeSource repository..."
    
    # Install Node.js 18.x LTS
    log_info "Adding NodeSource repository for Node.js 18.x..."
    
    # Ensure certificates are properly configured
    export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
    export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
    
    # Configure curl for corporate network
    local curl_config=""
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        # During Docker build, use insecure options for corporate network
        curl_config="-k --connect-timeout 30"
        log_info "Docker build context detected - using SSL workarounds for NodeSource"
    else
        curl_config="--connect-timeout 30"
    fi
    
    # Download and add NodeSource GPG key and repository with retry logic
    local setup_success=false
    for attempt in 1 2 3; do
        log_info "NodeSource setup attempt $attempt of 3..."
        if curl -fsSL $curl_config https://deb.nodesource.com/setup_18.x | sudo -E bash - >/dev/null 2>&1; then
            setup_success=true
            break
        else
            log_warning "NodeSource setup attempt $attempt failed, retrying..."
            sleep 2
        fi
    done
    
    if [ "$setup_success" = false ]; then
        log_error "Failed to add NodeSource repository after 3 attempts"
        return 1
    fi
    
    # Install Node.js and npm
    log_info "Installing Node.js and npm packages..."
    
    # Configure apt for corporate network during Docker build
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        # Create apt configuration for SSL issues
        echo 'Acquire::https::Verify-Peer "false";' | sudo tee /etc/apt/apt.conf.d/99-ssl-workaround >/dev/null
        echo 'Acquire::https::Verify-Host "false";' | sudo tee -a /etc/apt/apt.conf.d/99-ssl-workaround >/dev/null
        log_info "apt configured with SSL workarounds for Docker build"
    fi
    
    # Update package list first
    sudo apt-get update >/dev/null 2>&1
    
    # Try to install Node.js with retry logic
    local install_success=false
    for attempt in 1 2 3; do
        log_info "Node.js installation attempt $attempt of 3..."
        if sudo apt-get install -y nodejs >/dev/null 2>&1; then
            install_success=true
            break
        else
            log_warning "Node.js installation attempt $attempt failed, retrying..."
            sleep 3
        fi
    done
    
    # Clean up SSL workaround configuration after installation
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        sudo rm -f /etc/apt/apt.conf.d/99-ssl-workaround >/dev/null 2>&1 || true
    fi
    
    if [ "$install_success" = false ]; then
        log_error "Failed to install Node.js package after 3 attempts"
        return 1
    fi

    # Verify installation
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        local node_version=$(node --version)
        local npm_version=$(npm --version)
        log_success "Node.js $node_version and npm $npm_version installed successfully from repository"
        
        # Configure npm for corporate environment
        configure_npm_for_corporate
        export NODEJS_INSTALLED=true
        return 0
    else
        log_error "Node.js repository installation verification failed"
        return 1
    fi
}

# Configure npm for corporate environment
configure_npm_for_corporate() {
    log_info "Configuring npm for corporate environment..."
    
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        # During Docker build, use more aggressive SSL workarounds
        npm config set ca ""
        npm config set strict-ssl false
        npm config set registry https://registry.npmjs.org/
        log_info "npm configured for Docker build with SSL workarounds"
    else
        # Runtime configuration
        npm config set ca ""
        npm config set strict-ssl false
        log_info "npm configured for corporate environment"
    fi
}

install_nodejs() {
    log_step "Installing Node.js and npm..."
    
    # Check if Node.js is already installed
    if command -v node >/dev/null 2>&1; then
        local node_version=$(node --version 2>/dev/null)
        log_info "Node.js already installed: $node_version"
        
        # Check if version is acceptable (18.x or higher)
        local major_version=$(echo "$node_version" | sed 's/v\([0-9]*\).*/\1/')
        if [ "$major_version" -ge 18 ]; then
            log_success "Node.js version is acceptable"
            export NODEJS_INSTALLED=true
            return 0
        else
            log_warning "Node.js version $node_version is too old, upgrading..."
        fi
    fi
    
    # Try different installation methods based on context
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        # Docker build context - use direct binary installation to avoid repository issues
        log_info "Docker build context - installing Node.js from official binaries"
        install_nodejs_binary
    else
        # Runtime context - try NodeSource first, fallback to binary
        log_info "Runtime context - trying NodeSource repository installation"
        install_nodejs_repository || install_nodejs_binary
    fi

    # Final verification
    if [ "$NODEJS_INSTALLED" != true ]; then
        log_error "All Node.js installation methods failed"
        return 1
    fi
}

install_nodejs() {
    log_step "Installing Node.js and npm..."
    
    # Check if Node.js is already installed
    if command -v node >/dev/null 2>&1; then
        local node_version=$(node --version 2>/dev/null)
        log_info "Node.js already installed: $node_version"
        
        # Check if version is acceptable (18.x or higher)
        local major_version=$(echo "$node_version" | sed 's/v\([0-9]*\).*/\1/')
        if [ "$major_version" -ge 18 ]; then
            log_success "Node.js version is acceptable"
            export NODEJS_INSTALLED=true
            return 0
        else
            log_warning "Node.js version $node_version is too old, upgrading..."
        fi
    fi
    
    # Try different installation methods based on context
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        # Docker build context - use direct binary installation to avoid repository issues
        log_info "Docker build context - installing Node.js from official binaries"
        install_nodejs_binary
    else
        # Runtime context - try NodeSource first, fallback to binary
        log_info "Runtime context - trying NodeSource repository installation"
        install_nodejs_repository || install_nodejs_binary
    fi
}
    
    # Install Node.js 18.x LTS
    log_info "Adding NodeSource repository for Node.js 18.x..."
    
    # Ensure certificates are properly configured
    export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
    export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
    
    # Configure curl for corporate network
    local curl_config=""
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        # During Docker build, use insecure options for corporate network
        curl_config="-k --connect-timeout 30"
        log_info "Docker build context detected - using SSL workarounds for NodeSource"
    else
        curl_config="--connect-timeout 30"
    fi
    
    # Download and add NodeSource GPG key and repository with retry logic
    local setup_success=false
    for attempt in 1 2 3; do
        log_info "NodeSource setup attempt $attempt of 3..."
        if curl -fsSL $curl_config https://deb.nodesource.com/setup_18.x | sudo -E bash - >/dev/null 2>&1; then
            setup_success=true
            break
        else
            log_warning "NodeSource setup attempt $attempt failed, retrying..."
            sleep 2
        fi
    done
    
    if [ "$setup_success" = false ]; then
        log_error "Failed to add NodeSource repository after 3 attempts"
        return 1
    fi
    
    # Install Node.js and npm
    log_info "Installing Node.js and npm packages..."
    
    # Configure apt for corporate network during Docker build
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        # Create apt configuration for SSL issues
        echo 'Acquire::https::Verify-Peer "false";' | sudo tee /etc/apt/apt.conf.d/99-ssl-workaround >/dev/null
        echo 'Acquire::https::Verify-Host "false";' | sudo tee -a /etc/apt/apt.conf.d/99-ssl-workaround >/dev/null
        log_info "apt configured with SSL workarounds for Docker build"
    fi
    
    # Update package list first
    sudo apt-get update >/dev/null 2>&1
    
    # Try to install Node.js with retry logic
    local install_success=false
    for attempt in 1 2 3; do
        log_info "Node.js installation attempt $attempt of 3..."
        if sudo apt-get install -y nodejs >/dev/null 2>&1; then
            install_success=true
            break
        else
            log_warning "Node.js installation attempt $attempt failed, retrying..."
            sleep 3
        fi
    done
    
    # Clean up SSL workaround configuration after installation
    if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
        sudo rm -f /etc/apt/apt.conf.d/99-ssl-workaround >/dev/null 2>&1 || true
    fi
    
    if [ "$install_success" = false ]; then
        log_error "Failed to install Node.js package after 3 attempts"
        return 1
    fi
    
    # Verify installation
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        local node_version=$(node --version)
        local npm_version=$(npm --version)
        log_success "Node.js $node_version and npm $npm_version installed successfully"
        
        # Configure npm for corporate environment
        if [ "$DOCKER_BUILD_CONTEXT" = "true" ]; then
            # During Docker build, use more aggressive SSL workarounds
            npm config set ca ""
            npm config set strict-ssl false
            npm config set registry https://registry.npmjs.org/
            log_info "npm configured for Docker build with SSL workarounds"
        else
            # Runtime configuration
            npm config set ca ""
            npm config set strict-ssl false
            log_info "npm configured for corporate environment"
        fi
        
        export NODEJS_INSTALLED=true
    else
        log_error "Node.js installation failed"
        export NODEJS_INSTALLED=false
        return 1
    fi
}

# Run Node.js installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_step "Starting Node.js installation..."
    check_sudo
    install_nodejs
    
    if [ "$NODEJS_INSTALLED" = true ]; then
        log_success "Node.js setup complete"
    else
        log_error "Node.js setup failed"
        exit 1
    fi
fi