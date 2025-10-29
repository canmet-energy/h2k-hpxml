#!/bin/bash
# certctl-safe.sh - Complete portable certificate management for DevContainers
# Single-script solution that won't break shell initialization
# Version: 2.0.0

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default probe targets
DEFAULT_TARGETS=(
  "https://pypi.org/"
  "https://registry.npmjs.org/"
  "https://github.com/"
  "https://cli.github.com/"
  "https://download.docker.com/"
  "https://nodejs.org/"
  "https://awscli.amazonaws.com/"
  "https://s3.amazonaws.com/"
)

# Default insecure hosts for UV_INSECURE_HOST
DEFAULT_INSECURE_HOSTS="github.com codeload.github.com objects.githubusercontent.com pypi.org files.pythonhosted.org registry.npmjs.org nodejs.org download.docker.com awscli.amazonaws.com s3.amazonaws.com"

# Timeouts
PROBE_TIMEOUT="${CERTCTL_PROBE_TIMEOUT:-10}"      # Per-URL timeout
TOTAL_TIMEOUT="${CERTCTL_TOTAL_TIMEOUT:-10}"      # Total operation timeout

# Debug control (stderr debug stream)
DEBUG="${CERTCTL_DEBUG:-0}"

# Logging (persistent file for post-mortem troubleshooting)
# Override with CERTCTL_LOG_FILE. Falls back to /tmp if /var/log not writable.
CERTCTL_LOG_FILE_DEFAULT="${CERTCTL_LOG_FILE:-/var/log/certctl.log}"
if touch "$CERTCTL_LOG_FILE_DEFAULT" 2>/dev/null; then
    LOG_FILE="$CERTCTL_LOG_FILE_DEFAULT"
else
    LOG_FILE="/tmp/certctl.log"
fi

# Initialize log file with header (once per shell execution)
if [ -z "${CERTCTL_LOG_INIT_DONE:-}" ]; then
    {
        echo "==== certctl session $(date -u '+%Y-%m-%dT%H:%M:%SZ') pid=$$ ===="
        echo "SCRIPT_VERSION=2.0.0 DEBUG=$DEBUG LOG_FILE=$LOG_FILE USER=$(whoami) EUID=$EUID"
    } >>"$LOG_FILE" 2>/dev/null || true
    CERTCTL_LOG_INIT_DONE=1
fi

# Certificate bundle path
CERT_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

# ============================================================================
# DEBUG FUNCTIONS
# ============================================================================

debug() {
    if [ "$DEBUG" = "1" ]; then
        echo "[certctl] $*" >&2
    fi
}

# Always write to logfile (and optionally stderr when DEBUG=1)
log_msg() {
    local ts
    ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    echo "$ts $*" >>"$LOG_FILE" 2>/dev/null || true
    if [ "$DEBUG" = "1" ]; then
        echo "[certctl] $*" >&2
    fi
}

# ============================================================================
# CORE FUNCTIONS (safe for sourcing)
# ============================================================================

# Compute insecure hosts list
compute_insecure_hosts() {
    # Check for override
    if [ -n "${CERTCTL_INSECURE_HOSTS:-}" ]; then
        echo "${CERTCTL_INSECURE_HOSTS//,/ }" | xargs
        return 0
    fi

    # Start with defaults
    local hosts="$DEFAULT_INSECURE_HOSTS"

    # Add any appended hosts
    if [ -n "${CERTCTL_APPEND_INSECURE_HOSTS:-}" ]; then
        local append="${CERTCTL_APPEND_INSECURE_HOSTS//,/ }"
        hosts="$hosts $append"
    fi

    # Deduplicate while preserving order
    local cleaned=""
    for host in $hosts; do
        case " $cleaned " in
            *" $host "*) ;;
            *) cleaned="$cleaned $host" ;;
        esac
    done

    echo "$cleaned" | xargs
}

