#!/bin/bash
# Runtime Node.js installation for devcontainer environment
# This runs during postCreateCommand when network access is more reliable

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

install_nodejs_runtime() {
    log_step "Installing Node.js at runtime (deferred from Docker build)"
    
    # Check if Node.js is already installed
    if command -v node >/dev/null 2>&1; then
        local node_version=$(node --version 2>/dev/null)
        log_info "Node.js already installed: $node_version"
        
        # Check if version is acceptable (18.x or higher)
        local major_version=$(echo "$node_version" | sed 's/v\([0-9]*\).*/\1/')
        if [ "$major_version" -ge 18 ]; then
            log_success "Node.js version is acceptable"
            return 0
        else
            log_warning "Node.js version $node_version is too old, upgrading..."
        fi
    fi
    
    # Install Node.js 18.x LTS at runtime (better network conditions)
    log_info "Adding NodeSource repository for Node.js 18.x..."
    
    # Configure environment for runtime installation
    export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
    export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
    
    # Download and add NodeSource GPG key and repository (runtime has better network)
    if curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - >/dev/null 2>&1; then
        log_info "NodeSource repository added successfully"
    else
        log_warning "NodeSource setup failed, trying fallback approach..."
        # Fallback: Use default Ubuntu Node.js (may be older version)
        sudo apt-get update >/dev/null 2>&1
        if sudo apt-get install -y nodejs npm >/dev/null 2>&1; then
            log_warning "Installed default Ubuntu Node.js (may be older version)"
        else
            log_error "Failed to install Node.js even with fallback"
            return 1
        fi
    fi
    
    # Install Node.js and npm packages
    log_info "Installing Node.js and npm packages..."
    sudo apt-get update >/dev/null 2>&1
    
    if sudo apt-get install -y nodejs >/dev/null 2>&1; then
        log_success "Node.js installed successfully at runtime"
    else
        log_error "Failed to install Node.js at runtime"
        return 1
    fi
    
    # Verify installation and configure npm
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        local node_version=$(node --version)
        local npm_version=$(npm --version)
        log_success "Node.js $node_version and npm $npm_version installed successfully"
        
        # Configure npm for corporate environment
        npm config set ca ""
        npm config set strict-ssl false
        npm config set registry https://registry.npmjs.org/
        log_info "npm configured for corporate environment"
        
        # Install Claude CLI if it was deferred
        if [ -f "$HOME/.nodejs_deferred_claude" ]; then
            log_info "Installing deferred Claude CLI..."
            npm install -g @anthropic-ai/claude-cli >/dev/null 2>&1
            if command -v claude >/dev/null 2>&1; then
                log_success "Claude CLI installed successfully"
                rm -f "$HOME/.nodejs_deferred_claude"
            else
                log_warning "Claude CLI installation may have failed"
            fi
        fi
        
        return 0
    else
        log_error "Node.js installation verification failed"
        return 1
    fi
}

# Only run if this script is executed directly or if Node.js is not available
if [[ "${BASH_SOURCE[0]}" == "${0}" ]] || ! command -v node >/dev/null 2>&1; then
    log_step "Starting runtime Node.js installation..."
    install_nodejs_runtime
    
    if command -v node >/dev/null 2>&1; then
        log_success "Runtime Node.js setup complete"
    else
        log_error "Runtime Node.js setup failed"
        exit 1
    fi
fi
