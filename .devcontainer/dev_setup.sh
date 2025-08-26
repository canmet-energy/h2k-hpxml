#!/bin/bash
set -e  # Exit on any error

# --- Helper Functions ---
log_info() { echo "ℹ️ $1"; }
log_success() { echo "✅ $1"; }
log_warning() { echo "⚠️ $1"; }
log_step() { echo "🚀 $1"; }

install_certificates() {
    # Check if we're on NRCAN network
    if [ "$(curl -k -o /dev/null -s -w "%{http_code}" "https://intranet.nrcan.gc.ca/")" -ge 200 ] && \
       [ "$(curl -o /dev/null -s -w "%{http_code}" "https://intranet.nrcan.gc.ca/")" -lt 400 ]; then
        log_step "NRCAN network detected - installing certificates..."
        log_step "Cloning NRCAN certificates repository..."
        git clone https://github.com/canmet-energy/linux_nrcan_certs.git
        log_step "Installing NRCAN certificates..."
        cd linux_nrcan_certs
        ./install_nrcan_certs.sh >/dev/null 2>&1
        cd ..
        log_step "Cleaning up..."
        rm -fr linux_nrcan_certs

        log_step "Reloading certificate store..."
        sudo update-ca-certificates >/dev/null 2>&1
        
        log_success "NRCAN certificates installed"
        NRCAN_NETWORK=true
    else
        log_info "Standard network detected - using default certificates"
        NRCAN_NETWORK=false
    fi

    # Set certificate environment variables for immediate use
    if [ -f "/etc/ssl/certs/ca-certificates.crt" ]; then
        log_info "Setting SSL certificate environment variables..."
        export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
        export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    fi
}

install_nodejs() {
    log_step "Installing Node.js and tools..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - >/dev/null 2>&1
    sudo apt-get install -y nodejs python3-pip >/dev/null 2>&1
    log_success "Node.js installed"
}

install_uv() {
    log_step "Installing uv (Python package manager)..."
    
    # Simplified uv installation with fallbacks
    if [[ "$(which python3)" == "/venv/"* ]] || [[ -n "$VIRTUAL_ENV" ]]; then
        sudo -H pip3 install uv >/dev/null 2>&1 || log_warning "uv installation failed, continuing..."
    else
        pip3 install --user uv >/dev/null 2>&1 || \
        pip install --user uv >/dev/null 2>&1 || \
        python3 -m pip install --user uv >/dev/null 2>&1 || \
        python -m pip install --user uv >/dev/null 2>&1 || \
        log_warning "uv installation failed"
    fi
}

setup_python_venv() {
    # Find available Python command
    for cmd in "/venv/bin/python" "python3" "python"; do
        if command -v $cmd >/dev/null 2>&1; then
            PYTHON_CMD=$cmd
            break
        fi
    done
    
    if [ -n "$PYTHON_CMD" ]; then
        log_step "Setting up Python virtual environment using $PYTHON_CMD..."
        $PYTHON_CMD -m venv ./.venv && PYTHON_VENV_CREATED=true
        log_success "Python virtual environment created"
        
        # Install packages from pyproject.toml or requirements.txt
        if [ -f "pyproject.toml" ]; then
            log_info "Installing Python packages from pyproject.toml..."
            
            # Find pip in venv or system
            for pip_cmd in "./.venv/bin/pip" "./.venv/bin/pip3" "pip3" "pip"; do
                if [ -f "$pip_cmd" ] || command -v $pip_cmd >/dev/null 2>&1; then
                    PIP_CMD=$pip_cmd
                    break
                fi
            done
            
            if [ -z "$PIP_CMD" ]; then
                PIP_CMD="$PYTHON_CMD -m pip"
            fi
            
            log_info "Using pip command: $PIP_CMD"
            
            # Install the project in editable mode with all dependencies
            $PIP_CMD install --upgrade pip setuptools wheel
            $PIP_CMD install -e . 
            
            # Install optional dependencies if they exist
            if grep -q "project.optional-dependencies" pyproject.toml; then
                log_info "Installing optional dependencies..."
                # Try to install common optional dependency groups that exist in the file
                for group in "dev" "test" "gui" "all"; do
                    if grep -A 20 "project.optional-dependencies" pyproject.toml | grep -q "^$group = "; then
                        log_info "Installing [$group] dependencies..."
                        $PIP_CMD install -e ".[$group]" || log_warning "Failed to install [$group] dependencies"
                    fi
                done
            fi
            
            log_success "Python packages installed from pyproject.toml"
            
        elif [ -f "requirements.txt" ]; then
            log_info "Installing Python packages from requirements.txt..."
            
            # Find pip in venv or system
            for pip_cmd in "./.venv/bin/pip" "./.venv/bin/pip3" "pip3" "pip"; do
                if [ -f "$pip_cmd" ] || command -v $pip_cmd >/dev/null 2>&1; then
                    PIP_CMD=$pip_cmd
                    break
                fi
            done
            
            if [ -z "$PIP_CMD" ]; then
                PIP_CMD="$PYTHON_CMD -m pip"
            fi
            
            log_info "Using pip command: $PIP_CMD"
            $PIP_CMD install --upgrade pip setuptools wheel
            $PIP_CMD install -r requirements.txt
            log_success "Python packages installed from requirements.txt"
            
        else
            log_info "No pyproject.toml or requirements.txt found, skipping Python package installation"
        fi
    else
        log_warning "No Python installation found, skipping virtual environment setup"
    fi
}

install_vscode_mcp_servers() {
    log_step "Setting up standalone MCP servers..."
    
    # Create .vscode directory and basic MCP configuration
    mkdir -p $HOME/.vscode
    # Update VS Code MCP config with AWS server
    cat > $HOME/.vscode/mcp.json << 'EOF'
{
  "servers": {
    "serena": {
      "type": "stdio",
      "command": "uv",
      "args": ["tool", "run", "--python", "3.12", "--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server", "--context", "ide-assistant", "--project", "."]
    },
    "awslabs-ccapi-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": ["tool", "run", "--python", "3.12", "--from", "awslabs.ccapi-mcp-server@latest", "awslabs.ccapi-mcp-server", "--readonly"],
      "env": {
        "DEFAULT_TAGS": "enabled",
        "SECURITY_SCANNING": "enabled",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
EOF


}

install_claude() {
    log_step "Installing Claude..."
    
    # Ensure certificate environment variables are set for npm
    export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
    export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
    export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    
    log_info "Installing Claude CLI with certificate support..."
    
    # Try installation with certificates
    if ! sudo -E NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt npm install -g @anthropic-ai/claude-code; then
        log_warning "Claude installation failed with certificates. Trying with --unsafe-perm..."
        
        # Try with --unsafe-perm
        if ! sudo -E NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt npm install -g @anthropic-ai/claude-code --unsafe-perm; then
            log_warning "Installation with --unsafe-perm failed. Trying with strict-ssl disabled..."
            
            # Try with strict-ssl disabled as last resort
            if ! sudo -E NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt npm install -g @anthropic-ai/claude-code --unsafe-perm --strict-ssl=false; then
                log_warning "Claude installation failed with all methods. Please check certificate configuration."
                return 1
            else
                log_success "Claude installed with strict-ssl disabled"
            fi
        else
            log_success "Claude installed with --unsafe-perm"
        fi
    else
        log_success "Claude installed successfully with certificates"
    fi
    
    # Verify installation
    if ! command -v claude >/dev/null 2>&1; then
        log_warning "Claude command not found after installation. Check npm configuration."
        return 1
    else
        CLAUDE_VERSION=$(claude --version 2>/dev/null || echo 'version unknown')
        log_success "Claude installed successfully ($CLAUDE_VERSION)"
    fi
    
    # Set certificate environment variables in .bashrc for persistence
    log_info "Adding certificate environment variables to .bashrc..."
    echo 'export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt' >> /home/vscode/.bashrc
    echo 'export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt' >> /home/vscode/.bashrc
    echo 'export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt' >> /home/vscode/.bashrc
    echo 'export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt' >> /home/vscode/.bashrc
    rm -rf $HOME/.config/claude-code/auth.json
    log_success "Claude installed"
}

install_claude_mcp() {
    if [ "$AWS_MOUNTED" != "true" ]; then
        return
    fi
    
    log_step "Setting up AWS MCP server..."
    

    log_success "AWS MCP server added to VS Code configuration"
    
    # Add AWS server to Claude if installed
    if [ "$INSTALL_CLAUDE" = true ]; then
        log_info "Adding AWS MCP server to Claude configuration..."
        claude mcp add awslabs-ccapi-mcp-server \
          -e DEFAULT_TAGS=enabled \
          -e SECURITY_SCANNING=enabled \
          -e FASTMCP_LOG_LEVEL=ERROR \
          -- uv tool run --python 3.12 --from awslabs.ccapi-mcp-server@latest awslabs.ccapi-mcp-server --readonly 2>/dev/null || \
        echo "AWS MCP server already exists in Claude configuration"
            log_info "Configuring Claude to use standalone MCP servers..."
        # Ensure certificates are available for MCP configuration
        if claude mcp add serena -- uv tool run --python 3.12 --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project "$(pwd)" 2>/dev/null; then
            log_success "Serena MCP server added to Claude"
        else
            log_info "Serena MCP server already exists in Claude configuration"
        fi
    fi
}

verify_aws_credentials() {
    log_step "Setting up AWS credentials..."
    
    # Check if credentials are mounted and working
    if [ -d "$HOME/.aws" ] && [ "$(ls -A $HOME/.aws 2>/dev/null)" ]; then
        log_info "AWS credentials found"
        # Test if credentials work
        if aws sts get-caller-identity >/dev/null 2>&1; then
            AWS_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null)
            AWS_USER=$(aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null | rev | cut -d'/' -f1 | rev)
            AWS_REGION=$(aws configure get region 2>/dev/null || echo "not-set")
            
            log_success "AWS credentials are valid"
            log_info "Connected to AWS Account: $AWS_ACCOUNT"
            log_info "User: $AWS_USER"
            log_info "Region: $AWS_REGION"
            
            AWS_MOUNTED=true
        else
            log_warning "AWS credentials found but not working - check your configuration"
            AWS_MOUNTED=false
        fi
    else
        log_info "No AWS credentials found in $HOME/.aws If you're not using AWS, ignore this message."
        AWS_MOUNTED=false
    fi
}

# --- Main Script ---
# Parse command line arguments
INSTALL_CLAUDE=false

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --claude    Install Claude with MCP support"
    echo "  -h, --help  Show this help message"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --claude)
            INSTALL_CLAUDE=true
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

log_step "Starting devcontainer setup..."
if [ "$INSTALL_CLAUDE" = true ]; then
    log_info "Claude MCP support will be installed"
else
    log_info "Skipping Claude MCP installation (use --claude to enable)"
fi

# Initialize variables
PYTHON_VENV_CREATED=false
RUBY_BUNDLE_INSTALLED=false
AWS_MOUNTED=false

# Setup stages
install_certificates
verify_aws_credentials
install_vscode_mcp_servers

# Install Claude and tools if requested
if [ "$INSTALL_CLAUDE" = true ]; then
    install_nodejs
    install_uv
    install_claude
    install_claude_mcp
fi

# setup_aws_mcp
setup_python_venv

# Summary
log_step "Devcontainer setup complete!"

log_info "You can now use:"
echo "   - VS Code with standalone MCP servers (Serena for code analysis)"
if [ "$AWS_MOUNTED" = true ]; then
    echo "   - VS Code with AWS MCP server for AWS resource management"
fi
echo "   - GitHub Copilot for code completion"
if [ "$PYTHON_VENV_CREATED" = true ]; then
    echo "   - Python virtual environment at ./.venv"
fi
if [ "$RUBY_BUNDLE_INSTALLED" = true ]; then
    echo "   - Ruby gems in ./vendor/bundle"
fi

log_info "MCP Configuration:"
echo "   - VS Code MCP config: .vscode/mcp.json"
if [ "$INSTALL_CLAUDE" = true ]; then
    echo "   - Claude Desktop/Code with the same MCP servers"
    echo "   - Both VS Code and Claude use the same MCP servers independently"
fi