#!/bin/bash
# VS Code MCP (Model Context Protocol) server configuration
# Configures MCP servers for use with VS Code extensions and features

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Function to detect Python version from pyproject.toml
detect_python_version() {
    local project_root="/workspaces/h2k_hpxml"
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

install_vscode_mcp_servers() {
    log_step "Setting up VS Code MCP servers..."
    
    # Detect Python version dynamically
    local python_version=$(detect_python_version)
    log_info "Using Python version: $python_version"
    
    # Create .vscode directory in home for global VS Code MCP configuration
    mkdir -p "$HOME/.vscode"
    
    # Create VS Code MCP configuration with dynamic Python version
    log_info "Creating VS Code MCP configuration..."
    cat > "$HOME/.vscode/mcp.json" << EOF
{
  "servers": {
    "serena": {
      "type": "stdio",
      "command": "uv",
      "args": ["tool", "run", "--python", "$python_version", "--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server", "--context", "ide-assistant", "--project", "."]
    },
    "awslabs-ccapi-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": ["tool", "run", "--python", "$python_version", "--from", "awslabs.ccapi-mcp-server@latest", "awslabs.ccapi-mcp-server", "--readonly"],
      "env": {
        "DEFAULT_TAGS": "enabled",
        "SECURITY_SCANNING": "enabled",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
EOF
    
    log_success "VS Code MCP configuration created at $HOME/.vscode/mcp.json"
    export VSCODE_MCP_CONFIGURED=true
}


verify_vscode_mcp_setup() {
    log_step "Verifying VS Code MCP server setup..."
    
    # Check if uv is available (required for MCP servers)
    if ! command -v uv >/dev/null 2>&1; then
        log_warning "uv not found - MCP servers may not work properly"
        log_info "Install uv manually if needed: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    else
        log_info "uv is available for MCP server execution"
    fi
    
    # Check VS Code MCP configuration
    if [ -f "$HOME/.vscode/mcp.json" ]; then
        log_success "VS Code MCP configuration exists"
    else
        log_warning "VS Code MCP configuration not found"
    fi
    
    # Test Serena MCP server availability (non-blocking)
    local python_version=$(detect_python_version)
    log_info "Testing Serena MCP server availability..."
    if timeout 10 uv tool run --python "$python_version" --from git+https://github.com/oraios/serena serena --help >/dev/null 2>&1; then
        log_success "Serena MCP server is accessible"
    else
        log_warning "Serena MCP server test timed out or failed (may work in actual usage)"
    fi
}

# Run MCP setup if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_step "Starting VS Code MCP server configuration..."
    
    # Check for AWS credentials to determine if AWS MCP server should be included
    if [ -f "$HOME/.aws/credentials" ] || [ -n "$AWS_ACCESS_KEY_ID" ]; then
        log_info "AWS credentials detected - will include AWS MCP server"
        export AWS_MOUNTED=true
    else
        log_info "AWS credentials not available - will skip AWS MCP server"
        export AWS_MOUNTED=false
    fi
    
    # Install VS Code MCP servers
    install_vscode_mcp_servers
    
    # Verify setup
    verify_vscode_mcp_setup
    
    # Summary
    log_success "VS Code MCP server configuration complete"
    log_info "MCP servers configured for VS Code:"
    echo "   - Serena (IDE assistant for code analysis)"
    if [ "$AWS_MOUNTED" = true ]; then
        echo "   - AWS Labs CCAPI (AWS resource management)"
    fi
    log_info "Configuration saved to: $HOME/.vscode/mcp.json"
    
    # Note about Claude integration
    if command -v claude >/dev/null 2>&1; then
        log_info "Claude CLI detected - run claude.sh to configure MCP servers for Claude"
    fi
fi