#!/bin/bash
set -e

echo "🐍 Installing Python via uv..."

# Parse command line arguments
PYTHON_VERSION="3.12"  # Default version
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version|-v)
            PYTHON_VERSION="$2"
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
    echo "Install Python using uv with version management"
    echo ""
    echo "Options:"
    echo "  -v, --version VERSION   Python version to install (default: 3.12)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Install Python 3.12 (default)"
    echo "  $0 --version 3.11      # Install Python 3.11"
    echo "  $0 --version 3.13      # Install Python 3.13"
    echo ""
    echo "Supported versions: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13"
    exit 0
fi

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ Error: uv is not installed"
    echo "   Please install uv first using install-uv.sh"
    exit 1
fi

# Validate Python version format
if ! echo "$PYTHON_VERSION" | grep -qE '^3\.(8|9|10|11|12|13)$'; then
    echo "❌ Error: Unsupported Python version: $PYTHON_VERSION"
    echo "   Supported versions: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13"
    exit 1
fi

echo "📋 Installing Python $PYTHON_VERSION using uv..."

# Use certificate-aware curl flags if available
CURL_FLAGS="${CURL_FLAGS:-"-fsSL"}"

# Install the specified Python version using uv
if uv python install "$PYTHON_VERSION"; then
    echo "✅ Python $PYTHON_VERSION installed successfully"
    
    # Verify installation
    echo "🔍 Verifying Python installation..."
    if uv python list | grep -q "$PYTHON_VERSION"; then
        INSTALLED_VERSION=$(uv python list | grep "$PYTHON_VERSION" | head -n1 | awk '{print $1}')
        echo "✅ Python $INSTALLED_VERSION is available via uv"
        
        # Test Python execution
        if uv python pin "$PYTHON_VERSION" 2>/dev/null && uv run python --version; then
            echo "✅ Python $PYTHON_VERSION is working correctly"
        else
            echo "⚠️  Python installed but version test failed"
        fi
    else
        echo "⚠️  Python installation may have issues"
        echo "📋 Available Python versions:"
        uv python list
    fi
else
    echo "❌ Error: Failed to install Python $PYTHON_VERSION"
    echo "🔍 Diagnostic information:"
    echo "   uv version: $(uv --version)"
    echo "   Available Python versions:"
    uv python list
    exit 1
fi

echo "🎉 Python installation via uv complete!"
echo "💡 Usage examples:"
echo "   uv run python --version          # Run Python directly"
echo "   uv python pin $PYTHON_VERSION    # Pin this version for project"
echo "   uv venv --python $PYTHON_VERSION # Create venv with this version"