# Safe probe function - runs in subshell, never exits parent
certctl_probe() {
    debug "Starting certificate probe"
    log_msg "probe:start PROBE_TIMEOUT=$PROBE_TIMEOUT TOTAL_TIMEOUT=$TOTAL_TIMEOUT targets_override='${CERTCTL_TARGETS:-<default>}'"

    # Run the actual probe in a subshell with timeout
    local result
    result=$(timeout "$TOTAL_TIMEOUT" bash -c '
        # This runs in a subshell - safe to fail
        success=0
        fail=0
        targets=(
          "https://pypi.org/"
          "https://registry.npmjs.org/"
          "https://github.com/"
          "https://cli.github.com/"
          "https://download.docker.com/"
          "https://nodejs.org/"
          "https://awscli.amazonaws.com/"
          "https://s3.amazonaws.com/"
        )

        # Override targets if specified
        if [ -n "$CERTCTL_TARGETS" ]; then
            IFS=" " read -ra targets <<< "$CERTCTL_TARGETS"
        fi

        total=${#targets[@]}

        # Test each target
        for url in "${targets[@]}"; do
            if timeout '"$PROBE_TIMEOUT"' curl -sSf --connect-timeout 10 "$url" >/dev/null 2>&1; then
                success=$((success + 1))
                [ "'$DEBUG'" = "1" ] && echo "[probe] ✓ $url" >&2
            else
                fail=$((fail + 1))
                [ "'$DEBUG'" = "1" ] && echo "[probe] ✗ $url" >&2
            fi
        done

        # Export counts
        echo "export CERT_SUCCESS_COUNT=$success"
        echo "export CERT_FAIL_COUNT=$fail"
        echo "export CERT_TOTAL_COUNT=$total"

        # Determine status - ALL must succeed for SECURE
        if [ $fail -eq 0 ]; then
            echo "export CERT_STATUS=SECURE"
        else
            echo "export CERT_STATUS=INSECURE"
        fi
    ' 2>/dev/null) || {
        # On timeout or error, return UNKNOWN
        echo "export CERT_STATUS=UNKNOWN"
        echo "export CERT_SUCCESS_COUNT=0"
        echo "export CERT_FAIL_COUNT=0"
        echo "export CERT_TOTAL_COUNT=0"
    }

    debug "Probe complete"
    # Extract simple status for logfile
    if echo "$result" | grep -q 'CERT_STATUS='; then
        local st
        st=$(echo "$result" | sed -n 's/export CERT_STATUS=//p')
        log_msg "probe:complete status=$st success=$(echo "$result" | sed -n 's/export CERT_SUCCESS_COUNT=//p') fail=$(echo "$result" | sed -n 's/export CERT_FAIL_COUNT=//p') total=$(echo "$result" | sed -n 's/export CERT_TOTAL_COUNT=//p')"
    else
        log_msg "probe:complete status=UNKNOWN (no parse)"
    fi
    echo "$result"
}

# Generate environment variables (always succeeds)
certctl_env() {
    local probe_output="${1:-}"

    # Get probe results if not provided
    if [ -z "$probe_output" ]; then
        probe_output=$(certctl_probe)
    fi

    # Parse the probe output to get status
    local status="UNKNOWN"
    if [[ "$probe_output" == *"CERT_STATUS=SECURE"* ]]; then
        if certctl_has_custom_certs; then
            status="SECURE_CUSTOM"
        else
            status="SECURE"
        fi
    elif [[ "$probe_output" == *"CERT_STATUS=INSECURE"* ]]; then
        status="INSECURE"
    fi

    # Output probe results first
    echo "$probe_output"

    # Always set certificate locations
    echo "export SSL_CERT_DIR=/etc/ssl/certs"
    echo "export SSL_CERT_FILE=$CERT_BUNDLE"
    echo "export CURL_CA_BUNDLE=$CERT_BUNDLE"
    echo "export REQUESTS_CA_BUNDLE=$CERT_BUNDLE"
    echo "export AWS_CA_BUNDLE=$CERT_BUNDLE"
    echo "export NODE_EXTRA_CA_CERTS=$CERT_BUNDLE"
    echo "export PIP_CERT=$CERT_BUNDLE"
    echo "export BUNDLE_SSL_CA_CERT=$CERT_BUNDLE"

    # Set mode-specific variables
    case "$status" in
        SECURE|SECURE_CUSTOM)
            echo "export CURL_FLAGS='-fsSL'"
            echo "export UV_NATIVE_TLS=true"
            echo "unset CERT_INSECURE 2>/dev/null || true"
            echo "unset NODE_TLS_REJECT_UNAUTHORIZED 2>/dev/null || true"
            echo "unset GIT_SSL_NO_VERIFY 2>/dev/null || true"
            echo "unset UV_INSECURE 2>/dev/null || true"
            echo "unset UV_INSECURE_HOST 2>/dev/null || true"
            echo "unset PIP_TRUSTED_HOST 2>/dev/null || true"
            echo "unset NPM_CONFIG_STRICT_SSL 2>/dev/null || true"
            ;;
        INSECURE)
            echo "export CERT_INSECURE=1"
            echo "export CURL_FLAGS='-fsSLk'"
            echo "export NODE_TLS_REJECT_UNAUTHORIZED=0"
            echo "export GIT_SSL_NO_VERIFY=1"
            echo "export UV_NATIVE_TLS=false"
            echo "export UV_INSECURE=1"
            echo "export UV_INSECURE_HOST='$(compute_insecure_hosts)'"
            echo "export PIP_TRUSTED_HOST='pypi.org pypi.python.org files.pythonhosted.org'"
            echo "export NPM_CONFIG_STRICT_SSL=false"
            ;;
        *)
            # Unknown status - use safe defaults
            echo "export CURL_FLAGS='-fsSL'"
            echo "export UV_NATIVE_TLS=true"
            ;;
    esac
}

