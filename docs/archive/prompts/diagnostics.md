# DevContainer & WSL2 Diagnostic Report
Generated: July 24, 2025
Source: Working h2k_hpxml System

## 🎯 Purpose
This report focuses on **container configuration and WSL2 setup** for troubleshooting systems where h2k_hpxml devcontainer doesn't work properly.

## 🐳 DevContainer Configuration

### Complete devcontainer.json
```json
{
	"name": "H2K_HPXML",
	"image": "canmet/model_dev_container:3.9.0",
	"containerUser": "vscode",
	"containerEnv": {
		"NODE_TLS_REJECT_UNAUTHORIZED": "0"
	},
	"runArgs": [
        "--env=LANG=en_US.UTF-8",
        "--cap-add=SYS_PTRACE",
        "--security-opt", "seccomp=unconfined",
        // WSLg support for GUI applications
        "--env=DISPLAY=:0",
        "--env=WAYLAND_DISPLAY=wayland-0",
        "--env=XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir",
        "--env=PULSE_SERVER=/mnt/wslg/PulseServer",
        "--volume=/run/desktop/mnt/host/wslg/.X11-unix:/tmp/.X11-unix",
        "--volume=/run/desktop/mnt/host/wslg:/mnt/wslg",
        "--cap-add=SYS_PTRACE",
        "--security-opt", "seccomp=unconfined"
    ],
	"customizations": {
		"vscode": {
			"extensions": [
				"castwide.solargraph",
				"ms-azuretools.vscode-docker",
				"KoichiSasada.vscode-rdbg",
				"karyfoundation.idf",
				"ms-python.python",
				"mechatroner.rainbow-csv",
				"janisdd.vscode-edit-csv",
				"qwtel.sqlite-viewer",
				"ms-toolsai.jupyter",
				"ms-vscode.powershell"
			],
			"settings": {
				"files.associations": {
					"*.h2k": "xml",
					"*.hpxml": "xml",
					"*.sql": "sqlite"
				},
				"terminal.integrated.env.linux": {
                    "WINEARCH": "win32",
                    "WINEPREFIX": "/home/vscode/.wine_hot2000",
                    "WINEDEBUG": "-all",
                    "DISPLAY": ":0"
                },
				"python.terminal.activateEnvironment": true,
				"python.defaultInterpreterPath": "/workspaces/h2k_hpxml/venv/bin/python",
				"python.terminal.activateEnvInCurrentTerminal": true
			}
		}
	},
  "remoteUser": "vscode",
  "postCreateCommand": "if [ \"$(curl -k -o /dev/null -s -w \"%{http_code}\" \"https://intranet.nrcan.gc.ca/\")\" -ge 200 ] && [ \"$(curl -o /dev/null -s -w \"%{http_code}\" \"https://intranet.nrcan.gc.ca/\")\" -lt 400 ]; then echo \"nrcan network detected.\" && git clone https://github.com/canmet-energy/linux_nrcan_certs.git && cd linux_nrcan_certs && ./install_nrcan_certs.sh && cd .. && rm -fr linux_nrcan_certs ; fi && bash -c 'curl -fsSLk https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs && sudo apt-get update && cd /workspaces/h2k_hpxml && python -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -e . && pip install pytest && sudo npm config set strict-ssl false && sudo npm install -g @anthropic-ai/claude-code' && sudo apt install -y x11-apps"
}
```

### Critical DevContainer Elements

#### 🔑 **Base Image**
```json
"image": "canmet/model_dev_container:3.9.0"
```
- **What to check**: Does the image exist and is it accessible?
- **Test**: `docker pull canmet/model_dev_container:3.9.0`

#### 🖥️ **WSLg GUI Support** (Most Common Issue)
```json
"runArgs": [
    "--env=DISPLAY=:0",
    "--env=WAYLAND_DISPLAY=wayland-0",
    "--env=XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir",
    "--env=PULSE_SERVER=/mnt/wslg/PulseServer",
    "--volume=/run/desktop/mnt/host/wslg/.X11-unix:/tmp/.X11-unix",
    "--volume=/run/desktop/mnt/host/wslg:/mnt/wslg"
]
```

#### 🔒 **Security Settings**
```json
"--cap-add=SYS_PTRACE",
"--security-opt", "seccomp=unconfined"
```

#### 🏗️ **Post-Create Command**
Complex setup including:
- NRCAN network detection
- Node.js installation
- Python virtual environment setup
- Package installation
- X11 apps installation

## 💻 Host System Requirements

### Windows Requirements
- **Windows 11** or **Windows 10 version 19043+**
- **WSL2** installed and enabled
- **WSLg** enabled (usually automatic with WSL2)
- **Docker Desktop** with WSL2 backend

