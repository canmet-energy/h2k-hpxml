# Production Dockerfile for H2K-HPXML
# Build:
#   docker build -t h2k-hpxml .
# - Installs OS libraries commonly required by OpenStudio CLI
# - Installs Python via uv and sets up an isolated virtual environment
# - Installs the h2k-hpxml package with entry points (h2k-hpxml, h2k-resilience, h2k-deps)
# - Uses a non-root user so h2k-deps can install dependencies into user-writable locations

FROM ubuntu:22.04

# Build arguments for language versions
# Usage: docker build --build-arg PYTHON_VERSION=3.12 --build-arg RUBY_VERSION=3.1 .
ARG PYTHON_VERSION=3.12
ARG RUBY_VERSION=3.2

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
  # Record certificate status for user notification
  record_certificate_status && \
  # Set up certificate status notification system
  /tmp/install-scripts/create-cert-status-script.sh && \
  # Keep the script for later user setup (copy to permanent location)
  cp /tmp/install-scripts/create-cert-status-script.sh /usr/local/bin/ && \
  # Clean up
  rm -rf /var/lib/apt/lists/* /tmp/install-scripts

# Create a non-root user for running CLI tools and installing user-scoped deps
ARG USERNAME=appuser
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid ${USER_GID} ${USERNAME} \
  && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}

# Prepare a dedicated Python virtual environment using uv
ENV VENV_PATH=/opt/venv
# Create target venv directory and grant ownership to the app user first
RUN mkdir -p ${VENV_PATH} && chown -R ${USERNAME}:${USERNAME} ${VENV_PATH}

# Set workdir and copy project files
WORKDIR /app
COPY . /app

# (Package installation moved after venv creation under non-root user)

###############
# Runtime user
###############
# Switch to non-root user for runtime; h2k-deps will install OpenStudio/OpenStudio-HPXML
# Ensure app user owns the workdir so tools like `uv run` can create local environments
RUN chown -R ${USERNAME}:${USERNAME} /app
USER ${USERNAME}

# Install uv-managed Python and create venv as the app user so base interpreter
# lives under /home/appuser/.local/share/uv and is readable at runtime
RUN uv python install ${PYTHON_VERSION} \
  && uv venv --python ${PYTHON_VERSION} ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:${PATH}"

# Add certificate status display to user profile
RUN /usr/local/bin/create-cert-status-script.sh ${USERNAME}

# Install the package with CLI entry points into the venv
# Use --no-cache-dir behavior by uv implicitly; install in non-editable mode for production
RUN uv pip install .

# Pre-install OpenStudio and OpenStudio-HPXML so the image is ready to run
# Installs into user-writable locations under /home/appuser/.local/share
RUN h2k-deps --install-quiet

# Create user configuration from template and populate detected paths
RUN h2k-deps --setup

# Default volume for input/output convenience
VOLUME ["/data"]

# Default help; override with explicit command, e.g.:
# Linux/Mac:
#   docker run --rm -v $(pwd):/data h2k-hpxml h2k-hpxml /data/input.h2k
# Windows (PowerShell):
#   docker run --rm -v "${PWD}:/data" h2k-hpxml h2k-hpxml /data/input.h2k
# Windows (cmd.exe):
#   docker run --rm -v "%cd%:/data" h2k-hpxml h2k-hpxml /data/input.h2k
CMD ["h2k-hpxml", "--help"]

LABEL org.opencontainers.image.title="H2K-HPXML" \
  org.opencontainers.image.description="H2K to HPXML to EnergyPlus translation tool with OpenStudio CLI runtime deps" \
  org.opencontainers.image.licenses="MIT" \
  org.opencontainers.image.source="https://github.com/canmet-energy/h2k-hpxml"