# Load environment - safe for shell initialization
certctl_load() {
    debug "Loading certificate environment"
    log_msg "env:load:start"

    # Run probe and load environment (with timeout and fallback)
    local env_output
    if env_output=$(timeout 10s bash -c '. /usr/local/bin/certctl && certctl_env' 2>/dev/null); then
        eval "$env_output"
    else
        # Fallback to safe defaults if probe fails/times out
        export CERT_STATUS=UNKNOWN
        export CERT_SUCCESS_COUNT=0
        export CERT_FAIL_COUNT=0
        export CERT_TOTAL_COUNT=0
        export CURL_FLAGS='-fsSL'
        export SSL_CERT_DIR=/etc/ssl/certs
        export SSL_CERT_FILE=$CERT_BUNDLE
        export CURL_CA_BUNDLE=$CERT_BUNDLE
        export REQUESTS_CA_BUNDLE=$CERT_BUNDLE
        export AWS_CA_BUNDLE=$CERT_BUNDLE
        export NODE_EXTRA_CA_CERTS=$CERT_BUNDLE
        export PIP_CERT=$CERT_BUNDLE
        export BUNDLE_SSL_CA_CERT=$CERT_BUNDLE
        export UV_NATIVE_TLS=true
    fi

    debug "Environment loaded: CERT_STATUS=$CERT_STATUS"
    log_msg "env:load:complete CERT_STATUS=${CERT_STATUS:-UNKNOWN} CURL_FLAGS=${CURL_FLAGS:-unset}"
}

# Status banner for interactive display
certctl_banner() {
    case "${CERT_STATUS:-UNKNOWN}" in
        SECURE)
            echo "✅ Certificates: Secure validation OK"
            ;;
        SECURE_CUSTOM)
            echo "✅ Certificates: Secure validation OK (with custom certificates)"
            ;;
        INSECURE)
            echo "⚠️  Certificates: Insecure mode (SSL verification disabled) Please check your custom certificates. This could be in violation of your corporate policies. If this is a devcontainer, place valid certs provided by your organization in .devcontainer/certs/ and rebuild. You may continue to use this to debug your cert issues, but it is not recommended for development or production use."
            ;;
        *)
            echo "❓ Certificates: Unknown status"
            ;;
    esac

    if [ "$DEBUG" = "1" ] && [ -n "${CERT_SUCCESS_COUNT:-}" ]; then
        echo "   Probe results: $CERT_SUCCESS_COUNT/$CERT_TOTAL_COUNT successful"
    fi
}

