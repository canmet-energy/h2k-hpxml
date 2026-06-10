#!/bin/bash
set -e

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSLk}"

# Install Claude CLI (Anthropic's command-line interface)
echo "🤖 Installing Claude CLI..."
echo "   Note: This script can be run as a regular user (no sudo required)"

# Install Claude CLI via the official installer script
echo "🔄 Downloading and running the official Claude CLI installer..."
if curl ${CURL_FLAGS} https://claude.ai/install.sh | bash; then
    echo "✅ Claude CLI installed successfully"
else
    echo "❌ Failed to install Claude CLI via installer script"
    echo "   This might be due to:"
    echo "   - Network connectivity issues"
    echo "   - Unable to reach claude.ai"

    # Try to provide more specific error information
    echo "🔍 Testing connectivity to claude.ai..."
    if curl ${CURL_FLAGS} --connect-timeout 10 https://claude.ai/ > /dev/null 2>&1; then
        echo "   ✅ claude.ai is accessible"
        echo "   Issue might be installer-specific or permission-related"
    else
        echo "   ❌ claude.ai is not accessible"
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