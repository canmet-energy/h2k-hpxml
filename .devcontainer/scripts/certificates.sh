#!/bin/bash
# NRCAN certificate management for corporate network environments

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

install_certificates() {
    log_step "Checking network environment for certificate requirements..."
    
    # Skip certificate installation during Docker build (no Git credentials available)
    if [ -f "/.dockerenv" ] && [ -z "$CONTAINER_RUNTIME" ]; then
        log_info "Docker build context detected - skipping certificate installation"
        log_info "Certificates will be installed during container runtime if needed"
        export NRCAN_NETWORK=false
        return 0
    fi
    
    # Check if we're on NRCAN network by testing access to internal resources
    if [ "$(curl -k -o /dev/null -s -w "%{http_code}" "https://intranet.nrcan.gc.ca/")" -ge 200 ] && \
       [ "$(curl -o /dev/null -s -w "%{http_code}" "https://intranet.nrcan.gc.ca/")" -lt 400 ]; then
        
        log_step "NRCAN network detected - installing corporate certificates..."
        
        # Clone the NRCAN certificates repository
        log_info "Downloading NRCAN certificate installation tools..."
        git clone https://github.com/canmet-energy/linux_nrcan_certs.git /tmp/linux_nrcan_certs
        
        # Install certificates
        log_step "Installing NRCAN certificates..."
        cd /tmp/linux_nrcan_certs
        ./install_nrcan_certs.sh >/dev/null 2>&1
        
        # Cleanup
        cd - >/dev/null
        rm -rf /tmp/linux_nrcan_certs
        
        # Reload certificate store
        log_info "Updating system certificate store..."
        sudo update-ca-certificates >/dev/null 2>&1
        
        log_success "NRCAN certificates installed successfully"
        export NRCAN_NETWORK=true
        
    else
        log_info "Standard network environment detected - using default certificates"
        export NRCAN_NETWORK=false
    fi

    # Set certificate environment variables for all SSL operations
    if [ -f "/etc/ssl/certs/ca-certificates.crt" ]; then
        log_info "Configuring SSL certificate environment variables..."
        export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
        export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        
        # Persist to .bashrc for future sessions
        {
            echo "# SSL Certificate Configuration (added by certificates.sh)"
            echo "export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt"
            echo "export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt"
            echo "export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt"
            echo "export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt"
        } >> /home/vscode/.bashrc
        
        log_success "SSL environment variables configured"
    fi
}

# Run certificate installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_step "Starting certificate installation..."
    install_certificates
    log_success "Certificate setup complete"
fi