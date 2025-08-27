# H2K-HPXML Docker Container

This project provides unified Docker containers for both development and production environments using multi-stage builds.

## Quick Start

### Production Environment
```bash
# Build production container (default target)
docker build -t canmet/h2k-hpxml .

# Convert an H2K file
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# Interactive production shell
docker run -it canmet/h2k-hpxml bash
```

### Development Environment
```bash
# Build development container
docker build --target development -t canmet/h2k-hpxml:dev .

# Interactive development shell with dev tools
docker run -it -v $(pwd):/workspaces/h2k_hpxml -v /var/run/docker.sock:/var/run/docker.sock canmet/h2k-hpxml:dev

# Using Docker Compose (recommended)
docker-compose --profile dev run --rm h2k-hpxml-dev
```

## Build Targets

The Dockerfile supports two build targets:

| Target | Purpose | Base Image | Additional Tools |
|--------|---------|------------|------------------|
| **Production** (default) | Deployment | Ubuntu 22.04 | h2k-hpxml, OpenStudio, Python |
| **Development** | Development | Ubuntu 22.04 | All production tools + Docker CLI, Node.js, Git, sudo |

## Container Status

✅ **Working Components (Both Targets):**
- OpenStudio 3.9.0 installed at `/usr/local/bin/openstudio`
- OpenStudio-HPXML v1.9.1 installed at `/opt/OpenStudio-HPXML`
- Python 3.12 with h2k-hpxml package
- All CLI tools (h2k2hpxml, h2k-resilience, h2k-deps)
- Environment variables properly configured

✅ **Additional Development Tools:**
- Docker CLI for Docker-in-Docker
- Node.js 18 for frontend development
- Git for version control
- sudo access for system modifications

⚠️ **Known Issues:**
- Volume permissions may require adjustment on some systems
- Output includes entrypoint logging messages

## Docker Compose Usage

The recommended way to use the containers:

### Production Usage
```bash
# Interactive production shell
docker-compose run --rm h2k-hpxml

# Convert single file
docker-compose run --rm h2k-hpxml h2k2hpxml /data/examples/WizardHouse.h2k

# Batch processing
docker-compose --profile batch run --rm batch-convert
```

### Development Usage
```bash
# Interactive development shell with all dev tools
docker-compose --profile dev run --rm h2k-hpxml-dev

# Start development container in background
docker-compose --profile dev up -d h2k-hpxml-dev

# Access running development container
docker-compose exec h2k-hpxml-dev bash
```

## Testing the Container

Run the comprehensive test suite for both targets:

```bash
# Test production build
./docker/test_container.sh canmet/h2k-hpxml skip-build

# Test development build  
./docker/test_container.sh canmet/h2k-hpxml:dev skip-build

# Test specific image
./docker/test_container.sh my-custom-image:tag
```

## Verifying Installation

### Quick Health Check

**Production Container:**
```bash
# Check OpenStudio
docker run --rm canmet/h2k-hpxml bash -c "openstudio --version"

# Check OpenStudio-HPXML
docker run --rm canmet/h2k-hpxml bash -c "ls -la /opt/OpenStudio-HPXML"

# Check h2k-hpxml package
docker run --rm canmet/h2k-hpxml bash -c "pip list | grep h2k-hpxml"
```

**Development Container:**
```bash
# Check additional dev tools
docker run --rm canmet/h2k-hpxml:dev bash -c "docker --version && node --version && git --version"

# Check sudo access
docker run --rm canmet/h2k-hpxml:dev bash -c "sudo whoami"
```

### Test Conversion
```bash
# Using example files from the repository
docker run --rm -v $(pwd)/examples:/data canmet/h2k-hpxml \
  h2k2hpxml /data/WizardHouse.h2k --output /data/output.xml

# Check the output
ls -la examples/output.xml
```

## Custom Builds

The Dockerfile supports build arguments for customization:

```bash
# Custom OpenStudio version
docker build \
  --build-arg OPENSTUDIO_VERSION=3.8.0 \
  --build-arg OPENSTUDIO_SHA=<sha> \
  -t canmet/h2k-hpxml:custom .

# Custom Ubuntu base
docker build \
  --build-arg UBUNTU_VERSION=24.04 \
  -t canmet/h2k-hpxml:ubuntu24 .
```

See [BUILD_ARGS.md](BUILD_ARGS.md) for all available options.

## Volume Mounting

The container expects data at `/data`:

```bash
# Basic usage
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/file.h2k

# Separate input/output directories
docker run --rm \
  -v /path/to/input:/input:ro \
  -v /path/to/output:/output \
  canmet/h2k-hpxml h2k2hpxml /input/file.h2k --output /output/result.xml
```

## Configuration

The container creates a configuration file at `/data/.h2k-config/conversionconfig.ini` on first run. This file persists when mounting volumes and contains:
- OpenStudio paths
- Output directories
- Simulation settings

## Troubleshooting

### Permission Issues
If you encounter permission errors:
```bash
# Run as current user
docker run --rm --user $(id -u):$(id -g) -v $(pwd):/data canmet/h2k-hpxml ...

# Or adjust directory permissions
chmod 777 output_directory
```

### Missing Dependencies
The container includes all required dependencies. If something is missing:
```bash
# Check dependency status
docker run --rm canmet/h2k-hpxml h2k-deps --check-only

# Interactive troubleshooting
docker run -it --entrypoint /bin/bash canmet/h2k-hpxml
```

### Debug Mode
```bash
# Run with debug output
docker run --rm -v $(pwd):/data \
  -e H2K_LOG_LEVEL=DEBUG \
  canmet/h2k-hpxml h2k2hpxml /data/file.h2k
```

## Container Details

### Production Container
- **Base Image**: Ubuntu 22.04
- **Python Version**: 3.12
- **OpenStudio**: 3.9.0
- **OpenStudio-HPXML**: v1.9.1
- **Size**: ~870MB
- **User**: h2kuser (UID 1000)
- **Entrypoint**: `/usr/local/bin/entrypoint.sh`

### Development Container
- **Base Image**: Ubuntu 22.04
- **Python Version**: 3.12
- **OpenStudio**: 3.9.0
- **OpenStudio-HPXML**: v1.9.1
- **Size**: ~1.2GB (includes dev tools)
- **User**: vscode (UID 1000) with sudo access
- **Additional Tools**: Docker CLI, Node.js 18, Git, uv
- **Default CMD**: `/bin/bash`

## DevContainer Integration

The development container integrates seamlessly with VS Code DevContainers:

1. **Automatic Setup**: Uses development target from main Dockerfile
2. **Volume Mounting**: Project files mounted at `/workspaces/h2k_hpxml`
3. **Docker-in-Docker**: Docker socket mounted for container builds
4. **Port Forwarding**: Ports 3000, 8000, 8080 forwarded
5. **Extensions**: Python, Docker, CSV tools pre-installed

