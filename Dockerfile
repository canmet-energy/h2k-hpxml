# Multi-stage build for H2K-HPXML CLI tool
# Optimized with devcontainer base for development

# ===================================================================
# GLOBAL BUILD ARGUMENTS
# ===================================================================
ARG UBUNTU_VERSION=22.04
ARG OPENSTUDIO_VERSION=3.9.0
ARG OPENSTUDIO_SHA=c77fbb9569
ARG OPENSTUDIO_HPXML_VERSION=v1.9.1

# ===================================================================
# BUILDER STAGE - Build Python package
# ===================================================================
FROM ubuntu:${UBUNTU_VERSION} AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv - download binary directly to bypass SSL issues
RUN curl -LsSfk --insecure --connect-timeout 30 -o /tmp/uv.tar.gz \
        "https://github.com/astral-sh/uv/releases/download/0.8.15/uv-x86_64-unknown-linux-gnu.tar.gz" \
    && cd /tmp \
    && tar -xzf uv.tar.gz \
    && mv uv-x86_64-unknown-linux-gnu/uv /usr/local/bin/ \
    && chmod +x /usr/local/bin/uv \
    && rm -rf /tmp/uv*

# Set up build environment
WORKDIR /app
COPY pyproject.toml ./

# Configure uv for corporate networks
ENV UV_INSECURE_HOST="pypi.org files.pythonhosted.org github.com" \
    UV_NATIVE_TLS=true

# Copy source code and build the package
COPY src/ ./src/
COPY README.md CLAUDE.md ./
# Set version for setuptools_scm since we don't have git metadata in Docker context
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_H2K_HPXML=1.0.0
# uv automatically detects Python version from pyproject.toml and builds the package
RUN uv build

# ===================================================================
# PRODUCTION STAGE - Minimal runtime image
# ===================================================================
FROM ubuntu:${UBUNTU_VERSION} AS production

# Re-declare ARGs needed in this stage
ARG OPENSTUDIO_VERSION
ARG OPENSTUDIO_SHA
ARG OPENSTUDIO_HPXML_VERSION
ARG UBUNTU_VERSION

# Environment Configuration
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONHTTPSVERIFY=0 \
    CURL_CA_BUNDLE="" \
    REQUESTS_CA_BUNDLE="" \
    GIT_SSL_NO_VERIFY=true \
    UV_INSECURE_HOST="pypi.org files.pythonhosted.org github.com" \
    UV_NATIVE_TLS=true

# Install system dependencies (no Python needed!)
RUN apt-get update && apt-get install -y \
    # Basic utilities
    curl \
    git \
    ruby \
    unzip \
    ca-certificates \
    # Runtime libraries
    libgfortran5 \
    libgomp1 \
    libssl3 \
    # X11 libraries for OpenStudio
    libx11-6 \
    libxext6 \
    # Configure insecure HTTPS for corporate networks
    && echo 'Acquire::https::Verify-Peer "false";' > /etc/apt/apt.conf.d/99no-check-certificate \
    && echo 'Acquire::https::Verify-Host "false";' >> /etc/apt/apt.conf.d/99no-check-certificate \
    # Install uv - standalone Python manager
    && curl -LsSfk --insecure --connect-timeout 30 -o /tmp/uv.tar.gz \
        "https://github.com/astral-sh/uv/releases/download/0.8.15/uv-x86_64-unknown-linux-gnu.tar.gz" \
    && cd /tmp && tar -xzf uv.tar.gz \
    && mv uv-x86_64-unknown-linux-gnu/uv /usr/local/bin/ \
    && chmod +x /usr/local/bin/uv && rm -rf /tmp/uv* \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install OpenStudio and OpenStudio-HPXML
WORKDIR /tmp
RUN curl -L --progress-bar --insecure -o OpenStudio.deb \
        "https://github.com/NREL/OpenStudio/releases/download/v${OPENSTUDIO_VERSION}/OpenStudio-${OPENSTUDIO_VERSION}+${OPENSTUDIO_SHA}-Ubuntu-${UBUNTU_VERSION}-x86_64.deb" \
    && dpkg -i OpenStudio.deb \
    && rm -f OpenStudio.deb \
    # Clone OpenStudio-HPXML
    && git config --global http.sslverify false \
    && cd /opt \
    && git clone --depth 1 --branch ${OPENSTUDIO_HPXML_VERSION} https://github.com/NREL/OpenStudio-HPXML.git \
    && rm -rf OpenStudio-HPXML/.git

