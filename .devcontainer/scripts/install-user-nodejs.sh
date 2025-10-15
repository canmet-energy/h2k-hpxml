#!/bin/bash
set -e

# Install Python UV Manager for user (no sudo required)
echo "🐍 Installing UV Python package manager for user $(whoami)..."

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Allow caller to specify UV version via DEVCONTAINER_UV_VERSION (preferred) or UV_VERSION.
# Fallback default remains 0.8.15 if neither provided.
UV_VERSION_INPUT="${DEVCONTAINER_UV_VERSION:-${UV_VERSION:-0.8.15}}"

# Basic semantic version validation (major.minor.patch) – tolerate a leading 'v'. Some uv releases are simple semver.
if [[ "$UV_VERSION_INPUT" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    UV_VERSION="${UV_VERSION_INPUT#v}" # strip leading v if present
else
    echo "❌ Invalid UV version format: '$UV_VERSION_INPUT' (expected MAJOR.MINOR.PATCH)" >&2
    exit 2
fi

if [ -n "${DEVCONTAINER_UV_VERSION:-}" ]; then
    _uv_version_source="DEVCONTAINER_UV_VERSION"
elif [ -n "${UV_VERSION:-}" ]; then
    _uv_version_source="UV_VERSION (env override)"
else
    _uv_version_source="default (0.8.15)"
fi
echo "ℹ️ Using UV version ${UV_VERSION} (source: ${_uv_version_source})"

# Set up installation directory in user's home
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

echo "📥 Downloading UV v${UV_VERSION}..."
curl ${CURL_FLAGS} --connect-timeout 30 -o /tmp/uv.tar.gz \
    "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz"

cd /tmp
tar -xzf uv.tar.gz
mv uv-x86_64-unknown-linux-gnu/uv "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/uv"
rm -rf /tmp/uv*

# Update PATH in user's shell configuration
echo "🔧 Configuring PATH..."
if ! grep -q "$INSTALL_DIR" ~/.bashrc 2>/dev/null; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.bashrc
fi

if ! grep -q "$INSTALL_DIR" ~/.profile 2>/dev/null; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.profile
fi

# Export for current session
export PATH="$INSTALL_DIR:$PATH"

echo "✅ UV installed successfully for user $(whoami)"
uv --version
echo "   Installation directory: $INSTALL_DIR"
echo ""
echo "💡 UV is now available for Python package management"
echo "   No sudo required for any UV operations"

echo "🎉 UV installation complete!"