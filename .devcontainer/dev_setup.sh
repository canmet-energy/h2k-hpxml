#!/bin/bash
# Modular devcontainer setup orchestrator
# This script coordinates the execution of individual setup modules

# Exit on any error
set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"

# Source common utilities
source "$SCRIPTS_DIR/common.sh"

# Parse command line arguments
INSTALL_CLAUDE=false
INSTALL_NODEJS=false
INSTALL_AWS=false
INSTALL_VSCODE_MCP=false
INSTALL_ALL=false
SKIP_PYTHON=false

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Modular devcontainer setup script"
    echo ""
    echo "Options:"
    echo "  --all           Install everything (equivalent to --claude --nodejs --aws --vscode-mcp)"
    echo "  --claude        Install Claude CLI with MCP support"
    echo "  --nodejs        Install Node.js (required for Claude)"
    echo "  --aws           Verify and configure AWS credentials"
    echo "  --vscode-mcp    Configure MCP servers for VS Code"
    echo "  --skip-python   Skip Python environment setup"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Default behavior (no flags):"
    echo "  - Install certificates (always)"
    echo "  - Setup Python environment (unless --skip-python)"
    echo "  - Configure VS Code MCP servers"
    echo ""
    echo "Examples:"
    echo "  $0                    # Basic setup (certificates + Python + VS Code MCP)"
    echo "  $0 --claude           # Full Claude development setup"
    echo "  $0 --all              # Install everything"
    echo "  $0 --nodejs --vscode-mcp # Just Node.js and VS Code MCP servers"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            INSTALL_ALL=true
            INSTALL_CLAUDE=true
            INSTALL_NODEJS=true
            INSTALL_AWS=true
            INSTALL_VSCODE_MCP=true
            shift
            ;;
        --claude)
            INSTALL_CLAUDE=true
            INSTALL_NODEJS=true  # Claude requires Node.js
            INSTALL_VSCODE_MCP=true # Claude benefits from VS Code MCP
            shift
            ;;
        --nodejs)
            INSTALL_NODEJS=true
            shift
            ;;
        --aws)
            INSTALL_AWS=true
            shift
            ;;
        --vscode-mcp)
            INSTALL_VSCODE_MCP=true
            shift
            ;;
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# If no specific options were given, enable default behavior
if [ "$INSTALL_CLAUDE" = false ] && [ "$INSTALL_NODEJS" = false ] && [ "$INSTALL_AWS" = false ]; then
    INSTALL_VSCODE_MCP=true  # Default: install VS Code MCP servers
fi

# Initialize status variables
export CERTIFICATES_INSTALLED=false
export AWS_MOUNTED=false
export PYTHON_VENV_CREATED=false
export NODEJS_INSTALLED=false
export CLAUDE_INSTALLED=false
export VSCODE_MCP_CONFIGURED=false
export CLAUDE_MCP_CONFIGURED=false

