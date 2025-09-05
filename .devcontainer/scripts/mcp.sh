#!/bin/bash
# MCP (Model Context Protocol) server configuration for VS Code and Claude

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

install_claude_mcp() {
    log_step "Configuring MCP servers for Claude CLI..."
    
    # Detect Python version dynamically
    local python_version=$(detect_python_version)
    log_info "Using Python version: $python_version"
    
    # Check if Claude CLI is available
    if ! command -v claude >/dev/null 2>&1; then
        log_warning "Claude CLI not found - skipping Claude MCP configuration"
        export CLAUDE_MCP_CONFIGURED=false
        return 1
    fi
    
    # Configure Serena MCP server for Claude
    log_info "Adding Serena MCP server to Claude configuration..."
    if claude mcp add serena -- uv tool run --python "$python_version" --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project "$(pwd)" 2>/dev/null; then
        log_success "Serena MCP server added to Claude"
    else
        log_info "Serena MCP server already exists in Claude configuration or failed to add"
    fi
    
    # Configure AWS MCP server if AWS credentials are available
    if [ "$AWS_MOUNTED" = true ]; then
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
    if command -v claude >/dev/null 2>&1; then
        local mcp_count=$(claude mcp list 2>/dev/null | grep -E "serena|awslabs" | wc -l)
        if [ "$mcp_count" -gt 0 ]; then
            log_success "Claude MCP servers configured successfully ($mcp_count servers)"
            export CLAUDE_MCP_CONFIGURED=true
        else
            log_warning "No MCP servers found in Claude configuration"
            export CLAUDE_MCP_CONFIGURED=false
        fi
    else
        export CLAUDE_MCP_CONFIGURED=false
    fi
}

verify_mcp_setup() {
    log_step "Verifying MCP server setup..."
    
    # Check if uv is available (required for MCP servers)
    if ! command -v uv >/dev/null 2>&1; then
        log_warning "uv not found - MCP servers may not work properly"
        log_info "Install uv manually if needed"
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
    log_step "Starting MCP server configuration..."
    
    # Source AWS status if aws.sh has been run
    if [ -n "$AWS_MOUNTED" ]; then
        log_info "Using existing AWS status: $AWS_MOUNTED"
    else
        log_info "AWS status not available - will skip AWS MCP server"
        export AWS_MOUNTED=false
    fi
    
    # Install VS Code MCP servers
    install_vscode_mcp_servers
    
    # Install Claude MCP servers if Claude is available
    install_claude_mcp
    
    # Verify setup
    verify_mcp_setup
    
    # Summary
    log_success "MCP server configuration complete"
    log_info "Available integrations:"
    echo "   - VS Code with standalone MCP servers (Serena for code analysis)"
    if [ "$AWS_MOUNTED" = true ]; then
        echo "   - VS Code with AWS MCP server for AWS resource management"
    fi
    if [ "$CLAUDE_MCP_CONFIGURED" = true ]; then
        echo "   - Claude CLI with the same MCP servers"
        echo "   - Both VS Code and Claude use the same MCP servers independently"
    fi
fi