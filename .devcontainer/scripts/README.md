# DevContainer Installation Scripts

This directory contains modular installation scripts for the H2K-HPXML development container. These scripts make the Dockerfile cleaner, more maintainable, and allow for easier testing and reuse.

## Script Overview

### `install-dev-tools.sh`
Legacy helper (kept only if referenced elsewhere). Prefer invoking individual scripts directly. Certificate logic is fully unified under `certctl.sh`.

### `certctl.sh`
Unified certificate utility (strict-only) replaces all former certificate scripts. Only `certctl.sh` remains for certificate installation, probing, environment emission, banner, and MOTD snapshot logic. The old helper scripts have been removed.

Commands:
```
certctl install        # Install custom certs (idempotent)
certctl probe|status   # Live strict probe (all targets) --json/--quiet
certctl env            # Emit CERT_STATUS/CURL_FLAGS lines (use with eval)
certctl refresh        # Probe + update banner (and MOTD if root)
certctl motd           # Update MOTD (root) or banner (user)
certctl banner         # Refresh banner and print it
certctl write-motd     # Internal: write snapshot only (root)
```

Strict only: any failure => INSECURE. Targets:
```
https://pypi.org/
https://registry.npmjs.org/
https://github.com/
https://cli.github.com/
https://download.docker.com/
https://nodejs.org/
https://awscli.amazonaws.com/
https://s3.amazonaws.com/
```

Exit codes:
```
0  SECURE / SECURE_CUSTOM
10 INSECURE
20 UNKNOWN
30 install error (certificate store)
```

### Individual Installation Scripts

#### `install-uv.sh`
Installs UV Python package manager:
- Downloads from GitHub releases
- Installs to `/usr/local/bin/uv`
- Respects `CURL_FLAGS` for certificate handling

#### `install-github-cli.sh` 
Installs GitHub CLI:
- Adds GitHub CLI apt repository
- Installs via apt package manager
- Respects `CURL_FLAGS` for repository key download

#### `install-docker-cli.sh`
Installs Docker CLI and Compose plugin:
- Adds Docker apt repository  
- Installs docker-ce-cli and docker-compose-plugin
- Sets up docker group for vscode user
- Respects `CURL_FLAGS` for repository key download

#### `install-nodejs.sh`
Installs Node.js for development tooling:
- Downloads Node.js binary distribution
- Installs to `/usr/local/`
- Creates symlinks in `/usr/bin/`
- Configures npm for potentially insecure environments
- Respects `CURL_FLAGS` for download

#### `install-python.sh`
Installs Python with version management:
- Uses UV for Python version management (requires `install-uv.sh`)
- Supports Python versions 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 (default: 3.11)
- Command-line options: `--version`, `--help`
- Verifies installation and tests basic functionality
- Certificate-aware downloads using `CURL_FLAGS`

#### `install-ruby.sh`
Installs Ruby with flexible installation methods:
- System method: Via apt package manager (fast, limited versions)
- rbenv method: Via rbenv (flexible versions, slower compilation)
- Supports Ruby versions (system packages available for 3.0, 3.1, 3.2)
- Command-line options: `--version`, `--method`, `--help`
- Installs bundler and verifies installation
- Certificate-aware downloads using `CURL_FLAGS`

#### `install-csharp.sh`
Installs .NET SDK and C# development tools:
- Apt method: Via Microsoft's official apt repository (recommended)
- Manual method: Via Microsoft's install script (more versions available)
- Supports .NET versions 6.0 (LTS), 7.0, 8.0 (LTS), 9.0 (default: 8.0)
- Command-line options: `--version`, `--method`, `--help`
- Installs global tools (dotnet-ef, dotnet-format) for development
- Certificate-aware downloads using `CURL_FLAGS`

#### `install-aws-cli.sh`
Installs AWS CLI v2 via AWS's official installer:
- Uses AWS's official installer for latest version and best compatibility
- Supports x86_64 and aarch64 architectures automatically
- Only supports AWS CLI v2 (v1 is in maintenance mode)
- Command-line options: `--help`
- Includes AWS Session Manager plugin for EC2 access
- Certificate-aware downloads using `CURL_FLAGS`

#### Custom certificate installation
Handled by `certctl install` (old `install-certificates.sh` deleted).