### WSL2 Configuration
```bash
# Check WSL version
wsl --version

# Expected output should show:
# WSL version: 2.x.x.x
# Kernel version: 5.x.x.x
# WSLg version: 1.x.x
```

### Docker Desktop Settings
- **WSL2 Backend**: Must be enabled
- **WSL Integration**: Enabled for default distribution
- **Resource Limits**: Adequate memory/CPU allocation

## 🗂️ Critical Mount Points & Contents

### WSLg and GUI Related Mounts
```bash
# Primary WSLg mount point
/mnt/wslg/ → tmpfs (rw,relatime)
├── distro/          # WSL distribution files
├── doc/             # Documentation and help files
├── runtime-dir/     # Runtime sockets and IPC
│   ├── pulse/       # PulseAudio configuration
│   ├── wayland-0    # Wayland display socket
│   ├── wayland-0.lock
│   └── vscode-ipc-*.sock  # VS Code IPC sockets
├── PulseServer      # Audio server socket
├── PulseAudioRDP*   # RDP audio sinks/sources
└── *.log            # Various log files

# X11 display socket
/tmp/.X11-unix/ → tmpfs (rw,relatime)
└── X0               # X11 display :0 socket

# Container filesystem
/ → overlay (Docker overlay filesystem)
```

### Expected Mount Points on Working System
```bash
# WSLg GUI support
none on /tmp/.X11-unix type tmpfs (rw,relatime)
none on /mnt/wslg type tmpfs (rw,relatime)
/dev/sdg on /mnt/wslg/distro type ext4 (ro,relatime)

# Standard container mounts
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
tmpfs on /dev type tmpfs (rw,nosuid,size=65536k,mode=755)
sysfs on /sys type sysfs (ro,nosuid,nodev,noexec,relatime)

# Docker overlay filesystem
overlay on / type overlay (...)
```

### Critical Files/Sockets to Check
```bash
# GUI functionality
/tmp/.X11-unix/X0                    # X11 display socket (MUST exist)
/mnt/wslg/runtime-dir/wayland-0      # Wayland display socket
/mnt/wslg/PulseServer               # Audio server socket

# Container identification
/etc/hostname                        # Container hostname
/etc/os-release                     # OS information
```

### What Each Mount Provides
- **`/mnt/wslg/`**: Complete WSLg environment (display server, audio, runtime)
- **`/tmp/.X11-unix/`**: X11 display server socket for GUI applications
- **`/mnt/wslg/runtime-dir/`**: Runtime sockets for Wayland, audio, VS Code IPC
- **`overlay on /`**: Container filesystem with all installed packages

## 🧪 Diagnostic Commands for Problem System

### 1. Host System Checks (Run on Windows)
```powershell
# Check WSL2 status
wsl --status

# Check WSL version
wsl --version

# List WSL distributions
wsl --list --verbose

# Check Docker Desktop status
docker --version
docker info
```

### 2. Container Environment Checks (Inside devcontainer)
```bash
# Check environment variables
echo "DISPLAY: $DISPLAY"
echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
echo "PULSE_SERVER: $PULSE_SERVER"

# Check WSLg mounts
ls -la /mnt/wslg/ 2>/dev/null && echo "✅ WSLg mounted" || echo "❌ WSLg not mounted"
ls -la /tmp/.X11-unix/ 2>/dev/null && echo "✅ X11 socket mounted" || echo "❌ X11 socket not mounted"

# Check specific critical files
test -S /tmp/.X11-unix/X0 && echo "✅ X11 display socket exists" || echo "❌ X11 display socket missing"
test -S /mnt/wslg/PulseServer && echo "✅ Audio server available" || echo "❌ Audio server missing"
test -S /mnt/wslg/runtime-dir/wayland-0 && echo "✅ Wayland socket exists" || echo "❌ Wayland socket missing"

# Check container user and permissions
whoami
id
pwd

# Check if GUI works
which xeyes && echo "✅ X11 apps available" || echo "❌ X11 apps missing"
```

### 3. Docker Configuration Checks
```bash
# Check if running in correct container
cat /etc/hostname
cat /etc/os-release | head -5

# Check container mounts
mount | grep wslg
mount | grep X11-unix

# Check container capabilities
cat /proc/1/status | grep Cap
```

## 🚨 Common Issues & Solutions

### Issue 1: "Cannot connect to X server"
**Root Cause**: WSLg not properly configured or mounted

**Solutions**:
1. **Enable WSLg on Windows**:
   ```powershell
   # In PowerShell as Administrator
   wsl --update
   wsl --shutdown
   # Restart Docker Desktop
   ```

2. **Check Docker Desktop Settings**:
   - Settings → General → "Use WSL 2 based engine" ✅
   - Settings → Resources → WSL Integration → Enable for your distribution

3. **Verify devcontainer runArgs**:
   - All WSLg volume mounts present
   - Environment variables set correctly

