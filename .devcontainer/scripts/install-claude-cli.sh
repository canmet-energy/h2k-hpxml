#!/bin/bash
set -e

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Install Claude CLI (Anthropic's command-line interface)
echo "🤖 Installing Claude CLI..."
CLAUDE_VERSION="latest"

# Check if Node.js is available (Claude CLI requires Node.js)
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "📋 Node.js and/or npm not found - installing automatically..."
    
    # Find the install-nodejs.sh script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    NODEJS_SCRIPT="$SCRIPT_DIR/install-nodejs.sh"
    
    if [ -f "$NODEJS_SCRIPT" ]; then
        echo "🔄 Running install-nodejs.sh..."
        if "$NODEJS_SCRIPT"; then
            echo "✅ Node.js installation completed"
        else
            echo "❌ Error: Failed to install Node.js"
            exit 1
        fi
    else
        echo "❌ Error: install-nodejs.sh script not found at $NODEJS_SCRIPT"
        echo "   Please ensure install-nodejs.sh is in the same directory"
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

# Install Claude CLI globally via npm
echo "🔄 Installing @anthropic-ai/claude-code package..."
if npm install -g  @anthropic-ai/claude-code; then
    echo "✅ Claude CLI installed successfully"
else
    echo "❌ Failed to install Claude CLI via npm"
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

# Verify installation
if command -v claude >/dev/null 2>&1; then
    CLAUDE_VERSION_INSTALLED=$(claude --version 2>/dev/null || echo "version check failed")
    echo "✅ Claude CLI verification successful"
    echo "   Version: $CLAUDE_VERSION_INSTALLED"
    echo "   Location: $(which claude)"
else
    echo "❌ Claude CLI installation verification failed"
    echo "   Command 'claude' not found in PATH"
    exit 1
fi

# Provide usage information
echo ""
echo "🎉 Claude CLI installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Authenticate with Claude: claude auth"
echo "   2. Start a conversation: claude chat"
echo "   3. Get help: claude --help"
echo ""
echo "🔗 For more information:"
echo "   - Documentation: https://docs.anthropic.com/claude/reference/cli"
echo "   - GitHub: https://github.com/anthropics/claude-cli"