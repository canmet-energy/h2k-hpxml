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

# Function to detect Python version from pyproject.toml
detect_python_version() {
    local project_root="/workspaces/h2k-hpxml"
    local pyproject_file="$project_root/pyproject.toml"
    
    if [ -f "$pyproject_file" ]; then
        # Extract Python version using same method as Dockerfile
        local python_version=$(grep "requires-python" "$pyproject_file" | grep -o "[0-9]\+\.[0-9]\+" | head -1)
        if [ -n "$python_version" ]; then
            echo "$python_version"
            return 0
        fi
    fi
    
    # Fallback to default version if detection fails
    echo "3.12"
}

setup_claude_mcp_servers() {
    if [ "$CLAUDE_INSTALLED" != true ]; then
        log_warning "Claude not installed, skipping MCP setup"
        return 1
    fi
    
    log_step "Configuring MCP servers for Claude CLI..."
    
    # Detect Python version dynamically
    local python_version=$(detect_python_version)
    log_info "Using Python version: $python_version"
    
    # Check if uv is available (required for MCP servers)
    if ! command -v uv >/dev/null 2>&1; then
        log_warning "uv not found - MCP servers require uv to be installed"
        log_info "Install uv manually if needed: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    # Configure Serena MCP server for Claude
    log_info "Adding Serena MCP server to Claude configuration..."
    if claude mcp add serena -- uv tool run --python "$python_version" --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project "." 2>/dev/null; then
        log_success "Serena MCP server added to Claude"
    else
        log_info "Serena MCP server already exists in Claude configuration or failed to add"
    fi
    
    # Configure AWS MCP server if AWS credentials are available
    if [ -f "$HOME/.aws/credentials" ] || [ -n "$AWS_ACCESS_KEY_ID" ]; then
        log_info "Adding AWS MCP server to Claude configuration..."
        if claude mcp add awslabs-ccapi-mcp-server \
          -e DEFAULT_TAGS=enabled \
          -e SECURITY_SCANNING=enabled \
          -e FASTMCP_LOG_LEVEL=ERROR \
          -- uv tool run --python "$python_version" --from awslabs.ccapi-mcp-server@latest awslabs.ccapi-mcp-server --readonly 2>/dev/null; then
            log_success "AWS MCP server added to Claude"
        else
            log_info "AWS MCP server already exists in Claude configuration or failed to add"
        fi
    else
        log_info "AWS credentials not available - skipping AWS MCP server configuration"
    fi
    
    # Verify MCP server configuration
    log_info "Verifying Claude MCP server configuration..."
    local mcp_count=$(claude mcp list 2>/dev/null | grep -E "serena|awslabs" | wc -l)
    if [ "$mcp_count" -gt 0 ]; then
        log_success "Claude MCP servers configured successfully ($mcp_count servers)"
        export CLAUDE_MCP_CONFIGURED=true
        
        # Test Serena MCP server availability (non-blocking)
        log_info "Testing Serena MCP server availability..."
        if timeout 10 uv tool run --python "$python_version" --from git+https://github.com/oraios/serena serena --help >/dev/null 2>&1; then
            log_success "Serena MCP server is accessible"
        else
            log_warning "Serena MCP server test timed out or failed (may work in actual usage)"
        fi
    else
        log_warning "No MCP servers found in Claude configuration"
        export CLAUDE_MCP_CONFIGURED=false
    fi
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
    setup_claude_mcp_servers
    
    if [ "$CLAUDE_INSTALLED" = true ]; then
        log_success "Claude CLI setup complete"
        if [ "$CLAUDE_MCP_CONFIGURED" = true ]; then
            log_success "MCP servers configured for Claude"
            log_info "Available MCP servers:"
            claude mcp list 2>/dev/null || true
        else
            log_info "MCP servers not configured (may require uv installation)"
        fi
        log_info "To authenticate: claude auth"
    else
        log_error "Claude CLI setup failed"
        exit 1
    fi
fi