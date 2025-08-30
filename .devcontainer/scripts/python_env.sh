#!/bin/bash
# Python virtual environment setup and package installation

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

configure_pip() {
    log_step "Configuring pip for corporate environment..."
    
    # Create pip config directory if it doesn't exist
    mkdir -p ~/.config/pip
    
    # Configure pip for corporate network
    if [[ "${DOCKER_BUILD_CONTEXT:-}" == "true" ]]; then
        # During Docker build, use more aggressive SSL workarounds
        cat > ~/.config/pip/pip.conf << 'EOF'
[global]
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
cert = /etc/ssl/certs/ca-certificates.crt
EOF
        log_success "Docker build pip configuration applied"
    else
        # Runtime configuration - check for NRCan network
        if curl -k -s --connect-timeout 5 https://intranet.nrcan.gc.ca/ > /dev/null 2>&1; then
            cat > ~/.config/pip/pip.conf << 'EOF'
[global]
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
cert = /etc/ssl/certs/ca-certificates.crt
EOF
            log_success "NRCan network pip configuration applied"
        else
            cat > ~/.config/pip/pip.conf << 'EOF'
[global]
cert = /etc/ssl/certs/ca-certificates.crt
EOF
            log_success "Standard pip configuration applied"
        fi
    fi
}

setup_python_venv() {
    log_step "Setting up Python virtual environment..."
    
    # Find available Python command (prefer Python from Docker image first)
    local PYTHON_CMD=""
    for cmd in "/venv/bin/python" "python3" "python"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            PYTHON_CMD="$cmd"
            log_info "Using Python: $PYTHON_CMD"
            break
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        log_error "No Python installation found"
        return 1
    fi
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        log_info "Creating Python virtual environment..."
        "$PYTHON_CMD" -m venv ./.venv
        log_success "Python virtual environment created at ./.venv"
        export PYTHON_VENV_CREATED=true
    else
        log_info "Python virtual environment already exists"
        export PYTHON_VENV_CREATED=false
    fi
    
    # Find pip command in the virtual environment
    local PIP_CMD=""
    for pip_cmd in "./.venv/bin/pip" "./.venv/bin/pip3"; do
        if [ -f "$pip_cmd" ]; then
            PIP_CMD="$pip_cmd"
            break
        fi
    done
    
    if [ -z "$PIP_CMD" ]; then
        PIP_CMD="$PYTHON_CMD -m pip"
        log_info "Using fallback pip: $PIP_CMD"
    else
        log_info "Using pip: $PIP_CMD"
    fi
    
    # Install packages based on available configuration files
    install_python_packages "$PIP_CMD"
}

install_python_packages() {
    local PIP_CMD="$1"
    
    # Upgrade pip first
    log_info "Upgrading pip and build tools..."
    "$PIP_CMD" install --upgrade pip setuptools wheel >/dev/null 2>&1 || log_warning "Failed to upgrade pip"
    
    if [ -f "pyproject.toml" ]; then
        log_step "Installing Python packages from pyproject.toml..."
        
        # Install the project in editable mode
        log_info "Installing project in development mode..."
        "$PIP_CMD" install -e . || {
            log_warning "Failed to install project in editable mode"
            return 1
        }
        
        # Install optional dependencies if they exist
        if grep -q "project.optional-dependencies" pyproject.toml 2>/dev/null; then
            log_info "Checking for optional dependencies..."
            
            for group in "dev" "test" "gui" "all"; do
                if grep -A 20 "project.optional-dependencies" pyproject.toml | grep -q "^$group = "; then
                    log_info "Installing [$group] dependencies..."
                    "$PIP_CMD" install -e ".[$group]" 2>/dev/null || log_warning "Failed to install [$group] dependencies"
                fi
            done
        fi
        
        log_success "Python packages installed from pyproject.toml"
        
    elif [ -f "requirements.txt" ]; then
        log_step "Installing Python packages from requirements.txt..."
        "$PIP_CMD" install -r requirements.txt || {
            log_warning "Failed to install from requirements.txt"
            return 1
        }
        log_success "Python packages installed from requirements.txt"
        
    else
        log_info "No pyproject.toml or requirements.txt found - skipping package installation"
    fi
    
    # Verify installation
    if [ -f "pyproject.toml" ]; then
        local project_name=$(grep -E '^name = ' pyproject.toml | sed 's/name = "\(.*\)"/\1/' 2>/dev/null)
        if [ -n "$project_name" ]; then
            if ./.venv/bin/python -c "import ${project_name//-/_}" 2>/dev/null; then
                log_success "Project package '$project_name' is importable"
            else
                log_warning "Project package '$project_name' may not be properly installed"
            fi
        fi
    fi
}

install_uv() {
    if command -v uv &> /dev/null; then
        echo "✅ uv already installed"
        return 0
    fi
    
    echo "📦 Installing uv package manager..."
    
    # Handle NRCan network SSL issues during Docker build
    if [[ "${DOCKER_BUILD_CONTEXT:-}" == "true" ]]; then
        echo "🔧 Docker build context detected - using pip with SSL workarounds for corporate network"
        pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --user uv
        export PATH="$HOME/.local/bin:$PATH"
        # Verify installation
        if command -v uv &> /dev/null; then
            echo "✅ uv installed successfully via pip"
            return 0
        else
            echo "❌ uv installation failed via pip"
            return 1
        fi
    else
        # Runtime installation (postCreateCommand) - use official installer
        if curl -k -s --connect-timeout 5 https://intranet.nrcan.gc.ca/ > /dev/null 2>&1; then
            echo "🔧 NRCan network detected - using curl with SSL workarounds"
            curl -k -LsSf https://astral.sh/uv/install.sh | sh
        else
            echo "🌐 External network - using standard installation"
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
        
        # Source the shell profile to get uv in PATH
        if [ -f "$HOME/.profile" ]; then
            source "$HOME/.profile"
        fi
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Final verification
    if command -v uv &> /dev/null; then
        echo "✅ uv installed successfully"
        uv --version
        return 0
    else
        echo "❌ uv installation failed"
        return 1
    fi
}

# Run Python environment setup if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_step "Starting Python environment setup..."
    
    # Configure pip for corporate network before installing uv
    configure_pip
    
    # Install uv first for faster package management
    install_uv
    
    # Setup virtual environment and install packages
    setup_python_venv
    
    if [ "$PYTHON_VENV_CREATED" = true ]; then
        log_success "Python environment setup complete - new virtual environment created"
    else
        log_success "Python environment setup complete - existing virtual environment used"
    fi
    
    log_info "To activate the environment: source ./.venv/bin/activate"
fi