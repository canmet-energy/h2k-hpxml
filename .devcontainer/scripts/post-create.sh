#!/bin/bash
# Post-create setup script for H2K-HPXML devcontainer
# This script runs after the container is created to set up the development environment

set -e  # Exit on error

echo "🚀 Starting post-create setup..."

# Refresh certificate status and enable terminal banner (non-blocking)
if command -v certctl >/dev/null 2>&1; then
    echo "🔐 Checking certificate status..."
    certctl banner || true

    # Enable certificate status banner in new terminals
    echo "🔐 Enabling certificate status banner for new terminals..."
    sudo sed -i 's/^    # certctl_banner 2>\/dev\/null || true$/    certctl_banner 2>\/dev\/null || true/' /etc/profile.d/certctl-env.sh || true
fi

# Fix Docker socket permissions for Docker-in-Docker support Useful for testing Dockerfile builds
echo "🐳 Configuring Docker socket permissions..."
sudo chgrp docker /var/run/docker.sock

# Set up Python virtual environment as required by the project
echo "🐍 Setting up Python virtual environment..."
rm -rf .venv
uv venv --python 3.12 --clear
uv pip install -e '.[dev]'

# Install dependencies such as OpenStudio, EnergyPlus, HPXML, etc.
echo "📦 Installing H2K dependencies...This may take a minute..."
uv run h2k-deps --install-quiet

# Configure Git (personalize as needed, edit as needed. Uncomment and set your details but avoid committing them)
echo "📝 Configuring Git..."
# git config --global user.email 'phylroy.lopez@nrcan.gc.ca' && git config --global user.name 'Phylroy Lopez'

# Configure bash environment for auto-activation of virtual environment (venv) for h2k-hpxml python.
echo "⚙️ Configuring shell environment..."

# Add virtual environment auto-activation to bashrc
if ! grep -q 'Auto-activate h2k-hpxml venv' ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'EOF'

# Auto-activate h2k-hpxml venv
for CANDIDATE in /workspaces/h2k-hpxml /workspaces/h2k_hpxml; do
  if [ -f "${CANDIDATE}/.venv/bin/activate" ] && [ -z "$VIRTUAL_ENV" ]; then
    . "${CANDIDATE}/.venv/bin/activate"
    echo "🐍 Virtual environment activated: $(python --version)"
    break
  fi
done

EOF
fi

# Note: Certificate environment now handled by /etc/profile.d/certctl-env.sh
# No need to add anything to bashrc - profile.d integration handles everything

# Ensure bash_profile sources bashrc
if [ ! -f ~/.bash_profile ] || ! grep -q '.bashrc' ~/.bash_profile 2>/dev/null; then
    echo '[[ -f ~/.bashrc ]] && . ~/.bashrc' >> ~/.bash_profile
fi

echo "✅ Post-create setup complete!"
echo ""
echo "📌 Note: A new terminal may be needed to activate all shell configurations."