# Main setup flow
main() {
    log_step "Starting modular devcontainer setup..."
    
    # Display configuration
    if [ "$INSTALL_ALL" = true ]; then
        log_info "Full installation requested (all components)"
    else
        log_info "Selected components:"
        [ "$SKIP_PYTHON" = false ] && echo "   - Python environment"
        [ "$INSTALL_NODEJS" = true ] && echo "   - Node.js"
        [ "$INSTALL_CLAUDE" = true ] && echo "   - Claude CLI"
        [ "$INSTALL_AWS" = true ] && echo "   - AWS credentials"
        [ "$INSTALL_VSCODE_MCP" = true ] && echo "   - VS Code MCP servers"
        if [ "$DOCKER_BUILD_CONTEXT" = true ]; then
            echo "   - Certificates (deferred to runtime)"
        else
            echo "   - Certificates (always)"
        fi
    fi
    
    # 1. Certificate setup (skip during Docker build, install at runtime)
    if [ "$DOCKER_BUILD_CONTEXT" = true ]; then
        log_step "Step 1: Certificate setup - SKIPPED (Docker build context)"
        log_info "Certificates will be installed during postCreateCommand"
        export NRCAN_NETWORK=false
    else
        log_step "Step 1: Certificate setup"
        source "$SCRIPTS_DIR/certificates.sh"
        install_certificates
    fi
    
    # 2. Verify AWS credentials if requested
    if [ "$INSTALL_AWS" = true ]; then
        log_step "Step 2: AWS credentials verification"
        source "$SCRIPTS_DIR/aws.sh"
        verify_aws_credentials
    fi
    
    # 3. Setup Python environment (unless skipped)
    if [ "$SKIP_PYTHON" = false ]; then
        log_step "Step 3: Python environment setup"
        log_info "Python environment should be setup via devcontainer postCreateCommand"
        # Check if uv is available
        if command -v uv >/dev/null 2>&1; then
            log_success "uv is available"
            export PATH="$HOME/.local/bin:$PATH"
        else
            log_warning "uv not found - Python packages may not be properly installed"
        fi
    else
        log_info "Step 3: Skipping Python environment setup"
    fi
    
    # 4. Install Node.js if requested (skip if already installed via Dockerfile)
    if [ "$INSTALL_NODEJS" = true ]; then
        if command -v node >/dev/null 2>&1; then
            local node_version=$(node --version 2>/dev/null)
            log_info "Node.js already installed: $node_version"
            log_success "Node.js installation verified"
            export NODEJS_INSTALLED=true
        else
            log_step "Step 4: Node.js installation"
            source "$SCRIPTS_DIR/nodejs.sh"
            install_nodejs
        fi
    fi
    
    # 5. Install Claude CLI if requested
    if [ "$INSTALL_CLAUDE" = true ]; then
        if [ "$NODEJS_INSTALLED" != true ] && [ "$INSTALL_NODEJS" != true ]; then
            log_error "Claude requires Node.js, but Node.js installation was not requested"
            log_info "Please run with --nodejs or --claude flags"
            return 1
        fi
        
        log_step "Step 5: Claude CLI installation"
        source "$SCRIPTS_DIR/claude.sh"
        install_claude
        setup_claude_environment
        setup_claude_mcp_servers
    fi
    
    # 6. Setup VS Code MCP servers if requested
    if [ "$INSTALL_VSCODE_MCP" = true ]; then
        log_step "Step 6: VS Code MCP server configuration"
        source "$SCRIPTS_DIR/vscode_mcp.sh"
        install_vscode_mcp_servers
        verify_vscode_mcp_setup
    fi
    
    # Summary
    display_summary
}

display_summary() {
    log_step "Setup Summary"
    log_success "Devcontainer setup complete!"
    
    echo ""
    log_info "Installed components:"
    echo "   ✅ SSL certificates configured"
    
    [ "$AWS_MOUNTED" = true ] && echo "   ✅ AWS credentials verified" || echo "   ⏭️  AWS credentials not configured"
    [ "$PYTHON_VENV_CREATED" = true ] && echo "   ✅ Python virtual environment created (./.venv)" || echo "   ⏭️  Python environment skipped or already existed"
    [ "$NODEJS_INSTALLED" = true ] && echo "   ✅ Node.js and npm installed" || echo "   ⏭️  Node.js not installed"
    [ "$CLAUDE_INSTALLED" = true ] && echo "   ✅ Claude CLI installed" || echo "   ⏭️  Claude CLI not installed"
    [ "$VSCODE_MCP_CONFIGURED" = true ] && echo "   ✅ VS Code MCP servers configured" || echo "   ⏭️  VS Code MCP not configured"
    [ "$CLAUDE_MCP_CONFIGURED" = true ] && echo "   ✅ Claude MCP servers configured" || echo "   ⏭️  Claude MCP not configured"
    
    echo ""
    log_info "Available tools:"
    echo "   - VS Code with MCP servers (code analysis, AWS resources)"
    echo "   - GitHub Copilot for code completion"
    [ "$PYTHON_VENV_CREATED" = true ] && echo "   - Python virtual environment: source ./.venv/bin/activate"
    [ "$CLAUDE_INSTALLED" = true ] && echo "   - Claude CLI: claude auth (to authenticate)"
    
    echo ""
    log_info "Individual components can be run separately:"
    echo "   - $SCRIPTS_DIR/certificates.sh    # Certificate management"
    echo "   - $SCRIPTS_DIR/aws.sh             # AWS credentials"
    echo "   - $SCRIPTS_DIR/nodejs.sh          # Node.js installation"
    echo "   - $SCRIPTS_DIR/claude.sh          # Claude CLI"
    echo "   - $SCRIPTS_DIR/vscode_mcp.sh      # VS Code MCP server configuration"
}

# Run main function
main "$@"