#!/bin/bash
set -e

# Install Node.js for development tooling
echo "🟢 Installing Node.js..."

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

NODE_VERSION="18.20.4"

# Download and install Node.js
DOWNLOAD_URL="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz"
echo "curl ${CURL_FLAGS} --connect-timeout 30 $DOWNLOAD_URL -o /tmp/node.tar.xz"
if ! curl ${CURL_FLAGS} --connect-timeout 30 "$DOWNLOAD_URL" -o /tmp/node.tar.xz; then
    echo "❌ Node.js download failed. Investigate certificate trust or run: certctl probe" >&2
    exit 1
fi
echo "Extracting Node.js..."

cd /tmp
tar -xJf node.tar.xz
cp -r node-v${NODE_VERSION}-linux-x64/* /usr/local/
rm -rf /tmp/node*

# Create symlinks
ln -sf /usr/local/bin/node /usr/bin/node
ln -sf /usr/local/bin/npm /usr/bin/npm
ln -sf /usr/local/bin/npx /usr/bin/npx

# Configure npm: only relax settings if we are explicitly insecure
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

echo "✅ Node.js installed successfully"
node --version
npm --version