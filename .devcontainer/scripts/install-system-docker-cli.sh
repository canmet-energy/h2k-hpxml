#!/bin/bash
set -e

# Install Docker CLI
echo "🐳 Installing Docker CLI..."

# Check for root/sudo privileges
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script requires root privileges"
    echo "   Please run with sudo: sudo $0 $@"
    exit 1
fi

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Add Docker repository key and source
curl ${CURL_FLAGS} https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list and install
apt-get update
apt-get install -y docker-ce-cli docker-compose-plugin

# Set up docker group for vscode user
groupadd -f docker
usermod -aG docker vscode

echo "✅ Docker CLI installed successfully"
docker --version