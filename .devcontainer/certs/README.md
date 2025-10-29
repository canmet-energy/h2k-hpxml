# Certificate Configuration (Unified via certctl-safe)

Place optional corporate / custom CA certificates here to have them trusted inside the dev container and production image.

## How to Use

1. **Place certificate files in this directory**:
   - Supported formats: `.crt` and `.pem` files (PEM format)
   - Example: `corporate-ca.crt`, `proxy-cert.pem`

2. **Rebuild the devcontainer**:
   - The Dockerfile will automatically install any certificates via `certctl certs-refresh`
   - All development tools will be configured to use the system certificate store

## What Happens Automatically

During container build:
1. **Certificate Installation** (`certctl certs-refresh`):
   - Cleans old custom certificates from `/usr/local/share/ca-certificates/custom/`
   - Copies `.crt` files directly to `/usr/local/share/ca-certificates/custom/`
   - Converts `.pem` files to `.crt` format and installs them
   - Runs `update-ca-certificates` to rebuild the system certificate store

2. **Dynamic Environment Detection** (`certctl_load`):
   - Probes multiple targets to detect network certificate status
   - Automatically configures environment based on results:
     - **SECURE**: Valid certificates detected - normal SSL validation
     - **INSECURE**: Certificate issues detected - automatic fallback to insecure mode
   - 10-second timeout ensures probe has time to complete
   - Tools (curl, uv, requests, node, git, pip, npm, AWS CLI) are configured appropriately

## Corporate Network Setup

1. **Get your corporate CA certificate**:
   - Contact your IT department
   - Export from your browser's certificate store
   - Usually named something like `Corporate-Root-CA.crt`

2. **Add to this directory**:
   ```
   .devcontainer/certs/
   ├── Corporate-Root-CA.crt
   └── README.md
   ```

3. **Rebuild devcontainer** (VS Code Rebuild or image build) – certificates become trusted.

## Certificate Management Commands

After container is built, you can manage certificates manually:

**Status and Information:**
- `certctl certs-status` - Show detailed certificate installation status
- `certctl status` - Show overall certificate validation status
- `certctl banner` - Show certificate status banner

**Manual Management:**
- `certctl certs-refresh` - Full certificate refresh (clean + install + update)
- `certctl certs-clean` - Remove old custom certificates only
- `certctl certs-install` - Install certificates from `/tmp/certs/` (if available)
- `certctl certs-update` - Update system certificate store only

## Verification (Strict Mode)

The system tests certificate validation against these targets:
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

**Verification Steps:**
1. **Quick check**: `curl -I https://pypi.org/` (should work without `-k`)
2. **Detailed status**: `certctl status` (shows probe results and environment)
3. **Certificate info**: `certctl certs-status` (shows installed custom certificates)
4. **Shell status**: New terminal shows certificate banner automatically
5. **Verify files**: `ls -la /usr/local/share/ca-certificates/custom/`

**Certificate Status Values:**
- **SECURE_CUSTOM**: All targets OK + custom certificates installed
- **SECURE**: All targets OK (system certificates only)
- **INSECURE**: One or more probe failures (automatic fallback mode with `-k` flags and insecure environment variables)
- **UNKNOWN**: Unable to determine status (uses secure defaults for safety)

## Security Notes

- **Only add trusted certificates**: These certificates will be trusted system-wide
- **Keep certificates updated**: Corporate certificates may expire and need renewal
- **Version control**: Consider adding `*.crt` and `*.pem` to `.gitignore` if they contain sensitive information

## Troubleshooting

### Certificate Not Working
- Verify file format (must be PEM format, even with `.crt` extension)
- Check file permissions (should be readable)
- Rebuild container completely (don't use cached layers)

### Still Getting Certificate Errors
- Run: `certctl status` to see detailed probe results and current status
- If status is INSECURE and you have corporate certs available:
  1. Install missing corporate root/intermediate certificates in this directory
  2. Rebuild the container completely (don't use cached layers)
  3. Verify installation: `certctl certs-status`
- Verify certificate format: `openssl x509 -in your-cert.crt -text -noout | less`
- Domain-specific failures may need firewall/proxy adjustments
- For persistent issues, try: `sudo certctl certs-refresh` to reload certificates
- Note: INSECURE mode is automatically enabled for development - tools will still work with bypass flags

## Example Corporate Certificate

If you need to export a cert from your browser:
1. Navigate to any HTTPS site
2. View certificate chain (lock icon)
3. Export root CA (PEM)
4. Save here and rebuild