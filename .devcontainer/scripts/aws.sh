#!/bin/bash
# AWS credentials verification and setup

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

verify_aws_credentials() {
    log_step "Checking AWS credentials configuration..."
    
    # Check if AWS credentials directory exists and has contents
    if [ -d "$HOME/.aws" ] && [ "$(ls -A "$HOME/.aws" 2>/dev/null)" ]; then
        log_info "AWS credentials directory found"
        
        # Test if AWS CLI is available
        if ! command -v aws >/dev/null 2>&1; then
            log_warning "AWS CLI not installed - installing..."
            curl -sSk "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
            unzip -q /tmp/awscliv2.zip -d /tmp/
            sudo /tmp/aws/install
            rm -rf /tmp/aws /tmp/awscliv2.zip
            log_success "AWS CLI installed"
        fi
        
        # Test credentials validity
        if aws sts get-caller-identity >/dev/null 2>&1; then
            AWS_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null)
            AWS_USER=$(aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null | rev | cut -d'/' -f1 | rev)
            AWS_REGION=$(aws configure get region 2>/dev/null || echo "not-configured")
            
            log_success "AWS credentials are valid"
            log_info "Connected to AWS Account: $AWS_ACCOUNT"
            log_info "User: $AWS_USER"
            log_info "Region: $AWS_REGION"
            
            export AWS_MOUNTED=true
            export AWS_ACCOUNT="$AWS_ACCOUNT"
            export AWS_USER="$AWS_USER"
            export AWS_REGION="$AWS_REGION"
            
        else
            log_warning "AWS credentials found but not working - check your configuration"
            log_info "Try running 'aws configure' to set up credentials"
            export AWS_MOUNTED=false
        fi
        
    else
        log_info "No AWS credentials found in $HOME/.aws"
        log_info "If you need AWS access, mount your ~/.aws directory or run 'aws configure'"
        export AWS_MOUNTED=false
    fi
}

# Run AWS verification if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_step "Starting AWS credentials verification..."
    verify_aws_credentials
    
    if [ "$AWS_MOUNTED" = true ]; then
        log_success "AWS setup complete - credentials verified"
    else
        log_info "AWS setup complete - no valid credentials found"
    fi
fi