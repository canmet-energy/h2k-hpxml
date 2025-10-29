#!/bin/bash
set -e

# Install Ruby via rbenv for user (no sudo required)
echo "💎 Installing Ruby via rbenv for user $(whoami)..."

# Certificate environment now handled system-wide by certctl
# Get appropriate curl flags from environment (set by certctl if available)
CURL_FLAGS="${CURL_FLAGS:--fsSL}"

# Allow caller to specify Ruby version via DEVCONTAINER_RUBY_VERSION (preferred) or RUBY_VERSION.
# Fallback default remains 3.2.2 if neither provided.
RUBY_VERSION_INPUT="${DEVCONTAINER_RUBY_VERSION:-${RUBY_VERSION:-3.2.2}}"

# Basic semantic version validation (major.minor.patch) – tolerate a leading 'v'.
if [[ "$RUBY_VERSION_INPUT" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    RUBY_VERSION="${RUBY_VERSION_INPUT#v}" # strip leading v if present
else
    echo "❌ Invalid Ruby version format: '$RUBY_VERSION_INPUT' (expected MAJOR.MINOR.PATCH)" >&2
    exit 2
fi

if [ -n "${DEVCONTAINER_RUBY_VERSION:-}" ]; then
    _ruby_version_source="DEVCONTAINER_RUBY_VERSION"
elif [ -n "${RUBY_VERSION:-}" ]; then
    _ruby_version_source="RUBY_VERSION (env override)"
else
    _ruby_version_source="default (3.2.2)"
fi
echo "ℹ️ Using Ruby version ${RUBY_VERSION} (source: ${_ruby_version_source})"

# Set up installation directories in user's home
RBENV_ROOT="$HOME/.rbenv"
mkdir -p "$RBENV_ROOT"

# Check if rbenv is already installed
if [ -d "$RBENV_ROOT/.git" ]; then
    echo "ℹ️ rbenv already installed, updating..."
    cd "$RBENV_ROOT"
    git pull --quiet
else
    echo "📥 Installing rbenv..."
    git clone https://github.com/rbenv/rbenv.git "$RBENV_ROOT"
fi

# Install ruby-build plugin for rbenv
RUBY_BUILD_DIR="$RBENV_ROOT/plugins/ruby-build"
if [ -d "$RUBY_BUILD_DIR/.git" ]; then
    echo "ℹ️ ruby-build already installed, updating..."
    cd "$RUBY_BUILD_DIR"
    git pull --quiet
else
    echo "📥 Installing ruby-build plugin..."
    git clone https://github.com/rbenv/ruby-build.git "$RUBY_BUILD_DIR"
fi

# Optional: Install rbenv-update plugin for easier maintenance
RBENV_UPDATE_DIR="$RBENV_ROOT/plugins/rbenv-update"
if [ ! -d "$RBENV_UPDATE_DIR/.git" ]; then
    echo "📥 Installing rbenv-update plugin..."
    git clone https://github.com/rkh/rbenv-update.git "$RBENV_UPDATE_DIR"
fi

# Update PATH and initialize rbenv in shell configuration
echo "🔧 Configuring shell environment..."

# Function to add rbenv configuration to a file
add_rbenv_config() {
    local config_file="$1"
    if ! grep -q 'rbenv init' "$config_file" 2>/dev/null; then
        cat >> "$config_file" << 'EOF'

# rbenv initialization
export PATH="$HOME/.rbenv/bin:$PATH"
eval "$(rbenv init - bash)"
EOF
        echo "   Added rbenv config to $config_file"
    fi
}

# Add to both .bashrc and .profile
add_rbenv_config ~/.bashrc
add_rbenv_config ~/.profile

# Export for current session
export PATH="$RBENV_ROOT/bin:$PATH"
eval "$(rbenv init - bash)"

# Check if the requested Ruby version is already installed
if rbenv versions --bare | grep -q "^${RUBY_VERSION}$"; then
    echo "ℹ️ Ruby ${RUBY_VERSION} already installed"
else
    # Detect number of CPU cores for parallel compilation
    if command -v nproc &> /dev/null; then
        MAKE_JOBS=$(nproc)
    elif [ -f /proc/cpuinfo ]; then
        MAKE_JOBS=$(grep -c ^processor /proc/cpuinfo)
    else
        MAKE_JOBS=4  # Fallback to 4 cores
    fi

    echo "📦 Installing Ruby ${RUBY_VERSION}..."
    echo "   Compiling with ${MAKE_JOBS} parallel jobs..."
    echo "   This may take several minutes..."

    # Install required build dependencies info message
    echo "ℹ️ Ensure build dependencies are available (libssl-dev, libreadline-dev, etc.)"

    # Install Ruby with rbenv
    # Use --verbose for better feedback during long builds
    # Set MAKE_OPTS to enable parallel compilation
    if MAKE_OPTS="-j${MAKE_JOBS}" RUBY_CONFIGURE_OPTS="--disable-install-doc" rbenv install "$RUBY_VERSION" --verbose; then
        echo "✅ Ruby ${RUBY_VERSION} installed successfully"
    else
        echo "❌ Ruby installation failed. Check build dependencies." >&2
        echo "   Required packages: libssl-dev libreadline-dev zlib1g-dev" >&2
        echo "   libyaml-dev libffi-dev build-essential" >&2
        exit 1
    fi
fi

# Set the installed version as global default
echo "🔧 Setting Ruby ${RUBY_VERSION} as global default..."
rbenv global "$RUBY_VERSION"

# Rehash to update rbenv shims
rbenv rehash

# Verify installation
echo ""
echo "🔬 Verifying Ruby installation..."
if ruby --version; then
    echo "✅ Ruby installed and configured successfully!"
    echo ""
    echo "📊 Installation details:"
    echo "   Ruby version: $(ruby --version)"
    echo "   Gem version: $(gem --version)"
    echo "   rbenv root: $RBENV_ROOT"
    echo "   Ruby location: $(which ruby)"
    echo ""
    echo "💡 Useful rbenv commands:"
    echo "   rbenv versions          - List installed Ruby versions"
    echo "   rbenv install <version> - Install a Ruby version"
    echo "   rbenv global <version>  - Set global Ruby version"
    echo "   rbenv local <version>   - Set local Ruby version for current directory"
    echo "   rbenv update            - Update rbenv and plugins"
    echo ""
    echo "💎 Installing bundler gem..."
    gem install bundler --no-document
    rbenv rehash
    echo "   Bundler version: $(bundle --version)"
else
    echo "❌ Ruby verification failed" >&2
    exit 1
fi

# Create a basic Gemfile if it doesn't exist
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GEMFILE_PATH="$PROJECT_ROOT/Gemfile"

if [ ! -f "$GEMFILE_PATH" ]; then
    echo ""
    echo "📝 Creating basic Gemfile..."
    cat > "$GEMFILE_PATH" << 'EOF'
# frozen_string_literal: true

source "https://rubygems.org"

# Ruby version (should match DEVCONTAINER_RUBY_VERSION in devcontainer.json)
ruby "~> 3.2.0"

# Development and testing gems
group :development, :test do
  gem "rake", "~> 13.0"
  gem "rspec", "~> 3.12"
  gem "rubocop", "~> 1.50", require: false
  gem "rubocop-performance", "~> 1.17", require: false
  gem "rubocop-rspec", "~> 2.20", require: false
end

# Add your application gems here
# gem "rails", "~> 7.0"
# gem "sinatra", "~> 3.0"
EOF
    echo "✅ Created Gemfile at $GEMFILE_PATH"

    # Run bundle install
    echo ""
    echo "📦 Installing gems with bundler..."
    cd "$PROJECT_ROOT"
    if bundle install; then
        echo "✅ Gems installed successfully"
    else
        echo "⚠️ Bundle install failed, but Gemfile was created" >&2
    fi
else
    echo ""
    echo "ℹ️ Gemfile already exists at $GEMFILE_PATH"
    echo "   Run 'bundle install' to install gems"
fi

echo ""
echo "🎉 Ruby installation complete!"
