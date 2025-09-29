#!/bin/bash
set -e

echo "☁️ Installing AWS CLI..."

# Check for root/sudo privileges
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script requires root privileges"
    echo "   Please run with sudo: sudo $0 $@"
    exit 1
fi

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Parse command line arguments
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Show help if requested
if [ "$HELP" = true ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install AWS CLI v2 via AWS's official installer"
    echo ""
    echo "Options:"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Install AWS CLI v2"
    echo ""
    echo "Features:"
    echo "  - Uses AWS's official installer for latest version"
    echo "  - Supports x86_64 and aarch64 architectures"
    echo "  - Includes AWS Session Manager plugin"
    echo "  - Certificate-aware downloads for corporate networks"
    echo ""
    echo "Note: Only AWS CLI v2 is supported. AWS CLI v1 is in maintenance mode."
    exit 0
fi


# Function to install AWS CLI v2 via official installer
install_aws_cli_official() {
    echo "📦 Installing AWS CLI v2 via official installer..."
    
    # Determine architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            AWS_INSTALLER_URL="https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"
            ;;
        aarch64)
            AWS_INSTALLER_URL="https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip"
            ;;
        *)
            echo "❌ Error: Unsupported architecture: $ARCH"
            echo "   AWS CLI v2 official installer supports x86_64 and aarch64"
            exit 1
            ;;
    esac
    
    echo "🏗️  Architecture: $ARCH"
    echo "📥 Downloading AWS CLI v2 installer..."
    
    # Download and install
    curl ${CURL_FLAGS} "$AWS_INSTALLER_URL" -o "/tmp/awscliv2.zip"
    
    # Verify download
    if [ ! -f "/tmp/awscliv2.zip" ] || [ ! -s "/tmp/awscliv2.zip" ]; then
        echo "❌ Error: Failed to download AWS CLI installer"
        exit 1
    fi
    
    echo "📂 Extracting installer..."
    unzip -q /tmp/awscliv2.zip -d /tmp/
    
    echo "⚙️  Installing AWS CLI v2..."
    /tmp/aws/install
    
    # Clean up
    rm -rf /tmp/aws /tmp/awscliv2.zip
}





# Install AWS CLI using official installer
install_aws_cli_official

# Verify installation
echo "🔍 Verifying AWS CLI installation..."
if command -v aws >/dev/null 2>&1; then
    INSTALLED_VERSION=$(aws --version 2>&1)
    echo "✅ AWS CLI installed successfully"
    echo "   Version: $INSTALLED_VERSION"
    echo "   Location: $(which aws)"
    
    # Test basic functionality
    echo "🧪 Testing AWS CLI functionality..."
    if aws help >/dev/null 2>&1; then
        echo "✅ AWS CLI is working correctly"
    else
        echo "⚠️  AWS CLI verification had issues"
    fi
else
    echo "❌ Error: AWS CLI installation failed"
    echo "   Command 'aws' not found in PATH"
    exit 1
fi

# Install additional AWS tools if requested
echo "🛠️  Installing additional AWS development tools..."

# Install AWS Session Manager plugin (useful for EC2 access)
echo "🔌 Installing AWS Session Manager plugin..."
if curl ${CURL_FLAGS} "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "/tmp/session-manager-plugin.deb"; then
    dpkg -i /tmp/session-manager-plugin.deb 2>/dev/null || true
    rm -f /tmp/session-manager-plugin.deb
    
    if command -v session-manager-plugin >/dev/null 2>&1; then
        echo "✅ AWS Session Manager plugin installed"
    else
        echo "⚠️  AWS Session Manager plugin installation had issues"
    fi
else
    echo "⚠️  Could not download AWS Session Manager plugin"
fi

echo "🎉 AWS CLI installation complete!"
echo "💡 Usage examples:"
echo "   aws --version                 # Show AWS CLI version"
echo "   aws configure                 # Configure AWS credentials"
echo "   aws sts get-caller-identity   # Test credentials"
echo "   aws s3 ls                     # List S3 buckets"
echo "   aws ec2 describe-instances    # List EC2 instances"
echo ""
echo "🔗 Next steps:"
echo "   1. Configure credentials: aws configure"
echo "   2. Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
echo "   3. Or use IAM roles if running on AWS infrastructure"
echo ""
echo "📚 Useful resources:"
echo "   - AWS CLI Documentation: https://docs.aws.amazon.com/cli/"
echo "   - AWS CLI Command Reference: https://awscli.amazonaws.com/v2/documentation/api/latest/index.html"
echo "   - AWS Configuration: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html"