# ============================================================================
# CERTIFICATE MANAGEMENT FUNCTIONS
# ============================================================================

# Clean old custom certificates
certctl_clean_certs() {
    debug "Cleaning old custom certificates"
    log_msg "certs:clean:start"

    if [ "$EUID" -ne 0 ]; then
        echo "ERROR: Certificate management requires root permissions"
        return 1
    fi

    # Remove custom certificate directory
    if [ -d "/usr/local/share/ca-certificates/custom" ]; then
        echo "Removing old custom certificates..."
        rm -rf /usr/local/share/ca-certificates/custom
        mkdir -p /usr/local/share/ca-certificates/custom
    else
        mkdir -p /usr/local/share/ca-certificates/custom
    fi

    # Verify cleanup was successful
    local remaining_certs=$(find /usr/local/share/ca-certificates/custom -name '*.crt' 2>/dev/null | wc -l)
    if [ "$remaining_certs" -eq 0 ]; then
        echo "Custom certificate cleanup: OK"
        log_msg "certs:clean:complete remaining=0"
    else
        echo "WARNING: $remaining_certs custom certificates remain after cleanup"
        log_msg "certs:clean:warning remaining=$remaining_certs"
        return 1
    fi
}

# Validate certificate format
certctl_validate_cert() {
    local cert_file="$1"
    log_msg "cert:validate:start file=$cert_file"

    # Check if file exists and is readable
    if [ ! -f "$cert_file" ] || [ ! -r "$cert_file" ]; then
        debug "Certificate file not accessible: $cert_file"
        log_msg "cert:validate:fail reason=not_accessible file=$cert_file"
        return 1
    fi

    # Check if file contains valid PEM certificate structure
    if ! grep -q "BEGIN CERTIFICATE" "$cert_file" || ! grep -q "END CERTIFICATE" "$cert_file"; then
        debug "Certificate file missing PEM markers: $cert_file"
        log_msg "cert:validate:fail reason=missing_pem_markers file=$cert_file"
        return 1
    fi

    # Use openssl to validate certificate format (if available)
    if command -v openssl >/dev/null 2>&1; then
        if ! openssl x509 -in "$cert_file" -noout >/dev/null 2>&1; then
            debug "Certificate file failed OpenSSL validation: $cert_file"
            log_msg "cert:validate:fail reason=openssl_validation file=$cert_file"
            return 1
        fi
    fi
    log_msg "cert:validate:success file=$cert_file"
    return 0
}

# Backup certificate bundle
certctl_backup_bundle() {
    local backup_dir="/var/backups/certctl"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/ca-certificates-$timestamp.crt"

    debug "Creating certificate bundle backup"
    log_msg "bundle:backup:start dest=$backup_file"

    # Create backup directory
    mkdir -p "$backup_dir"

    # Backup current bundle
    if [ -f "$CERT_BUNDLE" ]; then
    cp "$CERT_BUNDLE" "$backup_file"
    echo "Certificate bundle backed up to: $backup_file"
    log_msg "bundle:backup:complete file=$backup_file"

        # Keep only last 5 backups
        find "$backup_dir" -name "ca-certificates-*.crt" -type f | sort | head -n -5 | xargs rm -f 2>/dev/null || true
    fi
}

# Verify certificate bundle integrity after operations
certctl_verify_bundle() {
    debug "Verifying certificate bundle integrity"
    log_msg "bundle:verify:start file=$CERT_BUNDLE"

    # Check if bundle file exists and is readable
    if [ ! -f "$CERT_BUNDLE" ] || [ ! -r "$CERT_BUNDLE" ]; then
        echo "ERROR: Certificate bundle not accessible: $CERT_BUNDLE"
        log_msg "bundle:verify:fail reason=not_accessible file=$CERT_BUNDLE"
        return 1
    fi

    # Check if bundle has reasonable size (should be > 100KB for typical system)
    local bundle_size=$(stat -c%s "$CERT_BUNDLE" 2>/dev/null || echo 0)
    if [ "$bundle_size" -lt 100000 ]; then
        echo "WARNING: Certificate bundle unusually small ($bundle_size bytes)"
        log_msg "bundle:verify:warning reason=small size=$bundle_size"
        return 1
    fi

    # Test bundle with curl if possible
    if command -v curl >/dev/null 2>&1; then
        if ! timeout 3s curl -sSf --cacert "$CERT_BUNDLE" https://github.com/ >/dev/null 2>&1; then
            echo "WARNING: Certificate bundle failed validation test"
            log_msg "bundle:verify:warning reason=curl_validation_failed"
            return 1
        fi
    fi

    echo "Certificate bundle verification: OK"
    log_msg "bundle:verify:success size=$bundle_size"
    return 0
}

