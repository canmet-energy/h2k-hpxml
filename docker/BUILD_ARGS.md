# Docker Build Arguments

The H2K-HPXML Dockerfile supports the following build arguments to customize versions:

## Available Build Arguments

| Argument | Default Value | Description |
|----------|--------------|-------------|
| `UBUNTU_VERSION` | `22.04` | Ubuntu base image version |
| `PYTHON_VERSION` | `3.12` | Python version to install |
| `OPENSTUDIO_VERSION` | `3.9.0` | OpenStudio version |
| `OPENSTUDIO_SHA` | `c77fbb9569` | OpenStudio build SHA/commit hash |
| `OPENSTUDIO_HPXML_VERSION` | `v1.9.1` | OpenStudio-HPXML version tag |

## Usage Examples

### Default build (uses all default values):
```bash
docker build -t canmet/h2k-hpxml .
```

### Custom OpenStudio version:
```bash
docker build \
  --build-arg OPENSTUDIO_VERSION=3.8.0 \
  --build-arg OPENSTUDIO_SHA=abc123def \
  -t canmet/h2k-hpxml:os-3.8.0 .
```

### Custom Python version:
```bash
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t canmet/h2k-hpxml:py-3.11 .
```

### Custom OpenStudio-HPXML version:
```bash
docker build \
  --build-arg OPENSTUDIO_HPXML_VERSION=v1.8.1 \
  -t canmet/h2k-hpxml:hpxml-1.8.1 .
```

### Different Ubuntu version:
```bash
docker build \
  --build-arg UBUNTU_VERSION=24.04 \
  --build-arg OPENSTUDIO_SHA=<sha-for-24.04> \
  -t canmet/h2k-hpxml:ubuntu-24.04 .
```

### Complete custom build:
```bash
docker build \
  --build-arg UBUNTU_VERSION=22.04 \
  --build-arg PYTHON_VERSION=3.11 \
  --build-arg OPENSTUDIO_VERSION=3.8.0 \
  --build-arg OPENSTUDIO_SHA=xyz789 \
  --build-arg OPENSTUDIO_HPXML_VERSION=v1.8.0 \
  -t canmet/h2k-hpxml:custom .
```

## Finding Version Information

### OpenStudio Versions
Check available versions and their SHA values at:
https://github.com/NREL/OpenStudio/releases

The SHA is part of the .deb filename, e.g.:
- `OpenStudio-3.9.0+c77fbb9569-Ubuntu-22.04-x86_64.deb`
  - Version: `3.9.0`
  - SHA: `c77fbb9569`

### OpenStudio-HPXML Versions
Check available versions at:
https://github.com/NREL/OpenStudio-HPXML/releases

### Ubuntu Compatibility
Ensure the Ubuntu version you choose has a corresponding OpenStudio package available. Check the OpenStudio release page for supported Ubuntu versions.

## Build-time vs Run-time Configuration

These arguments configure what gets installed in the Docker image at build time. For run-time configuration (paths, settings, etc.), use:
- Environment variables
- The `conversionconfig.ini` file
- Command-line arguments