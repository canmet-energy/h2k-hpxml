# Docker Guide for H2K-HPXML

The easiest way to use h2k-hpxml without installing Python, OpenStudio, or other dependencies is through Docker. This approach works identically on Windows, Mac, and Linux with zero configuration required.

> 🍎 **macOS Users**: Docker is the **recommended** method for macOS since automatic dependency installation is not currently supported on macOS.

## Why Use Docker?

- ✅ **Zero Setup**: No Python, OpenStudio, or dependency installation required
- ✅ **Universal**: Works identically on Windows, Mac, and Linux
- ✅ **macOS Compatible**: Only method currently supported for automatic setup on macOS
- ✅ **Consistent**: Same environment and results every time
- ✅ **Isolated**: No conflicts with existing software
- ✅ **Version-Controlled**: Reproducible builds with specific tool versions
- ✅ **CI/CD Ready**: Easy integration into automated workflows

## Quick Start with Docker

### Prerequisites

#### 1. Install Docker Desktop

**Windows:**
1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Run installer as Administrator
3. Enable WSL 2 integration if prompted
4. Restart computer when installation completes

**Mac:**
1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
2. Drag Docker.app to Applications folder
3. Launch Docker Desktop and follow setup prompts

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. Verify Docker Installation

```bash
docker --version
docker run --rm hello-world
```

### Basic Usage

#### First Test
```bash
# Test the container
docker run --rm canmet/h2k-hpxml h2k2hpxml --help

# Should show help text - confirms Docker and container work correctly
```

#### Convert Your Files

**Linux/Mac:**
```bash
# Convert H2K file in your current directory
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/your_file.h2k

# Convert entire folder (parallel processing)
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/
```

**Windows PowerShell:**
```powershell
# Convert H2K file in current directory
docker run --rm -v "${PWD}:/data" canmet/h2k-hpxml h2k2hpxml /data/your_file.h2k

# Convert entire folder
docker run --rm -v "${PWD}:/data" canmet/h2k-hpxml h2k2hpxml /data/
```

**Windows Command Prompt:**
```cmd
# Convert H2K file in current directory
docker run --rm -v "%cd%:/data" canmet/h2k-hpxml h2k2hpxml /data/your_file.h2k

# Convert entire folder
docker run --rm -v "%cd%:/data" canmet/h2k-hpxml h2k2hpxml /data/
```

#### Resilience Analysis
```bash
# Linux/Mac
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-resilience /data/your_file.h2k

# Windows PowerShell
docker run --rm -v "${PWD}:/data" canmet/h2k-hpxml h2k-resilience /data/your_file.h2k
```

## Docker Usage Examples

### File Conversion

```bash
# Basic conversion - process file in current directory
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# Process entire folder (uses parallel processing)
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/

# Specify output location
docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
  h2k2hpxml /data/input.h2k --output /data/output.xml

# Use separate input/output directories (Windows example)
docker run --rm \
  -v "C:\path\to\input":/input:ro \
  -v "C:\path\to\output":/output \
  canmet/h2k-hpxml h2k2hpxml /input/house.h2k --output /output/house.xml
```

### Resilience Analysis

```bash
# Basic resilience analysis
docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
  h2k-resilience /data/house.h2k

# With custom parameters
docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
  h2k-resilience /data/input.h2k \
  --outage-days 10 \
  --clothing-factor-summer 0.6 \
  --clothing-factor-winter 1.2 \
  --run-simulation
```

### Getting Help

```bash
# H2K conversion help
docker run --rm canmet/h2k-hpxml h2k2hpxml --help

# Resilience analysis help
docker run --rm canmet/h2k-hpxml h2k-resilience --help

# Show version
docker run --rm canmet/h2k-hpxml h2k2hpxml --version
```

## Docker Configuration

The Docker container automatically:
- Sets up all required dependencies (OpenStudio, OpenStudio-HPXML, Python packages)
- Creates configuration files in `/data/.h2k-config/` (preserved between runs)
- Creates output directories as needed

## Docker Desktop Configuration

### Memory and CPU Settings

For large batch processing, optimize Docker Desktop settings:

**Windows/Mac (Docker Desktop):**
1. Open Docker Desktop
2. Go to Settings → Resources
3. Recommended settings:
   - **Memory**: 8GB+ (minimum 4GB)
   - **CPUs**: Use all available cores
   - **Disk Space**: 20GB+ for processing large batches

### Windows-Specific Setup

#### Enable WSL 2 (Recommended)
```powershell
# Enable WSL and Virtual Machine Platform
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-for-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart computer, then set WSL 2 as default
wsl --set-default-version 2
```

#### File Sharing Configuration
1. Open Docker Desktop → Settings → Resources → File Sharing
2. Add drives you want to access (C:, D:, etc.)
3. Apply & Restart

#### Performance Tips for Windows
```powershell
# Use WSL 2 paths for better performance
docker run --rm -v "\\wsl$\Ubuntu\home\user\h2k_files:/data" canmet/h2k-hpxml h2k2hpxml /data/

# Or map network drive for easier access
net use Z: \\wsl$\Ubuntu\home\user\h2k_files
docker run --rm -v "Z:/:/data" canmet/h2k-hpxml h2k2hpxml /data/
```

