FROM canmet/model_dev_container:3.9.0

ARG IS_DEVCONTAINER=false
ENV IS_DEVCONTAINER=${IS_DEVCONTAINER}

# Install Docker CLI (not daemon) for building production images
USER root

# Create docker group first
RUN groupadd -f docker

# Install Docker packages
RUN apt-get update && \
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

# Add vscode user to docker group
RUN usermod -aG docker vscode

WORKDIR /workspaces/h2k_hpxml

# Copy script to /tmp - no chmod needed
COPY dev_setup.sh /tmp/dev_setup.sh

USER vscode
RUN if [ "$IS_DEVCONTAINER" = "true" ]; then \
        echo "Setting up devcontainer-specific configuration..." && \
        bash /tmp/dev_setup.sh --claude; \
    else \
        echo "Setting up standard configuration..." && \
        bash /tmp/dev_setup.sh; \
    fi

