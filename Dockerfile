# Multi-stage build for H2K-HPXML CLI tool
# Optimized with devcontainer base for development

# Build arguments with default values
ARG UBUNTU_VERSION=22.04
ARG PYTHON_VERSION=3.12
ARG OPENSTUDIO_VERSION=3.9.0
ARG OPENSTUDIO_SHA=c77fbb9569
ARG OPENSTUDIO_HPXML_VERSION=v1.9.1

# Build stage - install build dependencies and compile Python packages
FROM python:${PYTHON_VERSION}-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir build wheel

# Copy source code and build the package
COPY src/ ./src/
COPY README.md CLAUDE.md ./
# Set version for setuptools_scm since we don't have git metadata in Docker context
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_H2K_HPXML=1.0.0
RUN python -m build

# Production stage - Minimal runtime with only necessary components
FROM ubuntu:${UBUNTU_VERSION} AS production

# Re-declare build arguments in production stage
ARG PYTHON_VERSION=3.12
ARG OPENSTUDIO_VERSION=3.9.0
ARG OPENSTUDIO_SHA=c77fbb9569
ARG OPENSTUDIO_HPXML_VERSION=v1.9.1

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Configure insecure operations for corporate networks during build
# These will be overridden at runtime with proper certificates
ENV PYTHONHTTPSVERIFY=0
ENV CURL_CA_BUNDLE=""
ENV REQUESTS_CA_BUNDLE=""
ENV GIT_SSL_NO_VERIFY=true

# Install runtime dependencies including X11 for OpenStudio (but no dev tools)
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    unzip \
    git \
    libssl3 \
    libgfortran5 \
    libgomp1 \
    ruby \
    libx11-6 \
    libxext6 \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python${PYTHON_VERSION} \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install pip for Python
RUN curl -sSk https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION}

# Configure pip to work with corporate networks (ignore SSL during build)
RUN python${PYTHON_VERSION} -m pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org" \
    && python${PYTHON_VERSION} -m pip config set global.disable-pip-version-check true

# Set Python as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1

# Install OpenStudio
WORKDIR /tmp
ARG UBUNTU_VERSION=22.04
RUN curl -L --progress-bar --insecure -o OpenStudio.deb \
    "https://github.com/NREL/OpenStudio/releases/download/v${OPENSTUDIO_VERSION}/OpenStudio-${OPENSTUDIO_VERSION}+${OPENSTUDIO_SHA}-Ubuntu-${UBUNTU_VERSION}-x86_64.deb" \
    && dpkg -i OpenStudio.deb \
    && rm -f OpenStudio.deb

# Clone OpenStudio-HPXML
WORKDIR /opt
RUN git config --global http.sslverify false \
    && git clone --depth 1 --branch ${OPENSTUDIO_HPXML_VERSION} https://github.com/NREL/OpenStudio-HPXML.git \
    && rm -rf OpenStudio-HPXML/.git

# Set up application directory
WORKDIR /app

# Copy built package from builder stage
COPY --from=builder /app/dist/*.whl ./

# Install the package and its dependencies
RUN pip install --no-cache-dir *.whl \
    && rm -f *.whl

# Set up configuration template
RUN mkdir -p /app/config/templates
COPY config/defaults/conversionconfig.template.ini /app/config/templates/

# Create non-root user for security (no sudo access for production)
RUN useradd -m -u 1000 h2kuser && \
    chown -R h2kuser:h2kuser /app

# Set environment variables for dependencies
ENV HPXML_OS_PATH=/opt/OpenStudio-HPXML
ENV OPENSTUDIO_BINARY=/usr/local/bin/openstudio
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages

# Copy and set up entrypoint script
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Switch to non-root user
USER h2kuser
WORKDIR /data

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["h2k2hpxml", "--help"]

# Development stage - Use VS Code devcontainer base with development tools
FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu-22.04 AS development

# Re-declare build arguments for development stage
ARG PYTHON_VERSION=3.12
ARG OPENSTUDIO_VERSION=3.9.0
ARG OPENSTUDIO_SHA=c77fbb9569
ARG OPENSTUDIO_HPXML_VERSION=v1.9.1

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Configure insecure operations for corporate networks during build
# These will be overridden at runtime with proper certificates
ENV PYTHONHTTPSVERIFY=0
ENV CURL_CA_BUNDLE=""
ENV REQUESTS_CA_BUNDLE=""
ENV GIT_SSL_NO_VERIFY=true

# Switch to root for installations
USER root

# Install Python 3.12 from deadsnakes PPA
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-venv \
    libgfortran5 \
    libgomp1 \
    ruby \
    libx11-6 \
    libxext6 \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI for devcontainer support
RUN curl -fsSLk https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-compose-plugin \
    && groupadd -f docker \
    && usermod -aG docker vscode \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.12
RUN curl -sSk https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION}

# Configure pip to work with corporate networks (ignore SSL during build)
RUN python${PYTHON_VERSION} -m pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org" \
    && python${PYTHON_VERSION} -m pip config set global.disable-pip-version-check true

# Set Python as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1

# Install OpenStudio
WORKDIR /tmp
ARG UBUNTU_VERSION=22.04
RUN curl -L --progress-bar --insecure -o OpenStudio.deb \
    "https://github.com/NREL/OpenStudio/releases/download/v${OPENSTUDIO_VERSION}/OpenStudio-${OPENSTUDIO_VERSION}+${OPENSTUDIO_SHA}-Ubuntu-${UBUNTU_VERSION}-x86_64.deb" \
    && dpkg -i OpenStudio.deb \
    && rm -f OpenStudio.deb

# Clone OpenStudio-HPXML
WORKDIR /opt
RUN git config --global http.sslverify false \
    && git clone --depth 1 --branch ${OPENSTUDIO_HPXML_VERSION} https://github.com/NREL/OpenStudio-HPXML.git \
    && rm -rf OpenStudio-HPXML/.git

# Copy built package from builder stage and install
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl

# Set up configuration template
RUN mkdir -p /app/config/templates
COPY config/defaults/conversionconfig.template.ini /app/config/templates/

# Set environment variables for dependencies
ENV HPXML_OS_PATH=/opt/OpenStudio-HPXML
ENV OPENSTUDIO_BINARY=/usr/local/bin/openstudio
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages

# Copy development setup script and its dependencies
COPY .devcontainer/dev_setup.sh /tmp/dev_setup.sh
COPY .devcontainer/scripts/ /tmp/scripts/
RUN chmod +x /tmp/dev_setup.sh

# Install Node.js 18.x directly from official binaries (bypasses SSL/repository issues)
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
    && npm config set registry https://registry.npmjs.org/ \
    && node --version \
    && npm --version

# Switch to vscode user (already exists in devcontainer base)
USER vscode
WORKDIR /workspaces/h2k_hpxml

# Run development setup script with Claude support (certificates will be installed at runtime)
ENV DOCKER_BUILD_CONTEXT=true
RUN bash /tmp/dev_setup.sh --claude

# Default to development environment with bash
CMD ["/bin/bash"]

# Labels for metadata
LABEL maintainer="CANMET Energy <canmet-energy@nrcan-rncan.gc.ca>"
LABEL description="H2K to HPXML to EnergyPlus translation tool for Canadian building energy models"
LABEL org.opencontainers.image.source="https://github.com/canmet-energy/h2k-hpxml"
LABEL org.opencontainers.image.documentation="https://github.com/canmet-energy/h2k-hpxml/blob/main/README.md"
LABEL org.opencontainers.image.licenses="MIT"