# H2K-HPXML Docker Container

## Quick Start

```bash
# Build the container
docker build -t canmet/h2k-hpxml .

# Convert an H2K file
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# Run with bash for debugging
docker run -it --entrypoint /bin/bash canmet/h2k-hpxml
```

## Container Status

✅ **Working Components:**
- OpenStudio 3.9.0 installed at `/usr/local/bin/openstudio`
- OpenStudio-HPXML v1.9.1 installed at `/opt/OpenStudio-HPXML`
- Python 3.12 with h2k-hpxml package
- All CLI tools (h2k2hpxml, h2k-resilience, h2k-deps)
- Environment variables properly configured

⚠️ **Known Issues:**
- Volume permissions may require adjustment on some systems
- Output includes entrypoint logging messages

## Testing the Container

Run the comprehensive test suite:

```bash
# From project root directory
./docker/test_container.sh

# Skip build if image already exists
./docker/test_container.sh canmet/h2k-hpxml skip-build

# Test a specific image
./docker/test_container.sh my-custom-image:tag
```

## Verifying Installation

### Quick Health Check
```bash
# Check OpenStudio
docker run --rm --entrypoint /bin/bash canmet/h2k-hpxml -c "openstudio --version"

# Check OpenStudio-HPXML
docker run --rm --entrypoint /bin/bash canmet/h2k-hpxml -c "ls -la /opt/OpenStudio-HPXML"

# Check h2k-hpxml package
docker run --rm --entrypoint /bin/bash canmet/h2k-hpxml -c "pip list | grep h2k-hpxml"
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

- **Base Image**: Ubuntu 22.04
- **Python Version**: 3.12
- **OpenStudio**: 3.9.0
- **OpenStudio-HPXML**: v1.9.1
- **Size**: ~870MB
- **User**: h2kuser (UID 1000)