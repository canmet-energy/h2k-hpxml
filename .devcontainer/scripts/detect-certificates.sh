#!/bin/bash
# Certificate detection utility for Docker builds
# This script sets CURL_FLAGS based on certificate validation capability

detect_certificate_capability() {
    echo "🔍 Testing certificate connectivity..."
    
    # Check if certificates were already successfully installed
    if [ -f /etc/container-cert-status ]; then
        EXISTING_STATUS=$(cat /etc/container-cert-status)
        echo "📋 Existing certificate status: $EXISTING_STATUS"
        
        if [ "$EXISTING_STATUS" = "SECURE_CUSTOM" ]; then
            echo "✅ Custom certificates already installed successfully - using secure curl"
            export CERT_STATUS="SECURE_CUSTOM"
            export CURL_FLAGS="-fsSL"
            echo "Using curl flags: $CURL_FLAGS"
            return 0
        fi
    fi
    
    # Check if custom certificates were installed via environment
    if [ -f /etc/environment ] && grep -q "CUSTOM_CERT_PATH" /etc/environment; then
        echo "🔐 Custom certificates detected - testing connectivity..."
    fi
    
    if curl -sSf --connect-timeout 10 https://pypi.org/ > /dev/null 2>&1; then
        if [ -f /etc/environment ] && grep -q "CUSTOM_CERT_PATH" /etc/environment; then
            echo "✅ Certificate validation working with custom certificates - using secure curl"
            export CERT_STATUS="SECURE_CUSTOM"
        else
            echo "✅ Certificate validation working - using secure curl"
            export CERT_STATUS="SECURE"
        fi
        export CURL_FLAGS="-fsSL"
    else
        echo "⚠️  Certificate validation failed - using insecure curl"
        export CURL_FLAGS="-fsSLk"
        export CERT_STATUS="INSECURE"
    fi
    
    echo "Using curl flags: $CURL_FLAGS"
}

record_certificate_status() {
    echo "📝 Recording certificate status for user notification..."
    
    mkdir -p /etc/motd.d
    
    case "$CERT_STATUS" in
        "INSECURE")
            echo "INSECURE" > /etc/container-cert-status
            echo "⚠️  This container was built using insecure curl (certificate validation disabled)" > /etc/motd.d/cert-warning
            ;;
        "SECURE_CUSTOM")
            echo "SECURE_CUSTOM" > /etc/container-cert-status
            echo "🔐 This container was built with custom certificates and secure validation ✅" > /etc/motd.d/cert-status
            ;;
        "SECURE")
            echo "SECURE" > /etc/container-cert-status
            echo "✅ This container was built with secure certificate validation" > /etc/motd.d/cert-status
            ;;
    esac
}

# If script is executed (not sourced), run the detection
# Use POSIX-compatible test for sh compatibility
if [ "$(basename "$0")" = "detect-certificates.sh" ]; then
    detect_certificate_capability
    record_certificate_status
fi