# Certificate Configuration

This directory can contain custom certificate files for corporate environments where additional certificates are needed for HTTPS connections.

## How to Use

1. **Place certificate files in this directory**:
   - Supported formats: `.crt` and `.pem` files
   - Example: `corporate-ca.crt`, `proxy-cert.pem`

2. **Rebuild the devcontainer**:
   - The Dockerfile will automatically detect and install any certificates found here
   - All development tools will be configured to use the system certificate store

## What Happens Automatically

When certificate files are detected:

### System Integration
- Certificates are copied to `/usr/local/share/ca-certificates/`
- System certificate store is updated via `update-ca-certificates`
- All applications will use the updated certificate bundle

### Environment Variables Set
- `SSL_CERT_DIR=/etc/ssl/certs`
- `SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`
- `CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt`
- `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` (Python requests)
- `NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt` (Node.js)

### Tool Configuration
- **curl**: Uses system certificate store
- **Python UV**: Configured to use system certificates
- **Node.js/npm**: Configured to use system certificates
- **Git**: Uses system certificate store
- **Docker CLI**: Uses system certificate store

## Corporate Network Setup

For corporate networks with TLS interception:

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

3. **Rebuild devcontainer**:
   - VS Code: Command Palette → "Dev Containers: Rebuild Container"
   - CLI: `docker build -f .devcontainer/Dockerfile .`

## Verification

After rebuilding with custom certificates:

1. **Check certificate status**: Login message will show certificate status
2. **Test connectivity**: All HTTPS downloads should work without `--insecure` flags
3. **Verify installation**: `ls -la /usr/local/share/ca-certificates/`

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
- The container will automatically fall back to insecure mode
- Check the login message for certificate status
- Verify the certificate chain is complete

## Example Corporate Certificate

If you need to export a certificate from your browser:
1. Navigate to any HTTPS site
2. Click the lock icon → Certificate details
3. Export the root CA certificate
4. Save as `.crt` or `.pem` file in this directory