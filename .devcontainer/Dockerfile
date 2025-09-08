# Development-only Dockerfile for H2K-HPXML CLI tool
# Simplified single-stage container focused on development workflow

FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu-22.04

# Environment Configuration
ENV DEBIAN_FRONTEND=noninteractive \
    UV_INSECURE_HOST="pypi.org files.pythonhosted.org github.com" \
    UV_NATIVE_TLS=true

# Install system dependencies required by OpenStudio and development tools
RUN apt-get update && apt-get install -y \
    # APT and repository tools
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    # Basic utilities
    curl \
    git \
    ruby \
    unzip \
    # Development tools
    build-essential \
    # Runtime libraries needed by OpenStudio
    libgfortran5 \
    libgomp1 \
    libssl3 \
    # X11 libraries for OpenStudio
    libx11-6 \
    libxext6 \
    # Install uv - standalone Python manager
    && curl -LsSfk --insecure --connect-timeout 30 -o /tmp/uv.tar.gz \
    "https://github.com/astral-sh/uv/releases/download/0.8.15/uv-x86_64-unknown-linux-gnu.tar.gz" \
    && cd /tmp && tar -xzf uv.tar.gz \
    && mv uv-x86_64-unknown-linux-gnu/uv /usr/local/bin/ \
    && chmod +x /usr/local/bin/uv && rm -rf /tmp/uv* \
    # Install GitHub CLI (insecure for corporate networks)
    && curl -fsSLk --insecure https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI for Docker-in-Docker support
RUN curl -fsSLk https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-compose-plugin \
    && groupadd -f docker \
    && usermod -aG docker vscode \
    && rm -rf /var/lib/apt/lists/*

# Set up application directory and permissions
RUN mkdir -p /app/deps && chown -R vscode:vscode /app

# Switch to vscode user for Python environment setup
USER vscode

# Create Python virtual environment using version from pyproject.toml
# This will be done by the postCreateCommand in devcontainer.json
# which has access to the mounted source code

# Set up configuration template directory (will be populated by mount/copy)
USER root
RUN mkdir -p /app/config/templates

# Configure environment paths for development
ENV PATH="/app/.venv/bin:$PATH" \
    H2K_DEPS_DIR=/app/deps

# Install Node.js for development tooling
RUN curl -fsSL -k --connect-timeout 30 https://nodejs.org/dist/v18.20.4/node-v18.20.4-linux-x64.tar.xz -o /tmp/node.tar.xz \
    && cd /tmp \
    && tar -xJf node.tar.xz \
    && cp -r node-v18.20.4-linux-x64/* /usr/local/ \
    && rm -rf /tmp/node* \
    && ln -sf /usr/local/bin/node /usr/bin/node \
    && ln -sf /usr/local/bin/npm /usr/bin/npm \
    && ln -sf /usr/local/bin/npx /usr/bin/npx \
    && npm config set ca "" \
    && npm config set strict-ssl false \
    && npm config set registry https://registry.npmjs.org/

# Set up for development workflow
USER vscode
WORKDIR /workspaces/h2k_hpxml
ENV DOCKER_BUILD_CONTEXT=true

# Default command for development
CMD ["/bin/bash"]

# Container metadata
LABEL maintainer="CANMET Energy <canmet-energy@nrcan-rncan.gc.ca>" \
    description="H2K to HPXML development environment" \
    version="dev" \
    org.opencontainers.image.source="https://github.com/canmet-energy/h2k-hpxml" \
    org.opencontainers.image.documentation="https://github.com/canmet-energy/h2k-hpxml/blob/main/README.md" \
    org.opencontainers.image.licenses="MIT"