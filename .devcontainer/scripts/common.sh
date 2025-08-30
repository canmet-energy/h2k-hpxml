#!/bin/bash
# Common utilities and logging functions for devcontainer setup scripts

# Exit on any error
set -e

# Logging functions with emojis for better visibility
log_info() { echo "ℹ️ $1"; }
log_success() { echo "✅ $1"; }
log_warning() { echo "⚠️ $1"; }
log_step() { echo "🚀 $1"; }
log_error() { echo "❌ $1" >&2; }

# Check if running with required privileges
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        log_error "This script requires sudo privileges"
        exit 1
    fi
}

# Export functions for use in other scripts
export -f log_info log_success log_warning log_step log_error check_sudo