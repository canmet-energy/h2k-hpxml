#!/bin/bash
# Claude CLI installation and configuration

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

install_claude() {
    log_step "Installing Claude CLI..."
    
    # Check if Node.js installation was deferred
    if [ "$NODEJS_DEFERRED" = true ] || [ "$DOCKER_BUILD_CONTEXT" = "true" ] && ! command -v node >/dev/null 2>&1; then
        log_info "Node.js not available during Docker build - deferring Claude CLI installation to runtime"
        # Create marker file for runtime installation
        touch "$HOME/.nodejs_deferred_claude" 2>/dev/null || true
        export CLAUDE_DEFERRED=true
        return 0
    fi
    
    # Check if Claude is already installed
    if command -v claude >/dev/null 2>&1; then
        local claude_version=$(claude --version 2>/dev/null || echo "unknown")
        log_info "Claude CLI already installed: $claude_version"
        
        # Check if it's working properly
        if claude --help >/dev/null 2>&1; then
            log_success "Claude CLI is functional"
            export CLAUDE_INSTALLED=true
            return 0
        else
            log_warning "Claude CLI installed but not functional, reinstalling..."
        fi
    fi
    
    # Ensure certificate environment variables are set for npm
    export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
    export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
    export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    
    log_info "Installing Claude CLI with certificate support..."
    
    # Try multiple installation methods for robustness
    local install_success=false
    
    # Method 1: Standard npm install with certificates
    if sudo -E NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt npm install -g @anthropic-ai/claude-code >/dev/null 2>&1; then
        log_info "Claude installed using standard method"
        install_success=true
    # Method 2: With --unsafe-perm
    elif sudo -E NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt npm install -g @anthropic-ai/claude-code --unsafe-perm >/dev/null 2>&1; then
        log_info "Claude installed using --unsafe-perm method"
        install_success=true
    # Method 3: With strict-ssl disabled (last resort)
    elif sudo -E NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt npm install -g @anthropic-ai/claude-code --unsafe-perm --strict-ssl=false >/dev/null 2>&1; then
        log_warning "Claude installed with strict-ssl disabled"
        install_success=true
    else
        log_error "All Claude installation methods failed"
        export CLAUDE_INSTALLED=false
        return 1
    fi
    
    # Verify installation
    if ! command -v claude >/dev/null 2>&1; then
        log_error "Claude command not found after installation"
        export CLAUDE_INSTALLED=false
        return 1
    fi
    
    # Get version and verify functionality
    local claude_version=$(claude --version 2>/dev/null || echo "version unknown")
    log_success "Claude CLI installed successfully ($claude_version)"
    
    # Clear any existing authentication to ensure clean state
    rm -f "$HOME/.config/claude-code/auth.json" 2>/dev/null
    log_info "Cleared existing Claude authentication (will need to re-authenticate)"
    
    export CLAUDE_INSTALLED=true
}

setup_claude_environment() {
    if [ "$CLAUDE_INSTALLED" != true ]; then
        log_warning "Claude not installed, skipping environment setup"
        return 1
    fi
    
    log_step "Configuring Claude environment..."
    
    # Add certificate environment variables to .bashrc for persistence
    local bashrc="/home/vscode/.bashrc"
    
    # Check if variables are already in .bashrc
    if ! grep -q "NODE_EXTRA_CA_CERTS" "$bashrc" 2>/dev/null; then
        log_info "Adding certificate environment variables to .bashrc..."
        {
            echo ""
            echo "# Claude CLI Certificate Configuration (added by claude.sh)"
            echo "export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt"
            echo "export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt"
            echo "export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt"
            echo "export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt"
        } >> "$bashrc"
        log_success "Certificate environment variables added to .bashrc"
    else
        log_info "Certificate environment variables already configured in .bashrc"
    fi
}

# Run Claude installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_step "Starting Claude CLI installation..."
    
    # Check for Node.js prerequisite
    if ! command -v node >/dev/null 2>&1; then
        log_error "Node.js is required for Claude CLI installation"
        log_info "Please run nodejs.sh first"
        exit 1
    fi
    
    check_sudo
    install_claude
    setup_claude_environment
    
    if [ "$CLAUDE_INSTALLED" = true ]; then
        log_success "Claude CLI setup complete"
        log_info "To authenticate: claude auth"
    else
        log_error "Claude CLI setup failed"
        exit 1
    fi
fi