## Advantages of Docker Approach
- ✅ No local Python/OpenStudio installation required
- ✅ Consistent environment across Windows, Mac, and Linux
- ✅ Automatic dependency management
- ✅ Version-pinned for reproducibility
- ✅ Easy to integrate into CI/CD pipelines
- ✅ Instant updates with `docker pull`
- ✅ No PATH or environment variable configuration
- ✅ Portable - works on any machine with Docker

## Advanced Docker Usage

### Volume Mounting Options

```bash
# Single directory (read/write)
-v $(pwd):/data                              # Current directory
-v /absolute/path:/data                      # Absolute path
-v "C:\Windows\Path":/data                   # Windows path

# Separate input/output directories
-v /path/to/h2k/files:/input:ro              # Read-only input
-v /path/to/output:/output                   # Write-only output

# Multiple mount points
docker run --rm \
  -v /home/user/h2k_files:/input:ro \
  -v /home/user/results:/output \
  -v /home/user/configs:/config \
  canmet/h2k-hpxml h2k2hpxml /input/house.h2k --output /output/house.xml
```

### Environment Variables

```bash
# Enable debug logging
docker run --rm -e H2K_LOG_LEVEL=DEBUG -v $(pwd):/data \
  canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# Custom configuration path
docker run --rm -e H2K_CONFIG_PATH=/data/custom_config.ini -v $(pwd):/data \
  canmet/h2k-hpxml h2k2hpxml /data/input.h2k
```

### Interactive Shell (Debugging)

```bash
# Enter container with interactive shell
docker run --rm -it -v $(pwd):/data canmet/h2k-hpxml bash

# Then run commands inside container
h2k2hpxml /data/input.h2k
h2k-deps --check-only
```

## Building the Docker Image Locally

There is currently no root Dockerfile in this repository. Use the published Docker images from Docker Hub (canmet/h2k-hpxml) or the VS Code DevContainer for development.

## Docker Compose (Batch Processing)

For processing multiple files or automating workflows, use Docker Compose:

### Basic docker-compose.yml

```yaml
# docker-compose.yml for batch processing entire folder
version: '3.8'
services:
  h2k-converter:
    image: canmet/h2k-hpxml
    volumes:
      - ./h2k_files:/input:ro
      - ./results:/output
    command: h2k2hpxml /input/ --output /output/
    # Processes all .h2k files in /input folder in parallel
```

### Running with Docker Compose

```bash
# Start batch processing
docker-compose up

# Run in background
docker-compose up -d

# Check logs
docker-compose logs

# Stop processing
docker-compose down
```

### Advanced Docker Compose Example

```yaml
version: '3.8'
services:
  # H2K to HPXML conversion service
  converter:
    image: canmet/h2k-hpxml:latest
    volumes:
      - ./input:/input:ro
      - ./output:/output
    command: h2k2hpxml /input/ --output /output/ --debug
    environment:
      - H2K_LOG_LEVEL=INFO
    
  # Resilience analysis service
  resilience:
    image: canmet/h2k-hpxml:latest
    volumes:
      - ./input:/input:ro
      - ./resilience_output:/output
    command: h2k-resilience /input/ --output /output/
    depends_on:
      - converter
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Process H2K Files
on: [push]

jobs:
  convert:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Convert H2K files
        run: |
          docker run --rm \
            -v ${{ github.workspace }}/h2k_files:/input:ro \
            -v ${{ github.workspace }}/output:/output \
            canmet/h2k-hpxml h2k2hpxml /input/ --output /output/
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: hpxml-output
          path: output/
```

## Performance Notes

When processing folders with Docker:
- The tool automatically uses parallel processing
- Utilizes `(CPU cores - 1)` threads
- All .h2k files are processed simultaneously
- Significantly faster than sequential processing

## Troubleshooting

### Common Issues

1. **Permission denied errors**
   ```bash
   # Add user permissions
   docker run --rm --user $(id -u):$(id -g) -v $(pwd):/data ...
   ```

2. **Path issues on Windows**
   ```bash
   # Use Windows-style paths
   docker run --rm -v "C:\Users\Name\Documents":/data ...
   ```

3. **Out of memory errors**
   ```bash
   # Increase Docker memory limit in Docker Desktop settings
   # Or limit parallel processing with environment variable
   docker run --rm -e MAX_WORKERS=4 ...
   ```

## Docker Hub Repository

The official Docker image is available at: [canmet/h2k-hpxml](https://hub.docker.com/r/canmet/h2k-hpxml)

```bash
# Pull latest version
docker pull canmet/h2k-hpxml:latest

# Pull specific version
docker pull canmet/h2k-hpxml:v1.0.0
```

## See Also

- [Installation Guide](INSTALLATION.md) - For local installation
- [Performance Guide](PERFORMANCE.md) - For optimization tips
- [Development Guide](DEVELOPMENT.md) - For contributing to the project
