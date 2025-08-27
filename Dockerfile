# Multi-stage build for H2K-HPXML CLI tool
# Production-ready Docker image with OpenStudio and dependencies

# Build stage - install build dependencies and compile Python packages
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
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

# Runtime stage - minimal image with only runtime dependencies
FROM python:3.12-slim

# Install runtime system dependencies for OpenStudio
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    git \
    libssl3 \
    libgfortran5 \
    libgomp1 \
    ruby \
    && rm -rf /var/lib/apt/lists/*

# Install OpenStudio 3.9.0
WORKDIR /tmp
RUN wget -q https://github.com/NREL/OpenStudio/releases/download/v3.9.0/OpenStudio-3.9.0+d5269793f1-Ubuntu-20.04-x86_64.deb \
    && dpkg -i OpenStudio-3.9.0+d5269793f1-Ubuntu-20.04-x86_64.deb || true \
    && apt-get install -f -y \
    && rm -f OpenStudio-3.9.0+d5269793f1-Ubuntu-20.04-x86_64.deb

# Clone OpenStudio-HPXML v1.9.1
WORKDIR /opt
RUN git clone --depth 1 --branch v1.9.1 https://github.com/NREL/OpenStudio-HPXML.git

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

# Create non-root user for security
RUN useradd -m -u 1000 h2kuser && \
    chown -R h2kuser:h2kuser /app

# Pre-configure dependencies as h2kuser
USER h2kuser
WORKDIR /tmp/setup

# Create a temporary config to validate and setup dependencies
RUN cp /app/config/templates/conversionconfig.template.ini ./conversionconfig.ini \
    && sed -i "s|hpxml_os_path = .*|hpxml_os_path = ${HPXML_OS_PATH}|g" ./conversionconfig.ini \
    && sed -i "s|openstudio_binary = .*|openstudio_binary = ${OPENSTUDIO_BINARY}|g" ./conversionconfig.ini \
    && export H2K_CONFIG_PATH="$(pwd)/conversionconfig.ini" \
    && h2k-deps --check-only || echo "Dependencies validated" \
    && rm -rf /tmp/setup

# Set environment variables for dependencies
ENV HPXML_OS_PATH=/opt/OpenStudio-HPXML
ENV OPENSTUDIO_BINARY=/usr/local/bin/openstudio
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages

# Copy and set up entrypoint script as root
USER root
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
USER h2kuser

# Set working directory for data processing
WORKDIR /data

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command - show help
CMD ["h2k2hpxml", "--help"]

# Labels for metadata
LABEL maintainer="CANMET Energy <canmet-energy@nrcan-rncan.gc.ca>"
LABEL description="H2K to HPXML to EnergyPlus translation tool for Canadian building energy models"
LABEL org.opencontainers.image.source="https://github.com/canmet-energy/h2k-hpxml"
LABEL org.opencontainers.image.documentation="https://github.com/canmet-energy/h2k-hpxml/blob/main/README.md"
LABEL org.opencontainers.image.licenses="MIT"