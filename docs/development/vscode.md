# H2K-HPXML development using VSCode.

These are instructions on how to conduct development in the HPXML project, using development containers, and Visual Studio Code IDE. This method uses containers eliminate the need to install the correct version of python and other support tools required for development. It ensures that all developers are using the same consistent environment, same version of ruby and same toolchain. This help to avoid "It runs on my machine, but not yours" issues. The container is an Ubuntu linux based, and you can install linux console based applications if you wish. However, everything that you need for h2k-hpxml development is already included.

Another benefit is that simulations will run 50% faster using linux containers compared to Windows.


## Requirements
### Docker

**Windows**: [Docker Desktop 2.0+](https://www.docker.com/products/docker-desktop/) on Windows 10 Pro/Enterprise. Windows 10 Home (2004+) requires Docker Desktop 2.3+ and the WSL 2 back-end. (Docker Toolbox is not supported. Windows container images are not supported.) Installation instructions are [here](../installation/docker_windows_install.md).

**macOS**: [Docker Desktop 2.0+](https://www.docker.com/products/docker-desktop/).

**Linux**: Docker CE/EE 18.06+ and Docker Compose 1.21+. (The Ubuntu snap package is not supported.) Use your distros package manager to install.



Ensure that docker desktop is running on your system.  You should see it present in your windows task tray.  Then run the following command.

```
docker run hello-world
```

You should see the following output.

```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
c1ec31eb5944: Pull complete
Digest: sha256:d000bc569937abbe195e20322a0bde6b2922d805332fd6d8a68b19f524b7d21d
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```

### Visual Studio Code
[Visual Studio Code](https://code.visualstudio.com/) is an free to use editor that has a variety of publically created plug-ins. Some even support OpenStudio and EnergyPlus development which are included in this devcontainer by default. Click on the link above and install in on your computer.
## Configuration
1. Launch vscode and install the following extenstions.
    * [Remote-Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
    * [Remote-Containers-Extention-Pack](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)

## Development Workflow

### Clone H2K-HPXML Repository into a DevContainer
This will create a container workspace and clone all the source code for openstudio-standards required for development.
1. Hit Ctrl+Shift+P to bring up the command pallet on the top of vscode.
1. Start to type "Dev Containers" and select " Dev Containers: Clone Repository in Container Volume"
1. Enter the URL for the h2k-hpxml repository. For the main branch use:
```
https://github.com/canmet-energy/h2k-hpxml
```
1. Wait a few minutes for the container to be created and to clone the source-code.

### Bring up a terminal to execute commands.
1. Hit Ctrl-Shift-`  (that is a backtick, usually under the ~) to bring up a terminal. There are other ways to do this as well, such as the "Terminal Menu on the top or the "+" symbol to the right of the terminal on the bottom of vscode. You can now issue commands to the container.

### Install Certificates (Only if working while connected to the NRCan network)
Working from the NRCan network requires certificates to be installed in your container. Clone the cert repo with the command below. You need to request access from chris.kirney@nrcan.gc.ca
```sh
git clone https://github.com/canmet-energy/linux_nrcan_certs
```
Then install the certs by cut and pasting this command. This will also remove the cert folder as it will no longer be needed.
```ssh
cd linux_nrcan_certs && ./install_nrcan_certs.sh && cd .. && rm -fr linux_nrcan_certs
```

### Install / Update Python Packages.
This will install the package and all python dependencies.
1. In the terminal, enter:
```bash
uv pip install -e .
```

> **Note**: If you don't have `uv` installed, you can use pip: `pip install -e .`

### Configure Development Environment
After installing the package, set up your development configuration:

1. **Create configuration from template**:
   ```bash
   os-setup --setup
   ```

2. **Install dependencies automatically**:
   ```bash
   os-setup --auto-install
   ```

3. **Verify setup**:
   ```bash
   os-setup --check-only
   ```

4. **Run tests to verify everything works**:
   ```bash
   pytest tests/unit/
   ```

### Configuration Files

The development environment uses:
- **Main config**: `config/conversionconfig.ini` (created from template)
- **Template**: `config/templates/conversionconfig.template.ini` (version controlled)

Your configuration changes go in the main config file which is gitignored to avoid conflicts.

You are now ready for development! You can change branches/fork, commit, push and pull from git. You can run tests and quality checks from the terminal.

## Development Testing

### Run Tests
Tests are kept in the **tests** folder. To run tests:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with baseline generation (WARNING: overwrites golden files)
pytest --run-baseline
```

### Code Quality Checks

The project includes automated quality assurance tools:

```bash
# Run all quality checks (formatting, linting, type checking, tests)
./scripts/quality_check.sh

# Auto-fix formatting and linting issues
./scripts/quality_fix.sh

# Manual tools
black src/ tests/                    # Code formatting
ruff check src/ tests/               # Linting
mypy src/h2k_hpxml/core/            # Type checking
```


## Tips / Tricks
### Copy files to/from host into your workspace folder.
You can use the CTRL+C, CTRL-V to cut as paste to/from your host(windows) machine. You can also drag and drop files using the vscode folder Explorer.

## Development Workflow

### H2K to HPXML Translation

You can use the command line tools to translate and simulate H2K files:

1. **H2K to HPXML conversion**:
   ```bash
   # Convert a single file
   h2k-hpxml examples/WizardHouse.h2k

   # Convert with custom output
   h2k-hpxml examples/WizardHouse.h2k --output custom_output.xml

   # Get help on available options
   h2k-hpxml --help
   ```

2. **Resilience analysis**:
   ```bash
   # Run resilience analysis with all scenarios
   h2k-resilience examples/WizardHouse.h2k

   # Run specific scenarios
   h2k-resilience examples/WizardHouse.h2k --scenarios "outage_typical_year,thermal_autonomy_extreme_year"
   ```

### Output Files

By default, outputs are created in directories specified by your configuration:
- **HPXML files**: `output/hpxml/` (`.xml` files)
- **Simulation results**: `output/workflows/` (EnergyPlus files, results)
- **Comparison data**: `output/comparisons/` (analysis results)

The simulation workflow creates:
- **HPXML file**: The translated building model (`.xml`)
- **EnergyPlus files**: Input files (`.idf`), results (`.htm`, `.csv`, `.sql`)
- **OpenStudio files**: Model files (`.osm`) when debug flags are enabled

### Configuration for Development

Your development configuration is at `config/conversionconfig.ini`. Common settings to customize:

```ini
[paths]
# Your local H2K files
source_h2k_path = /path/to/your/h2k/files

# Auto-detected dependencies (updated by os-setup)
hpxml_os_path = /OpenStudio-HPXML/
openstudio_binary = /usr/local/bin/openstudio

[simulation]
# Add debug flags for detailed output
flags = --add-component-loads --debug --annual-output-file-format csv

[logging]
# Enable debug logging for development
log_level = DEBUG
log_to_file = true
```
