#!/bin/bash
set -e

# Install Python UV Manager
echo "🐍 Installing UV Python package manager..."

if [ -z "${CURL_FLAGS:-}" ]; then
    if command -v certctl >/dev/null 2>&1; then
        eval "$(certctl env --quiet)" || true
    fi
fi
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

CERT_STATUS=${CERT_STATUS:-SECURE}
echo "📋 (Stateless) certificate status: $CERT_STATUS"

# Configure UV environment variables based on certificate status
if [ "$CERT_STATUS" = "INSECURE" ]; then
    echo "⚠️  Insecure network detected – configuring UV with relaxed hosts"
    echo "UV_INSECURE_HOST=pypi.org files.pythonhosted.org github.com" >> /etc/environment
else
    echo "✅ Secure network – standard TLS for UV"
fi
echo "UV_NATIVE_TLS=true" >> /etc/environment

# Display final UV configuration
echo "🎯 UV Configuration Summary:"
if grep -q "UV_INSECURE_HOST" /etc/environment 2>/dev/null; then
    echo "  - UV_INSECURE_HOST: $(grep UV_INSECURE_HOST /etc/environment | cut -d'=' -f2-) (reduced validation)"
else
    echo "  - No insecure hosts configured (full validation)"
fi

echo "🎉 UV installation and configuration complete!"