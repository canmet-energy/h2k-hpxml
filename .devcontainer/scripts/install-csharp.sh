#!/bin/bash
set -e

echo "🔷 Installing .NET and C# support..."

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Parse command line arguments
DOTNET_VERSION="8.0"  # Default version (LTS)
HELP=false
INSTALL_METHOD="apt"  # apt or manual

while [[ $# -gt 0 ]]; do
    case $1 in
        --version|-v)
            DOTNET_VERSION="$2"
            shift 2
            ;;
        --method|-m)
            INSTALL_METHOD="$2"
            shift 2
            ;;
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
    echo "Install .NET SDK and C# development tools with version management"
    echo ""
    echo "Options:"
    echo "  -v, --version VERSION   .NET version to install (default: 8.0)"
    echo "  -m, --method METHOD     Installation method: apt, manual (default: apt)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Install .NET 8.0 via apt"
    echo "  $0 --version 6.0            # Install .NET 6.0 via apt"
    echo "  $0 --version 8.0 --method manual  # Install .NET 8.0 via Microsoft installer"
    echo ""
    echo "Installation Methods:"
    echo "  apt      - Install via Microsoft's apt repository (recommended)"
    echo "  manual   - Install via Microsoft's install script (more versions)"
    echo ""
    echo "Supported Versions:"
    echo "  6.0      - .NET 6 LTS (Long Term Support)"
    echo "  7.0      - .NET 7 (Standard Term Support)"
    echo "  8.0      - .NET 8 LTS (Long Term Support) - Default"
    echo "  9.0      - .NET 9 (Preview/Latest)"
    exit 0
fi

# Use certificate-aware curl flags if available
CURL_FLAGS="${CURL_FLAGS:-"-fsSL"}"

# Function to install .NET via apt repository
install_dotnet_apt() {
    echo "📦 Installing .NET $DOTNET_VERSION via Microsoft apt repository..."
    
    # Get Ubuntu version for repository selection
    UBUNTU_VERSION=$(lsb_release -rs)
    echo "📋 Detected Ubuntu $UBUNTU_VERSION"
    
    # Add Microsoft package repository
    echo "🔑 Adding Microsoft package signing key..."
    wget https://packages.microsoft.com/config/ubuntu/$UBUNTU_VERSION/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
    dpkg -i packages-microsoft-prod.deb
    rm packages-microsoft-prod.deb
    
    # Update package list
    apt-get update
    
    # Install .NET SDK
    echo "⏳ Installing .NET $DOTNET_VERSION SDK..."
    case "$DOTNET_VERSION" in
        "6.0")
            apt-get install -y dotnet-sdk-6.0
            ;;
        "7.0")
            apt-get install -y dotnet-sdk-7.0
            ;;
        "8.0")
            apt-get install -y dotnet-sdk-8.0
            ;;
        "9.0")
            # Try .NET 9, fall back to latest available
            if apt-cache show dotnet-sdk-9.0 >/dev/null 2>&1; then
                apt-get install -y dotnet-sdk-9.0
            else
                echo "⚠️  .NET 9.0 not available, installing latest available SDK"
                apt-get install -y dotnet-sdk-8.0
            fi
            ;;
        *)
            echo "⚠️  Installing latest available .NET SDK (version $DOTNET_VERSION not specifically supported)"
            apt-get install -y dotnet-sdk-8.0
            ;;
    esac
}

# Function to install .NET via Microsoft install script
install_dotnet_manual() {
    echo "🔧 Installing .NET $DOTNET_VERSION via Microsoft install script..."
    
    # Download and run Microsoft's install script
    echo "📥 Downloading Microsoft .NET install script..."
    curl ${CURL_FLAGS} https://dot.net/v1/dotnet-install.sh | bash -s -- --version $DOTNET_VERSION --install-dir /usr/local/dotnet
    
    # Add to PATH
    echo "🔗 Adding .NET to system PATH..."
    echo 'export DOTNET_ROOT=/usr/local/dotnet' >> /etc/environment
    echo 'export PATH=$PATH:/usr/local/dotnet' >> /etc/environment
    
    # Make available in current session
    export DOTNET_ROOT=/usr/local/dotnet
    export PATH=$PATH:/usr/local/dotnet
    
    # Create symlinks for system-wide access
    ln -sf /usr/local/dotnet/dotnet /usr/local/bin/dotnet
}

# Validate installation method
case "$INSTALL_METHOD" in
    "apt")
        install_dotnet_apt
        ;;
    "manual")
        install_dotnet_manual
        ;;
    *)
        echo "❌ Error: Unsupported installation method: $INSTALL_METHOD"
        echo "   Supported methods: apt, manual"
        exit 1
        ;;
esac

# Verify installation
echo "🔍 Verifying .NET installation..."
if command -v dotnet >/dev/null 2>&1; then
    INSTALLED_VERSION=$(dotnet --version)
    INSTALLED_INFO=$(dotnet --info 2>/dev/null | head -10)
    echo "✅ .NET installed successfully"
    echo "   Version: $INSTALLED_VERSION"
    echo "   Info: $INSTALLED_INFO"
    
    # Test basic functionality
    echo "🧪 Testing .NET functionality..."
    if dotnet --list-sdks >/dev/null 2>&1; then
        echo "✅ .NET SDK is working correctly"
        echo "   Available SDKs:"
        dotnet --list-sdks | sed 's/^/     /'
    else
        echo "⚠️  .NET SDK verification had issues"
    fi
else
    echo "❌ Error: .NET installation failed"
    exit 1
fi

# Install additional development tools
echo "🛠️  Installing additional C# development tools..."

# Install C# dev tools that work well in VS Code
echo "📦 Installing essential C# packages..."

# Try to install some useful global tools
if command -v dotnet >/dev/null 2>&1; then
    echo "🔧 Installing .NET global tools..."
    
    # Install Entity Framework tools (commonly used)
    dotnet tool install --global dotnet-ef 2>/dev/null || echo "   ⚠️  Could not install dotnet-ef (might already exist)"
    
    # Install code formatting tool
    dotnet tool install --global dotnet-format 2>/dev/null || echo "   ⚠️  Could not install dotnet-format (might already exist)"
    
    echo "✅ Global tools installation completed"
fi

echo "🎉 .NET and C# installation complete!"
echo "💡 Usage examples:"
echo "   dotnet --version              # Show .NET version"
echo "   dotnet new console -n MyApp   # Create new console application"
echo "   dotnet build                  # Build current project"
echo "   dotnet run                    # Run current project"
echo "   dotnet test                   # Run tests"
echo "   dotnet add package <name>     # Add NuGet package"
echo ""
echo "🔗 Useful resources:"
echo "   - .NET Documentation: https://docs.microsoft.com/dotnet/"
echo "   - C# Documentation: https://docs.microsoft.com/dotnet/csharp/"
echo "   - VS Code C# Extension: ms-dotnettools.csharp"