# Install application and configure
WORKDIR /opt
COPY --from=builder /app/dist/*.whl ./
COPY --from=builder /app/pyproject.toml ./
# Create directories and non-root user first  
RUN mkdir -p /app/config/templates \
    && useradd -m -u 1000 h2kuser \
    && chown -R h2kuser:h2kuser /app \
    && chown h2kuser:h2kuser *.whl *.toml

# Switch to h2kuser and install Python packages
USER h2kuser
RUN PYTHON_VERSION=$(grep "requires-python" pyproject.toml | grep -o "[0-9]\+\.[0-9]\+" | head -1) \
    && echo "Installing Python $PYTHON_VERSION from pyproject.toml" \
    && uv python install $PYTHON_VERSION \
    && uv venv /app/.venv --python $PYTHON_VERSION \
    && . /app/.venv/bin/activate && uv pip install *.whl

# Switch back to root for final setup
USER root
RUN rm -f /opt/*.whl /opt/*.toml

COPY config/defaults/conversionconfig.template.ini /app/config/templates/

# Configure runtime environment
ENV HPXML_OS_PATH=/opt/OpenStudio-HPXML \
    OPENSTUDIO_BINARY=/usr/local/bin/openstudio \
    PATH="/app/.venv/bin:$PATH"

# Set up entrypoint and switch to non-root user
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER h2kuser
WORKDIR /data

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["h2k2hpxml", "--help"]

# ===================================================================
# DEVELOPMENT STAGE - VS Code devcontainer with development tools
# ===================================================================
FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu-${UBUNTU_VERSION} AS development

# Re-declare ARGs needed in this stage
ARG OPENSTUDIO_VERSION
ARG OPENSTUDIO_SHA
ARG OPENSTUDIO_HPXML_VERSION
ARG UBUNTU_VERSION

# Environment Configuration
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONHTTPSVERIFY=0 \
    CURL_CA_BUNDLE="" \
    REQUESTS_CA_BUNDLE="" \
    GIT_SSL_NO_VERIFY=true \
    UV_INSECURE_HOST="pypi.org files.pythonhosted.org github.com" \
    UV_NATIVE_TLS=true

# Install system dependencies and development tools (no Python needed!)
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
    # Runtime libraries
    libgfortran5 \
    libgomp1 \
    libssl3 \
    # X11 libraries for OpenStudio
    libx11-6 \
    libxext6 \
    # Configure insecure HTTPS for corporate networks
    && echo 'Acquire::https::Verify-Peer "false";' > /etc/apt/apt.conf.d/99no-check-certificate \
    && echo 'Acquire::https::Verify-Host "false";' >> /etc/apt/apt.conf.d/99no-check-certificate \
    # Install uv - standalone Python manager
    && curl -LsSfk --insecure --connect-timeout 30 -o /tmp/uv.tar.gz \
        "https://github.com/astral-sh/uv/releases/download/0.8.15/uv-x86_64-unknown-linux-gnu.tar.gz" \
    && cd /tmp && tar -xzf uv.tar.gz \
    && mv uv-x86_64-unknown-linux-gnu/uv /usr/local/bin/ \
    && chmod +x /usr/local/bin/uv && rm -rf /tmp/uv* \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (Python managed by uv)
RUN curl -fsSLk https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-compose-plugin \
    && groupadd -f docker \
    && usermod -aG docker vscode \
    && rm -rf /var/lib/apt/lists/*

# Install OpenStudio, OpenStudio-HPXML, and application
WORKDIR /tmp
RUN curl -L --progress-bar --insecure -o OpenStudio.deb \
        "https://github.com/NREL/OpenStudio/releases/download/v${OPENSTUDIO_VERSION}/OpenStudio-${OPENSTUDIO_VERSION}+${OPENSTUDIO_SHA}-Ubuntu-${UBUNTU_VERSION}-x86_64.deb" \
    && dpkg -i OpenStudio.deb \
    && rm -f OpenStudio.deb \
    # Clone OpenStudio-HPXML
    && git config --global http.sslverify false \
    && cd /opt \
    && git clone --depth 1 --branch ${OPENSTUDIO_HPXML_VERSION} https://github.com/NREL/OpenStudio-HPXML.git \
    && rm -rf OpenStudio-HPXML/.git

# Install application
COPY --from=builder /app/dist/*.whl /tmp/
COPY --from=builder /app/pyproject.toml /tmp/
# Ensure /app exists and setup permissions
RUN mkdir -p /app && chown -R vscode:vscode /app
# Switch to vscode user for Python installation
USER vscode
RUN PYTHON_VERSION=$(grep "requires-python" /tmp/pyproject.toml | grep -o "[0-9]\+\.[0-9]\+" | head -1) \
    && echo "Installing Python $PYTHON_VERSION from pyproject.toml" \
    && uv python install $PYTHON_VERSION \
    && uv venv /app/.venv --python $PYTHON_VERSION \
    && . /app/.venv/bin/activate && uv pip install /tmp/*.whl
USER root
RUN rm -f /tmp/*.whl /tmp/*.toml

# Set up configuration and environment
RUN mkdir -p /app/config/templates
COPY config/defaults/conversionconfig.template.ini /app/config/templates/

ENV HPXML_OS_PATH=/opt/OpenStudio-HPXML \
    OPENSTUDIO_BINARY=/usr/local/bin/openstudio \
    PATH="/app/.venv/bin:$PATH"

# Install Node.js and configure development environment
COPY .devcontainer/dev_setup.sh /tmp/dev_setup.sh
COPY .devcontainer/scripts/ /tmp/scripts/
RUN chmod +x /tmp/dev_setup.sh \
    # Install Node.js 18.x directly from official binaries
    && curl -fsSL -k --connect-timeout 30 https://nodejs.org/dist/v18.20.4/node-v18.20.4-linux-x64.tar.xz -o /tmp/node.tar.xz \
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

# Switch to vscode user and run development setup
USER vscode
WORKDIR /workspaces/h2k_hpxml
ENV DOCKER_BUILD_CONTEXT=true
RUN bash /tmp/dev_setup.sh --claude

CMD ["/bin/bash"]

# ===================================================================
# METADATA
# ===================================================================
LABEL maintainer="CANMET Energy <canmet-energy@nrcan-rncan.gc.ca>" \
      description="H2K to HPXML to EnergyPlus translation tool for Canadian building energy models" \
      org.opencontainers.image.source="https://github.com/canmet-energy/h2k-hpxml" \
      org.opencontainers.image.documentation="https://github.com/canmet-energy/h2k-hpxml/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT"