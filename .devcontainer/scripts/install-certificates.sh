#!/bin/bash
set -e

echo "🔐 Installing custom certificates..."

# Default certificate directory in container
CERT_SOURCE_DIR="${CERT_SOURCE_DIR:-/tmp/certs}"
CERT_DEST_DIR="/usr/local/share/ca-certificates"

# Function to check if certificate files exist (excluding README files)
check_certificates() {
    local cert_found=false
    
    # Check for certificate files more reliably (exclude README files)
    for cert in "$CERT_SOURCE_DIR"/*.crt "$CERT_SOURCE_DIR"/*.pem; do
        if [ -f "$cert" ] && [ "$(basename "$cert")" != "README.md" ]; then
            cert_found=true
            break
        fi
    done
    
    echo "$cert_found"
}

# Function to install certificate files
install_certificate_files() {
    echo "📋 Installing certificate files..."
    
    # Copy .crt files directly
    for cert in "$CERT_SOURCE_DIR"/*.crt; do
        if [ -f "$cert" ]; then
            cp "$cert" "$CERT_DEST_DIR/" && echo "  ✅ Copied $(basename "$cert")"
        fi
    done
    
    # Convert .pem files to .crt and copy
    for cert in "$CERT_SOURCE_DIR"/*.pem; do
        if [ -f "$cert" ]; then
            local base_name=$(basename "$cert" .pem)
            cp "$cert" "$CERT_DEST_DIR/${base_name}.crt" && \
            echo "  ✅ Copied $(basename "$cert") as ${base_name}.crt"
        fi
    done
}

# Function to update system certificate store
update_certificate_store() {
    echo "🔄 Updating system certificate store..."
    
    if update-ca-certificates; then
        echo "✅ Custom certificates installed successfully"
        echo "CUSTOM_CERT_PATH=$CERT_DEST_DIR" > /etc/environment
        echo "SECURE_CUSTOM" > /etc/container-cert-status
        return 0
    else
        echo "⚠️  Certificate installation failed, but continuing..."
        echo "CERT_INSTALL_FAILED=true" > /etc/environment
        echo "INSECURE" > /etc/container-cert-status
        return 1
    fi
}

# Main installation logic
main() {
    # Ensure certificate directories exist
    mkdir -p "$CERT_DEST_DIR"
    
    # Check if certificate source directory exists
    if [ ! -d "$CERT_SOURCE_DIR" ]; then
        echo "ℹ️  No certificate source directory found at $CERT_SOURCE_DIR"
        echo "SECURE" > /etc/container-cert-status
        return 0
    fi
    
    # Check for certificate files
    if [ "$(check_certificates)" = "true" ]; then
        echo "🔐 Custom certificates found - configuring container..."
        
        # Install certificate files
        install_certificate_files
        
        # Update system certificate store
        if update_certificate_store; then
            echo "🎉 Certificate installation completed successfully!"
        else
            echo "⚠️  Certificate installation completed with warnings"
        fi
    else
        echo "ℹ️  No custom certificates found in $CERT_SOURCE_DIR/"
        echo "SECURE" > /etc/container-cert-status
    fi
    
    # Clean up source directory if it exists
    if [ -d "$CERT_SOURCE_DIR" ]; then
        rm -rf "$CERT_SOURCE_DIR"
        echo "🧹 Cleaned up certificate source directory"
    fi
}

# Run main function
main "$@"

echo "✅ Certificate installation script completed"