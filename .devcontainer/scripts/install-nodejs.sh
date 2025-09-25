#!/bin/bash
set -e

# Install Node.js for development tooling
echo "🟢 Installing Node.js..."

CURL_FLAGS=${CURL_FLAGS:-"-fsSL"}
NODE_VERSION="18.20.4"

# Download and install Node.js
curl $CURL_FLAGS --connect-timeout 30 https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz -o /tmp/node.tar.xz

cd /tmp
tar -xJf node.tar.xz
cp -r node-v${NODE_VERSION}-linux-x64/* /usr/local/
rm -rf /tmp/node*

# Create symlinks
ln -sf /usr/local/bin/node /usr/bin/node
ln -sf /usr/local/bin/npm /usr/bin/npm
ln -sf /usr/local/bin/npx /usr/bin/npx

# Configure npm for potentially insecure environments
npm config set ca ""
npm config set strict-ssl false
npm config set registry https://registry.npmjs.org/

echo "✅ Node.js installed successfully"
node --version
npm --version