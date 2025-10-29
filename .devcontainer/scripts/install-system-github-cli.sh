#!/bin/bash
set -e

# Install GitHub CLI
echo "🐙 Installing GitHub CLI..."

# Check for root/sudo privileges
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script requires root privileges"
    echo "   Please run with sudo: sudo $0 $@"
    exit 1
fi

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Add GitHub CLI repository key and source
curl ${CURL_FLAGS} https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null

# Update package list and install
apt-get update
apt-get install -y gh

echo "✅ GitHub CLI installed successfully"
gh --version