### Issue 2: Container Won't Start
**Root Cause**: Base image not accessible or Docker issues

**Solutions**:
1. **Test image access**:
   ```bash
   docker pull canmet/model_dev_container:3.9.0
   ```

2. **Check Docker Desktop**:
   - Restart Docker Desktop
   - Clear Docker cache: `docker system prune -a`

3. **Network Issues**:
   - Check corporate firewall/proxy settings
   - Verify Docker registry access

### Issue 3: Post-Create Command Fails
**Root Cause**: Network access or permission issues

**Solutions**:
1. **Check network connectivity**:
   ```bash
   curl -I https://deb.nodesource.com/
   ```

2. **Manual setup** (skip postCreateCommand):
   ```bash
   cd /workspaces/h2k_hpxml
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   sudo apt update && sudo apt install -y x11-apps
   ```

### Issue 4: VS Code DevContainer Extension Issues
**Solutions**:
1. **Update extensions**:
   - Dev Containers extension
   - Docker extension
   - WSL extension

2. **Reload VS Code**: `Ctrl+Shift+P` → "Developer: Reload Window"

3. **Rebuild container**: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

## 🔧 Troubleshooting Workflow

### Step 1: Verify Host Prerequisites
```powershell
# Windows PowerShell (as Administrator)
wsl --version              # Should show WSL2 and WSLg versions
docker --version           # Should show Docker version
docker info | findstr WSL  # Should show WSL2 backend active
```

### Step 2: Test Base Image Access
```bash
docker pull canmet/model_dev_container:3.9.0
```

### Step 3: Test Manual Container Run
```bash
docker run -it --rm \
  --env=DISPLAY=:0 \
  --env=WAYLAND_DISPLAY=wayland-0 \
  --env=XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir \
  --volume=/run/desktop/mnt/host/wslg/.X11-unix:/tmp/.X11-unix \
  --volume=/run/desktop/mnt/host/wslg:/mnt/wslg \
  canmet/model_dev_container:3.9.0 \
  bash -c "echo \$DISPLAY && ls -la /mnt/wslg/"
```

### Step 4: Test DevContainer Launch
1. Open VS Code
2. `Ctrl+Shift+P` → "Dev Containers: Open Folder in Container"
3. Select the h2k_hpxml folder
4. Monitor build process in terminal

### Step 5: Verify Container Environment
```bash
# Inside devcontainer
./diagnose_container.sh  # Use commands from section 2 above
```

## 📋 Quick Environment Test Script

Create this script to run on the problem system:

```bash
#!/bin/bash
# save as: test_devcontainer_env.sh

echo "🔍 DevContainer Environment Diagnostic"
echo "======================================"

echo -e "\n1. Host System:"
echo "Windows Version: $(cmd.exe /c ver 2>/dev/null || echo 'Not Windows')"

echo -e "\n2. WSL Status:"
wsl.exe --version 2>/dev/null || echo "WSL not available"

echo -e "\n3. Docker Status:"
docker --version 2>/dev/null || echo "Docker not available"
docker info >/dev/null 2>&1 && echo "✅ Docker running" || echo "❌ Docker not running"

echo -e "\n4. Container Environment:"
echo "Display: $DISPLAY"
echo "User: $(whoami)"
echo "Working Dir: $(pwd)"

echo -e "\n5. WSLg Mounts:"
ls -la /mnt/wslg/ 2>/dev/null && echo "✅ WSLg mounted" || echo "❌ WSLg not mounted"

echo -e "\n6. X11 Socket:"
ls -la /tmp/.X11-unix/ 2>/dev/null && echo "✅ X11 socket available" || echo "❌ X11 not available"

echo -e "\n7. Critical GUI Files:"
test -S /tmp/.X11-unix/X0 && echo "✅ X11 display :0 socket" || echo "❌ X11 display socket missing"
test -S /mnt/wslg/PulseServer && echo "✅ Audio server socket" || echo "❌ Audio server missing"
test -S /mnt/wslg/runtime-dir/wayland-0 && echo "✅ Wayland socket" || echo "❌ Wayland socket missing"

echo -e "\n8. GUI Test:"
which xeyes >/dev/null 2>&1 && echo "✅ X11 apps available" || echo "❌ X11 apps missing"

echo -e "\n9. Image Info:"
cat /etc/os-release | head -3 2>/dev/null || echo "Container info not available"

echo -e "\n======================================"
echo "Share this output for troubleshooting"
```

## 📞 What to Share for Support

When reporting issues, include:

1. **Output of test script above**
2. **Windows version** (`winver` command)
3. **VS Code version** and installed extensions
4. **Docker Desktop version** and settings screenshot
5. **Complete error messages** from devcontainer build
6. **Network environment** (corporate/proxy settings)

---

**Focus**: This diagnostic targets container/WSL2 configuration issues, not Python code problems.
