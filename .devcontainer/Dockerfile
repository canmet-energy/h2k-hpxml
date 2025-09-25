# Development-only Dockerfile for H2K-HPXML CLI tool
# Simplified single-stage container focused on development workflow

FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu-22.04

# Build arguments for language versions
# Usage: docker build --build-arg PYTHON_VERSION=3.12 --build-arg RUBY_VERSION=3.1 .
ARG PYTHON_VERSION=3.12
ARG RUBY_VERSION=3.2.2

# Check for custom certificates and configure if present
COPY .devcontainer/certs* /tmp/certs/
COPY .devcontainer/scripts/install-certificates.sh /tmp/install-certificates.sh
RUN chmod +x /tmp/install-certificates.sh && \
    /tmp/install-certificates.sh && \
    rm -f /tmp/install-certificates.sh

# Environment Configuration with certificate awareness
ENV DEBIAN_FRONTEND=noninteractive \
    # Certificate environment variables for various tools
    SSL_CERT_DIR=/etc/ssl/certs \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

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
    # Detect certificate capability and set CURL_FLAGS for all installations
    . /tmp/install-scripts/detect-certificates.sh && detect_certificate_capability && \
    # Install development tools (order matters for dependencies)
    /tmp/install-scripts/install-uv.sh && \
    /tmp/install-scripts/install-github-cli.sh && \
    /tmp/install-scripts/install-docker-cli.sh && \
    /tmp/install-scripts/install-nodejs.sh && \
    /tmp/install-scripts/install-python.sh --version ${PYTHON_VERSION} && \
    /tmp/install-scripts/install-ruby.sh --version ${RUBY_VERSION} && \
    # Record certificate status for user notification
    record_certificate_status && \
    # Set up certificate status notification system
    /tmp/install-scripts/create-cert-status-script.sh vscode && \
    # Clean up
    rm -rf /var/lib/apt/lists/* /tmp/install-scripts

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

# Certificate status display is already configured by the create-cert-status-script.sh

# Default command for development
CMD ["/bin/bash"]

# Container metadata
LABEL maintainer="CANMET Energy <canmet-energy@nrcan-rncan.gc.ca>" \
    description="H2K to HPXML development environment" \
    version="dev" \
    org.opencontainers.image.source="https://github.com/canmet-energy/h2k-hpxml" \
    org.opencontainers.image.documentation="https://github.com/canmet-energy/h2k-hpxml/blob/main/README.md" \
    org.opencontainers.image.licenses="MIT"