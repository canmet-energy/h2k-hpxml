# Production Dockerfile for H2K-HPXML
# Build:
#   docker build -t h2k-hpxml .
# - Installs OS libraries commonly required by OpenStudio CLI
# - Installs Python via uv and sets up an isolated virtual environment
# - Installs the h2k-hpxml package with entry points (h2k-hpxml, h2k-resilience, h2k-deps)
# - Uses a non-root user so h2k-deps can install dependencies into user-writable locations

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
  UV_NATIVE_TLS=true \
  UV_INSECURE_HOST="pypi.org files.pythonhosted.org github.com"

# Install system dependencies required by OpenStudio CLI and general tooling
# Notes:
# - libgfortran5, libgomp1, libssl3, libx11-6, libxext6 are common OpenStudio runtime deps
# - ruby is used by OpenStudio-HPXML workflow scripts
# - unzip and curl for downloads performed by h2k-deps
# - build-essential, git in case native wheels or builds are needed during installation
RUN apt-get update && apt-get install -y \
  apt-transport-https \
  ca-certificates \
  gnupg \
  lsb-release \
  curl \
  git \
  ruby \
  unzip \
  build-essential \
  libgfortran5 \
  libgomp1 \
  libssl3 \
  libx11-6 \
  libxext6 \
  libxrender1 \
  libfontconfig1 \
  libglu1-mesa \
  && rm -rf /var/lib/apt/lists/*

# Install uv (Python and package manager)
RUN curl -fsSLk --connect-timeout 30 -o /tmp/uv.tar.gz \
  https://github.com/astral-sh/uv/releases/download/0.8.15/uv-x86_64-unknown-linux-gnu.tar.gz \
  && cd /tmp \
  && tar -xzf uv.tar.gz \
  && mv uv-x86_64-unknown-linux-gnu/uv /usr/local/bin/uv \
  && chmod +x /usr/local/bin/uv \
  && rm -rf /tmp/uv*

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
RUN uv python install 3.12 \
  && uv venv --python 3.12 ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:${PATH}"

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
