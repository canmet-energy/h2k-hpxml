#!/bin/bash
set -e

# Install Python UV Manager
echo "🐍 Installing UV Python package manager..."

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

UV_VERSION="0.8.15"
echo "curl ${CURL_FLAGS} --connect-timeout 30 -o /tmp/uv.tar.gz https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz"
curl ${CURL_FLAGS} --connect-timeout 30 -o /tmp/uv.tar.gz \
    "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz"

cd /tmp
tar -xzf uv.tar.gz
mv uv-x86_64-unknown-linux-gnu/uv /usr/local/bin/
chmod +x /usr/local/bin/uv
rm -rf /tmp/uv*

echo "✅ UV installed successfully"
uv --version

# Note: UV environment variables are now managed dynamically by certctl
# at runtime, so no static configuration in /etc/environment is needed.
echo "🔧 UV environment will be configured at runtime by certctl"

echo "🎉 UV installation complete!"