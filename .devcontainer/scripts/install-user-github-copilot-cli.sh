#!/bin/bash
set -e

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Install GitHub Copilot CLI
echo "🤖 Installing GitHub Copilot CLI..."
echo "   Note: This script can be run as a regular user (no sudo required)"

# Check if Node.js is available (GitHub Copilot CLI requires Node.js)
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "📋 Node.js and/or npm not found - installing automatically..."

    # Find the install-user-nodejs.sh script (or fallback to install-system-nodejs.sh if it exists)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    NODEJS_USER_SCRIPT="$SCRIPT_DIR/install-user-nodejs.sh"
    NODEJS_SYSTEM_SCRIPT="$SCRIPT_DIR/install-system-nodejs.sh"

    # Try user installation first (no sudo required)
    if [ -f "$NODEJS_USER_SCRIPT" ]; then
        echo "🔄 Running install-user-nodejs.sh (user installation, no sudo required)..."
        if "$NODEJS_USER_SCRIPT"; then
            echo "✅ Node.js installation completed"
            # Source bashrc to get the new PATH
            source ~/.bashrc
        else
            echo "❌ Error: Failed to install Node.js"
            exit 1
        fi
    elif [ -f "$NODEJS_SYSTEM_SCRIPT" ]; then
        echo "🔄 Running install-system-nodejs.sh (system installation, requires sudo)..."
        if sudo "$NODEJS_SYSTEM_SCRIPT"; then
            echo "✅ Node.js installation completed"
        else
            echo "❌ Error: Failed to install Node.js"
            exit 1
        fi
    else
        echo "❌ Error: No Node.js installation script found"
        echo "   Expected $NODEJS_USER_SCRIPT or $NODEJS_SYSTEM_SCRIPT"
        exit 1
    fi

    # Verify Node.js is now available
    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
        echo "❌ Error: Node.js/npm still not available after installation"
        exit 1
    fi
fi

# Display Node.js version for context
NODE_VERSION=$(node --version 2>/dev/null)
NPM_VERSION=$(npm --version 2>/dev/null)
echo "📦 Using Node.js ${NODE_VERSION} with npm ${NPM_VERSION}"

# Install GitHub Copilot CLI globally via npm
echo "🔄 Installing @github/copilot package..."
if npm install -g @github/copilot; then
    echo "✅ GitHub Copilot CLI installed successfully"
else
    echo "❌ Failed to install GitHub Copilot CLI via npm"
    echo "   This might be due to:"
    echo "   - Network connectivity issues"
    echo "   - npm registry access problems"
    echo "   - Permission issues"

    # Try to provide more specific error information
    echo "🔍 Testing npm registry connectivity..."
    if curl ${CURL_FLAGS} --connect-timeout 10 https://registry.npmjs.org/ > /dev/null 2>&1; then
        echo "   ✅ npm registry is accessible"
        echo "   Issue might be package-specific or permission-related"
    else
        echo "   ❌ npm registry is not accessible"
        echo "   Check network connectivity and certificate configuration"
    fi

    exit 1
fi

# Verify installation (ensure PATH includes npm global bin)
export PATH="$HOME/.npm-global/bin:$PATH"

if command -v copilot >/dev/null 2>&1; then
    COPILOT_VERSION=$(copilot --version 2>/dev/null || echo "version check failed")
    echo "✅ GitHub Copilot CLI verification successful"
    echo "   Version: $COPILOT_VERSION"
    echo "   Location: $(which copilot)"
else
    echo "❌ GitHub Copilot CLI installation verification failed"
    echo "   Command 'copilot' not found in PATH"
    echo "   Expected location: $HOME/.npm-global/bin/copilot"
    exit 1
fi

# Provide usage information
echo ""
echo "🎉 GitHub Copilot CLI installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Authenticate with GitHub: copilot auth login"
echo "   2. Get suggestions: copilot suggest 'your command description'"
echo "   3. Explain commands: copilot explain 'complex command'"
echo "   4. Get help: copilot --help"
echo ""
echo "💡 Usage examples:"
echo "   copilot suggest 'install docker on ubuntu'"
echo "   copilot explain 'tar -xzf file.tar.gz'"
echo "   copilot suggest 'find all python files modified today'"
echo ""
echo "🔗 For more information:"
echo "   - Documentation: https://docs.github.com/en/copilot/github-copilot-in-the-cli"
echo "   - GitHub: https://github.com/github/gh-copilot"