# Development-only Dockerfile for H2K-HPXML CLI tool
# Simplified single-stage container focused on development workflow

FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu-22.04

# Build arguments for language versions
# Usage: docker build --build-arg PYTHON_VERSION=3.12 --build-arg RUBY_VERSION=3.1 .
ARG PYTHON_VERSION=3.12
ARG RUBY_VERSION=3.2.2

# Install certificate management (single script)
COPY .devcontainer/certs* /tmp/certs/
COPY .devcontainer/scripts/certctl-safe.sh /tmp/
RUN chmod +x /tmp/certctl-safe.sh && \
    /tmp/certctl-safe.sh install && \
    /tmp/certctl-safe.sh certs-refresh && \
    rm -rf /tmp/certctl-safe.sh /tmp/certs/

# Environment Configuration
ENV DEBIAN_FRONTEND=noninteractive
# Note: Certificate environment variables now managed dynamically by certctl-safe

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
    && rm -rf /var/lib/apt/lists/*

# Copy installation scripts and install development tools
# This modular approach makes the Dockerfile cleaner and scripts reusable
COPY .devcontainer/scripts/ /tmp/install-scripts/
RUN chmod +x /tmp/install-scripts/*.sh && \
    # Dynamically detect certificate environment for NRCan network
    bash -c '. /usr/local/bin/certctl && \
    certctl_load && \
    echo "Build environment detected: CERT_STATUS=$CERT_STATUS CURL_FLAGS=$CURL_FLAGS" && \
    # Install development tools (order matters for dependencies)
    /tmp/install-scripts/install-uv.sh && \
    /tmp/install-scripts/install-github-cli.sh && \
    /tmp/install-scripts/install-docker-cli.sh && \
    /tmp/install-scripts/install-nodejs.sh && \
    /tmp/install-scripts/install-python.sh --version '"${PYTHON_VERSION}"' && \
    rm -rf /var/lib/apt/lists/* /tmp/install-scripts'

# Set up application directory and permissions
RUN mkdir -p /app/deps && chown -R vscode:vscode /app

# Set up configuration template directory (will be populated by mount/copy)
USER root
RUN mkdir -p /app/config/templates

# Configure environment paths for development
ENV PATH="/app/.venv/bin:$PATH" \
    H2K_DEPS_DIR=/app/deps

# Set up for development workflow
USER vscode
WORKDIR /workspaces/h2k_hpxml
ENV DOCKER_BUILD_CONTEXT=true

## Stateless certificate detection: no persistent status display configured

# Default command for development
CMD ["/bin/bash"]

# Container metadata
LABEL maintainer="CANMET Energy <canmet-energy@nrcan-rncan.gc.ca>" \
    description="H2K to HPXML development environment" \
    version="dev" \
    org.opencontainers.image.source="https://github.com/canmet-energy/h2k-hpxml" \
    org.opencontainers.image.documentation="https://github.com/canmet-energy/h2k-hpxml/blob/main/README.md" \
    org.opencontainers.image.licenses="MIT"