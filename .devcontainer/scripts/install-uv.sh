#!/bin/bash
set -e

# Install Python UV Manager
echo "🐍 Installing UV Python package manager..."

CURL_FLAGS=${CURL_FLAGS:-"-fsSL"}
UV_VERSION="0.8.15"

curl $CURL_FLAGS --connect-timeout 30 -o /tmp/uv.tar.gz \
    "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz"

cd /tmp
tar -xzf uv.tar.gz
mv uv-x86_64-unknown-linux-gnu/uv /usr/local/bin/
chmod +x /usr/local/bin/uv
rm -rf /tmp/uv*

echo "✅ UV installed successfully"
uv --version

# Configure UV environment variables based on certificate status
echo "🔧 Configuring UV environment variables..."

# Read certificate status
CERT_STATUS_FILE="/etc/container-cert-status"
CERT_STATUS="SECURE"  # Default assumption

if [ -f "$CERT_STATUS_FILE" ]; then
    CERT_STATUS=$(cat "$CERT_STATUS_FILE")
    echo "📋 Certificate status: $CERT_STATUS"
else
    echo "ℹ️  No certificate status file found, assuming secure"
fi

# Configure UV environment variables based on certificate status
case "$CERT_STATUS" in
    "SECURE"|"SECURE_CUSTOM")
        echo "✅ Certificates are valid - configuring UV for secure TLS"
        # Use standard secure TLS - no special configuration needed
        echo "UV_NATIVE_TLS=true" >> /etc/environment
        echo "# UV configured for secure TLS validation" >> /etc/environment
        ;;
    "INSECURE")
        echo "⚠️  Certificates are problematic - configuring UV for insecure mode"
        # Configure UV for environments with certificate issues
        echo "UV_INSECURE_HOST=pypi.org files.pythonhosted.org github.com" >> /etc/environment
        echo "UV_NATIVE_TLS=true" >> /etc/environment
        echo "# UV configured for insecure hosts due to certificate issues" >> /etc/environment
        ;;
    *)
        echo "⚠️  Unknown certificate status: $CERT_STATUS, defaulting to secure"
        echo "UV_NATIVE_TLS=true" >> /etc/environment
        ;;
esac

# Display final UV configuration
echo "🎯 UV Configuration Summary:"
if grep -q "UV_INSECURE_HOST" /etc/environment 2>/dev/null; then
    echo "  - UV_INSECURE_HOST: $(grep UV_INSECURE_HOST /etc/environment | cut -d'=' -f2-)"
    echo "  - Security: Reduced certificate validation for corporate networks"
else
    echo "  - Standard secure TLS validation enabled"
    echo "  - Security: Full certificate validation active"
fi

echo "🎉 UV installation and configuration complete!"