# Install certificates from staging directory
certctl_install_certs() {
    debug "Installing certificates from /tmp/certs/"
    log_msg "certs:install:start source_scan=/tmp/certs"

    if [ "$EUID" -ne 0 ]; then
        echo "ERROR: Certificate management requires root permissions"
        return 1
    fi

    local cert_source="/tmp/certs"
    local cert_dest="/usr/local/share/ca-certificates/custom"
    local installed_count=0
    local validation_failed=0

    # Check if source directory exists and has certificates
    if [ ! -d "$cert_source" ]; then
        debug "No certificate source directory found at $cert_source"
        log_msg "certs:install:skip reason=source_dir_missing path=$cert_source"
        return 0
    fi

    # Log directory listing (non-fatal if fails)
    (ls -1A "$cert_source" 2>/dev/null || echo "<empty>") | sed 's/^/certs:install:source_entry /' >>"$LOG_FILE" 2>/dev/null || true

    # Create destination directory
    mkdir -p "$cert_dest"

    # Install .crt files with validation
    for cert_file in "$cert_source"/*.crt; do
        [ -f "$cert_file" ] || continue
        local basename=$(basename "$cert_file")

        # Validate certificate before installation
        if certctl_validate_cert "$cert_file"; then
            echo "Installing certificate: $basename"
            log_msg "certs:install:file action=install type=crt name=$basename"
            cp "$cert_file" "$cert_dest/"
            chmod 644 "$cert_dest/$basename"
            if command -v sha256sum >/dev/null 2>&1; then
                local fp
                fp=$(sha256sum "$cert_file" | awk '{print $1}')
                log_msg "certs:install:fingerprint type=crt name=$basename sha256=$fp"
            fi
            installed_count=$((installed_count + 1))
        else
            echo "WARNING: Skipping invalid certificate: $basename"
            log_msg "certs:install:file action=skip_invalid type=crt name=$basename"
            validation_failed=$((validation_failed + 1))
        fi
    done

    # Convert and install .pem files with validation
    for pem_file in "$cert_source"/*.pem; do
        [ -f "$pem_file" ] || continue
        local basename=$(basename "$pem_file" .pem)
        local crt_name="${basename}.crt"

        # Validate certificate before installation
        if certctl_validate_cert "$pem_file"; then
            echo "Converting and installing PEM certificate: $basename"
            log_msg "certs:install:file action=convert_install type=pem name=$basename"
            cp "$pem_file" "$cert_dest/$crt_name"
            chmod 644 "$cert_dest/$crt_name"
            if command -v sha256sum >/dev/null 2>&1; then
                local fp
                fp=$(sha256sum "$pem_file" | awk '{print $1}')
                log_msg "certs:install:fingerprint type=pem name=$basename sha256=$fp"
            fi
            installed_count=$((installed_count + 1))
        else
            echo "WARNING: Skipping invalid PEM certificate: $basename"
            log_msg "certs:install:file action=skip_invalid type=pem name=$basename"
            validation_failed=$((validation_failed + 1))
        fi
    done

    echo "Installed $installed_count custom certificate(s)"
    [ "$validation_failed" -gt 0 ] && echo "Skipped $validation_failed invalid certificate(s)"
    log_msg "certs:install:complete installed=$installed_count skipped_invalid=$validation_failed"

    return 0
}

# Update system certificate store
certctl_update_certs() {
    debug "Updating system certificate store"
    log_msg "certs:update:start"

    if [ "$EUID" -ne 0 ]; then
        echo "ERROR: Certificate management requires root permissions"
        return 1
    fi

    # Backup current bundle before update
    certctl_backup_bundle

    echo "Updating certificate store..."
    if update-ca-certificates >/dev/null 2>&1; then
        echo "Certificate store updated"
        log_msg "certs:update:store_updated"

        # Verify bundle integrity after update
        if ! certctl_verify_bundle; then
            echo "ERROR: Certificate bundle verification failed after update"
            log_msg "certs:update:verify_failed"
            echo "Consider restoring from backup in /var/backups/certctl/"
            return 1
        fi
    else
        echo "ERROR: Failed to update certificate store"
        log_msg "certs:update:failed"
        return 1
    fi
}

# Full certificate refresh
certctl_refresh_certs() {
    debug "Performing full certificate refresh"
    log_msg "certs:refresh:start"

    if certctl_clean_certs && certctl_install_certs && certctl_update_certs; then
        log_msg "certs:refresh:complete status=success"
    else
        log_msg "certs:refresh:complete status=failure"
        return 1
    fi
}

# Check for custom certificates
certctl_has_custom_certs() {
    [ -d "/usr/local/share/ca-certificates/custom" ] && \
    [ "$(find /usr/local/share/ca-certificates/custom -name '*.crt' 2>/dev/null | wc -l)" -gt 0 ]
}

# Show certificate status
certctl_certs_status() {
    echo "=== Certificate Status ==="
    echo "System certificate bundle: $CERT_BUNDLE"

    if certctl_has_custom_certs; then
        echo "Custom certificates: INSTALLED"
        echo "Custom certificate location: /usr/local/share/ca-certificates/custom/"
        echo "Custom certificates found:"
        find /usr/local/share/ca-certificates/custom -name '*.crt' 2>/dev/null | \
            xargs -I{} basename {} || echo "  (none readable)"
    else
        echo "Custom certificates: NOT INSTALLED"
    fi
}

# ============================================================================
# CLI INTERFACE (when executed directly)
# ============================================================================

certctl_cli() {
    case "${1:-help}" in
        probe|status)
            # Run probe and show result
            local probe_output=$(certctl_probe)
            eval "$probe_output"
            echo "Certificate status: $CERT_STATUS"
            echo "Successful probes: $CERT_SUCCESS_COUNT/$CERT_TOTAL_COUNT"
            echo ""
            echo "Environment variables to be set:"
            certctl_env "$probe_output"
            ;;

        env)
            # Just output environment variables
            certctl_env
            ;;

        load)
            # Load environment (for testing)
            certctl_load
            certctl_banner
            echo ""
            echo "Key variables:"
            echo "  CERT_STATUS=$CERT_STATUS"
            echo "  CURL_FLAGS=$CURL_FLAGS"
            [ -n "${UV_INSECURE_HOST:-}" ] && echo "  UV_INSECURE_HOST=$UV_INSECURE_HOST"
            ;;

        banner)
            # Show current status
            certctl_banner
            ;;

        install)
            # Self-install function
            certctl_install
            ;;

        certs-install)
            # Install certificates from /tmp/certs/
            certctl_install_certs
            ;;

        certs-clean)
            # Remove old custom certificates
            certctl_clean_certs
            ;;

        certs-update)
            # Update certificate store
            certctl_update_certs
            ;;

        certs-refresh)
            # Full certificate refresh
            certctl_refresh_certs
            ;;

        certs-status)
            # Show certificate status
            certctl_certs_status
            ;;

        certs-backup)
            # Create manual backup
            certctl_backup_bundle
            ;;

        certs-verify)
            # Verify certificate bundle
            certctl_verify_bundle
            ;;

        debug)
            # Debug mode probe
            CERTCTL_DEBUG=1 certctl_probe
            ;;

        help|--help|-h)
            cat << 'EOF'
certctl-safe - Complete Certificate Management for DevContainers

Usage: certctl-safe <command>

Commands:
  probe, status    Run certificate probe and show environment
  env             Output environment variables
  load            Load environment (for testing)
  banner          Show status banner
  install         Install to system
  certs-install   Install certificates from /tmp/certs/
  certs-clean     Remove old custom certificates
  certs-update    Update system certificate store
  certs-refresh   Full certificate refresh (clean + install + update)
  certs-status    Show certificate installation status
  certs-backup    Create manual backup of certificate bundle
  certs-verify    Verify certificate bundle integrity
  debug           Run probe with debug output
  help            Show this help

Environment Variables Managed:
  Certificate Status:
    CERT_STATUS, CERT_SUCCESS_COUNT, CERT_FAIL_COUNT, CERT_TOTAL_COUNT

  Certificate Locations (always set):
    SSL_CERT_DIR, SSL_CERT_FILE, CURL_CA_BUNDLE, REQUESTS_CA_BUNDLE,
    AWS_CA_BUNDLE, NODE_EXTRA_CA_CERTS, PIP_CERT, BUNDLE_SSL_CA_CERT

  Mode-Specific:
    SECURE: CURL_FLAGS, UV_NATIVE_TLS
    INSECURE: CERT_INSECURE, NODE_TLS_REJECT_UNAUTHORIZED, GIT_SSL_NO_VERIFY,
              UV_INSECURE, UV_INSECURE_HOST, PIP_TRUSTED_HOST, NPM_CONFIG_STRICT_SSL

Control Variables:
  CERTCTL_DEBUG=1                   Enable debug output
  CERTCTL_TARGETS="urls"            Override probe targets (space-separated)
  CERTCTL_PROBE_TIMEOUT=N           Timeout per URL (seconds, default: 10)
  CERTCTL_TOTAL_TIMEOUT=N           Total timeout (seconds, default: 10)
  CERTCTL_INSECURE_HOSTS="hosts"    Override insecure hosts list
  CERTCTL_APPEND_INSECURE_HOSTS="h" Append to insecure hosts list

Installation:
  sudo ./certctl-safe.sh install

Examples:
  # Check status
  certctl status

  # Debug mode
  CERTCTL_DEBUG=1 certctl probe

  # Custom targets
  CERTCTL_TARGETS="https://github.com https://pypi.org" certctl probe

  # Quick timeout for fast startup
  CERTCTL_TOTAL_TIMEOUT=1 certctl probe

EOF
            ;;

        *)
            echo "Unknown command: $1"
            echo "Run 'certctl-safe help' for usage"
            exit 1
            ;;
    esac
}

# ============================================================================
# SELF-INSTALLER
# ============================================================================

certctl_install() {
    echo "Installing certctl-safe..."

    # Check permissions
    if [ "$EUID" -ne 0 ]; then
        echo "ERROR: Installation requires root permissions"
        echo "Please run: sudo $0 install"
        exit 1
    fi

    # Install main script
    echo "Installing script to /usr/local/bin/certctl..."
    cp "$0" /usr/local/bin/certctl
    chmod 755 /usr/local/bin/certctl

    # Create profile.d integration
    echo "Creating shell integration..."
    cat > /etc/profile.d/certctl-env.sh << 'EOF'
#!/bin/bash
# Certificate environment loader - safe for shell initialization
# This file is auto-generated by certctl-safe installer

# Only load in interactive shells
if [[ $- == *i* ]] && [ -x /usr/local/bin/certctl ]; then
    # Source the functions (safe - no set -e)
    source /usr/local/bin/certctl

    # Load environment with timeout (won't block shell)
    certctl_load 2>/dev/null || true

    # Optional: Show banner in new terminals
    # Uncomment if desired:
    # certctl_banner 2>/dev/null || true
fi
EOF

    chmod 644 /etc/profile.d/certctl-env.sh

    echo "✅ Installation complete!"
    echo ""
    echo "To test: certctl status"
    echo "For new shells: source /etc/profile.d/certctl-env.sh"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Detect if script is being sourced or executed
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Being executed - run CLI
    certctl_cli "$@"
else
    # Being sourced - just load functions
    debug "certctl-safe sourced, functions available"
fi