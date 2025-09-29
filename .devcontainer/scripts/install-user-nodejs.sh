#!/bin/bash
set -e

# Install Node.js for user (no sudo required)
echo "🟢 Installing Node.js for user $(whoami)..."

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

NODE_VERSION="22.11.0"

# Set up installation directory in user's home
INSTALL_DIR="$HOME/.local"
mkdir -p "$INSTALL_DIR"

# Download and install Node.js
DOWNLOAD_URL="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz"
echo "📥 Downloading Node.js v${NODE_VERSION}..."
if ! curl ${CURL_FLAGS} --connect-timeout 30 "$DOWNLOAD_URL" -o /tmp/node.tar.xz; then
    echo "❌ Node.js download failed. Check network connectivity" >&2
    exit 1
fi

echo "📦 Extracting Node.js..."
cd /tmp
tar -xJf node.tar.xz

# Install to user's .local directory
echo "📂 Installing to $INSTALL_DIR..."
cp -r node-v${NODE_VERSION}-linux-x64/* "$INSTALL_DIR/"
rm -rf /tmp/node*

# Update PATH in user's shell configuration
echo "🔧 Configuring PATH..."
if ! grep -q "$INSTALL_DIR/bin" ~/.bashrc 2>/dev/null; then
    echo "export PATH=\"$INSTALL_DIR/bin:\$PATH\"" >> ~/.bashrc
fi

if ! grep -q "$INSTALL_DIR/bin" ~/.profile 2>/dev/null; then
    echo "export PATH=\"$INSTALL_DIR/bin:\$PATH\"" >> ~/.profile
fi

# Export for current session
export PATH="$INSTALL_DIR/bin:$PATH"

# Configure npm for certificate handling if needed
if [ "${CERT_INSECURE:-}" = "1" ]; then
    echo "⚠️  Insecure certificate mode detected - relaxing npm SSL settings"
    npm config set ca ""
    npm config set strict-ssl false
else
    # Ensure strict mode
    npm config delete ca >/dev/null 2>&1 || true
    npm config set strict-ssl true
fi
npm config set registry https://registry.npmjs.org/

echo "✅ Node.js installed successfully for user $(whoami)"
echo "   Node.js: $(node --version)"
echo "   npm: $(npm --version)"
echo "   Installation directory: $INSTALL_DIR"
echo ""
echo "💡 npm global packages will be installed to: $(npm config get prefix)"
echo "   No sudo required for: npm install -g <package>"