#### `install-claude-cli.sh`
Installs Claude CLI (Anthropic's command-line interface):
- Requires Node.js and npm (installed via `install-nodejs.sh`)
- Installs globally via npm: `@anthropic-ai/claude-cli`
- Provides comprehensive error handling and diagnostics
- Tests npm registry connectivity if installation fails
- Includes usage instructions and documentation links

## Benefits of Modular Approach

1. **Maintainability**: Each tool installation is isolated and easier to update
2. **Testing**: Individual scripts can be tested separately
3. **Reusability**: Scripts can be used outside of Docker context
4. **Debugging**: Easier to identify issues with specific installations
5. **Clean Dockerfile**: Main Dockerfile remains focused on structure, not implementation details
6. **Version Management**: Tool versions are centralized in individual scripts

## Usage in Dockerfile

```dockerfile
# Install custom certificates (optional)
COPY .devcontainer/certs* /tmp/certs/
COPY .devcontainer/scripts/certctl.sh /tmp/certctl.sh
RUN chmod +x /tmp/certctl.sh && /tmp/certctl.sh install && rm -f /tmp/certctl.sh

# Copy scripts and install tools (certctl supplies CURL_FLAGS & MOTD snapshot)
COPY .devcontainer/scripts/ /tmp/install-scripts/
RUN chmod +x /tmp/install-scripts/*.sh && \
  cp /tmp/install-scripts/certctl.sh /usr/local/bin/certctl && chmod +x /usr/local/bin/certctl && \
  eval "$(certctl env --quiet)" || true && \
  certctl motd --quiet || true && \
  /tmp/install-scripts/install-uv.sh && \
  /tmp/install-scripts/install-github-cli.sh && \
  /tmp/install-scripts/install-docker-cli.sh && \
  /tmp/install-scripts/install-nodejs.sh && \
  /tmp/install-scripts/install-python.sh && \
  /tmp/install-scripts/install-ruby.sh && \
  # Optional: /tmp/install-scripts/install-claude-cli.sh && \
  rm -rf /var/lib/apt/lists/* /tmp/install-scripts
```

### Build Arguments for Version Control

The Dockerfile supports build arguments to customize Python and Ruby versions:

```dockerfile
# Build arguments with defaults
ARG PYTHON_VERSION=3.11
ARG RUBY_VERSION=3.2
ARG RUBY_METHOD=system

# Usage in installation scripts
/tmp/install-scripts/install-python.sh --version ${PYTHON_VERSION} && \
/tmp/install-scripts/install-ruby.sh --version ${RUBY_VERSION} --method ${RUBY_METHOD} && \
```

**Build with custom versions:**
```bash
# Docker build with custom versions
docker build --build-arg PYTHON_VERSION=3.12 \
             --build-arg RUBY_VERSION=3.1 \
             --build-arg RUBY_METHOD=rbenv \
             -t h2k-hpxml .

# Docker Compose with build args
docker-compose build --build-arg PYTHON_VERSION=3.12
```

**VS Code Dev Container:**
Update `.devcontainer/devcontainer.json`:
```json
{
  "build": {
    "dockerfile": "./Dockerfile",
    "context": "..",
    "args": {
      "PYTHON_VERSION": "3.12",
      "RUBY_VERSION": "3.1",
      "RUBY_METHOD": "rbenv"
    }
  }
}
```

### Alternative: Using Master Script

For simpler usage, you can use the master script:

```dockerfile
COPY .devcontainer/scripts/ /tmp/install-scripts/
RUN chmod +x /tmp/install-scripts/*.sh && \
    /tmp/install-scripts/install-dev-tools.sh && \
    rm -rf /tmp/install-scripts
```

## Corporate Network Support

Place `.crt` or `.pem` files in `.devcontainer/certs/` before build/rebuild. Installed via `certctl install` into system trust store.

Runtime behavior:
- `certctl probe` tests live connectivity (strict only)
- `certctl motd` updates system snapshot (root) or user banner
- `certctl banner` prints latest live banner
- `certctl env` supplies `CERT_STATUS` and `CURL_FLAGS`
- Divergence reported in `certctl probe --json` when snapshot differs

Statuses returned by probe:
- `SECURE` – All targets succeeded with base store.
- `SECURE_CUSTOM` – All targets succeeded and custom cert(s) detected.
- `INSECURE` – One or more targets failed under current condition.

JSON output (`certctl probe --json`) example:
```json
{
  "status": "INSECURE",
  "curl_flags": "-fsSLk",
  "custom_certs": false,
  "snapshot_status": "SECURE",
  "divergent": true,
  "timestamp": 1700000000,
  "success": 6,
  "fail": 2,
  "total": 8
}
```

Lenient mode removed: strict-only (all targets must succeed).

## Standalone Usage

Individual scripts can be run independently outside of Docker:

```bash
# Install Claude CLI after Node.js is available
export CURL_FLAGS="-fsSL"  # or "-fsSLk" for insecure
.devcontainer/scripts/install-claude-cli.sh
```

**Prerequisites for Claude CLI:**
- Node.js must be installed first (`install-nodejs.sh`)
- npm registry must be accessible
- Sufficient permissions for global npm installation

## Version Selection Examples

The new Python and Ruby installation scripts support version selection:

### Python Installation Examples
```bash
# Install default Python (3.11)
./install-python.sh

# Install specific Python version
./install-python.sh --version 3.12

# Show help and available versions
./install-python.sh --help
```

### Ruby Installation Examples
```bash
# Install default Ruby via system packages (3.2)
./install-ruby.sh

# Install specific Ruby version via system packages
./install-ruby.sh --version 3.1

# Install Ruby via rbenv for maximum version flexibility
./install-ruby.sh --version 3.2 --method rbenv

# Show help and available options
./install-ruby.sh --help
```

### C# Installation Examples
```bash
# Install default .NET (8.0 LTS) via apt
./install-csharp.sh

# Install specific .NET version via apt
./install-csharp.sh --version 6.0

# Install .NET via Microsoft's install script
./install-csharp.sh --version 8.0 --method manual

# Show help and available options
./install-csharp.sh --help
```

### AWS CLI Installation Examples
```bash
# Install AWS CLI v2 (simple, no options needed)
./install-aws-cli.sh

# Show help and information
./install-aws-cli.sh --help
```

## Updating Tool Versions

To update tool versions, modify the version variables in the individual scripts:
- UV: Edit `UV_VERSION` in `install-uv.sh`
- Node.js: Edit `NODE_VERSION` in `install-nodejs.sh`
- Python: Use `--version` argument (supported: 3.8-3.13)
- Ruby: Use `--version` argument (system packages: 3.0-3.2, rbenv: any available)
- C#/.NET: Use `--version` argument (supported: 6.0, 7.0, 8.0, 9.0)
- AWS CLI: Only v2 supported (v1 is deprecated)
- Claude CLI: Uses latest from npm registry (`@anthropic-ai/claude-cli`)
- GitHub CLI and Docker CLI use latest from their respective repositories