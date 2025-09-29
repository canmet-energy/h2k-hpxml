#!/bin/bash
set -e

echo "💎 Installing Ruby via rbenv..."

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Parse command line arguments
RUBY_VERSION="3.2.2"  # Default version (latest stable)
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version|-v)
            RUBY_VERSION="$2"
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
    echo "Install Ruby via rbenv with version management"
    echo ""
    echo "Options:"
    echo "  -v, --version VERSION   Ruby version to install (default: 3.2)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Install Ruby 3.2 via rbenv"
    echo "  $0 --version 3.1          # Install Ruby 3.1 via rbenv"
    echo "  $0 --version 3.3          # Install Ruby 3.3 via rbenv"
    exit 0
fi


echo "🔧 Installing Ruby $RUBY_VERSION via rbenv..."

# Install rbenv dependencies
apt-get update
apt-get install -y git curl libssl-dev libreadline-dev zlib1g-dev \
    autoconf bison build-essential libyaml-dev libreadline-dev \
    libncurses5-dev libffi-dev libgdbm-dev

# Determine target user (default to vscode, but can be overridden)
TARGET_USER="${RBENV_USER:-vscode}"
TARGET_HOME="/home/${TARGET_USER}"

# Ensure the target user exists
if ! id "$TARGET_USER" &>/dev/null; then
    echo "❌ Error: User '$TARGET_USER' does not exist"
    exit 1
fi

# Install rbenv as the target user to avoid ownership issues
echo "📥 Installing rbenv for user: $TARGET_USER"

# Function to run commands as the target user
run_as_user() {
    if [ "$USER" = "$TARGET_USER" ]; then
        # Already running as target user
        "$@"
    else
        # Run as target user
        sudo -u "$TARGET_USER" "$@"
    fi
}

# Install rbenv
if [ ! -d "$TARGET_HOME/.rbenv" ]; then
    echo "📥 Installing rbenv..."
    run_as_user git clone https://github.com/rbenv/rbenv.git "$TARGET_HOME/.rbenv"
    run_as_user git clone https://github.com/rbenv/ruby-build.git "$TARGET_HOME/.rbenv/plugins/ruby-build"
    
    # Set up rbenv in PATH
    echo 'export PATH="$HOME/.rbenv/bin:$PATH"' >> "$TARGET_HOME/.bashrc"
    echo 'eval "$(rbenv init -)"' >> "$TARGET_HOME/.bashrc"
    
    # Ensure proper ownership
    chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.rbenv"
    chown "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.bashrc"
else
    echo "✅ rbenv already installed"
fi

# Install Ruby as the target user
echo "⏳ Installing Ruby $RUBY_VERSION (this may take several minutes)..."
run_as_user bash -c "
    export PATH=\"$TARGET_HOME/.rbenv/bin:\$PATH\"
    eval \"\$(rbenv init -)\"
    rbenv install \"$RUBY_VERSION\"
    rbenv global \"$RUBY_VERSION\"
    rbenv rehash
"

# Install bundler as the target user
echo "📦 Installing bundler..."
run_as_user bash -c "
    export PATH=\"$TARGET_HOME/.rbenv/bin:\$PATH\"
    eval \"\$(rbenv init -)\"
    gem install bundler --no-document
    rbenv rehash
"

# Verify installation as the target user
echo "🔍 Verifying Ruby installation..."
VERIFICATION_RESULT=$(run_as_user bash -c "
    export PATH=\"$TARGET_HOME/.rbenv/bin:\$PATH\"
    eval \"\$(rbenv init -)\"
    
    if command -v ruby >/dev/null 2>&1; then
        echo \"Ruby: \$(ruby --version)\"
        
        if command -v gem >/dev/null 2>&1; then
            echo \"RubyGems: \$(gem --version)\"
            
            if command -v bundle >/dev/null 2>&1; then
                echo \"Bundler: \$(bundle --version)\"
                echo \"SUCCESS\"
            else
                echo \"Bundler: NOT FOUND\"
                echo \"PARTIAL\"
            fi
        else
            echo \"RubyGems: NOT FOUND\"
            echo \"FAILED\"
        fi
    else
        echo \"Ruby: NOT FOUND\"
        echo \"FAILED\"
    fi
")

echo "$VERIFICATION_RESULT"

if echo "$VERIFICATION_RESULT" | grep -q "SUCCESS\|PARTIAL"; then
    echo "✅ Ruby installation completed successfully!"
    echo ""
    echo "🔧 To use Ruby in your shell, run:"
    echo "   source ~/.bashrc"
    echo "   # or start a new shell session"
else
    echo "❌ Error: Ruby installation verification failed"
    exit 1
fi

echo "🎉 Ruby installation complete!"
echo "💡 Usage examples:"
echo "   ruby --version              # Show current Ruby version"
echo "   rbenv versions              # List installed Ruby versions"
echo "   rbenv global <version>      # Set global Ruby version"
echo "   rbenv local <version>       # Set local Ruby version for project"
echo "   gem install <package>       # Install a gem"
echo "   bundle install              # Install project dependencies"