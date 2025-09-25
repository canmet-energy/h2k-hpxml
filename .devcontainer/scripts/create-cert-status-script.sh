#!/bin/bash
# Script to create the certificate status notification system
# This script creates the show-cert-status command and sets up user notifications

set -euo pipefail

# Create the certificate status display script
create_show_cert_status_script() {
    local script_path="/usr/local/bin/show-cert-status"
    
    cat > "$script_path" << 'EOF'
#!/bin/bash
# Display certificate status information for the container

if [ -f /etc/container-cert-status ]; then
    STATUS=$(cat /etc/container-cert-status)
    case "$STATUS" in
        "INSECURE")
            echo "🔒 Certificate Status: This container was built with INSECURE curl settings"
            echo "   This may indicate a corporate network with TLS interception"
            echo "   Security: Downloads were made without certificate verification"
            ;;
        "SECURE_CUSTOM")
            echo "🔐 Certificate Status: Container built with CUSTOM certificates ✅"
            echo "   Custom certificate files were provided and installed"
            echo "   All tools configured to use system certificate store"
            ;;
        "SECURE")
            echo "🔒 Certificate Status: Container built with secure certificate validation ✅"
            ;;
        *)
            echo "⚠️  Certificate Status: Unknown status '$STATUS'"
            ;;
    esac
else
    echo "ℹ️  Certificate Status: No certificate status information available"
fi
EOF

    chmod +x "$script_path"
    echo "Created certificate status script at $script_path"
}

# Set up automatic certificate status display for a user
setup_user_cert_display() {
    local username="${1:-}"
    
    if [ -z "$username" ]; then
        echo "Error: Username required for setup_user_cert_display"
        return 1
    fi
    
    local user_home
    user_home=$(eval echo "~$username")
    
    if [ ! -d "$user_home" ]; then
        echo "Warning: Home directory $user_home does not exist for user $username"
        return 1
    fi
    
    local bashrc_path="$user_home/.bashrc"
    
    # Check if certificate status display is already configured
    if grep -q "show-cert-status" "$bashrc_path" 2>/dev/null; then
        echo "Certificate status display already configured for user $username"
        return 0
    fi
    
    # Add certificate status display to bashrc
    cat >> "$bashrc_path" << 'EOF'

# Show certificate status on login
if [ -t 1 ] && [ -f /usr/local/bin/show-cert-status ]; then
    /usr/local/bin/show-cert-status
fi
EOF

    echo "Configured certificate status display for user $username"
}

# Main execution
main() {
    echo "Setting up certificate status notification system..."
    
    # Create the main status script
    create_show_cert_status_script
    
    # Set up user displays based on arguments or detect users
    if [ $# -gt 0 ]; then
        # Use provided usernames
        for username in "$@"; do
            setup_user_cert_display "$username"
        done
    else
        # Auto-detect common users
        for username in vscode appuser root; do
            if id "$username" &>/dev/null; then
                setup_user_cert_display "$username"
            fi
        done
    fi
    
    echo "Certificate status notification system setup complete!"
}

# Run main function with all arguments
main "$@"