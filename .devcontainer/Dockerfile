FROM canmet/model_dev_container:3.9.0

ARG IS_DEVCONTAINER=false
ENV IS_DEVCONTAINER=${IS_DEVCONTAINER}

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

