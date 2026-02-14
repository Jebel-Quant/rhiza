#!/bin/bash
# Rhiza shell initialization
# Source this file in your .bashrc or .zshrc to enable auto-activation features
#
# Note: This script is designed for bash and zsh. For other shells, you may need
# to manually run `make install` and `source .venv/bin/activate`.
#
# Usage:
#   echo 'source /path/to/rhiza/.rhiza/shell-init.sh' >> ~/.bashrc
#   # or for zsh:
#   echo 'source /path/to/rhiza/.rhiza/shell-init.sh' >> ~/.zshrc
#
# Then use 'rhiza-install' instead of 'make install' to get auto-activation

# Function to run make install and auto-activate the venv
rhiza-install() {
    # Suppress the activation message since we're auto-activating
    RHIZA_AUTO_ACTIVATE_VENV=false make install
    
    local exit_code=$?
    
    # Only activate if make install succeeded
    if [ $exit_code -eq 0 ]; then
        if [ -f .venv/bin/activate ]; then
            echo ""
            echo -e "\033[32m[SUCCESS] Installation complete! Auto-activating virtual environment...\033[0m"
            echo ""
            source .venv/bin/activate
        else
            echo ""
            echo -e "\033[33m[WARN] Virtual environment not found at .venv/bin/activate\033[0m"
            echo ""
        fi
    fi
    
    return $exit_code
}

# Export the function for bash (zsh doesn't need this)
if [ -n "$BASH_VERSION" ]; then
    export -f rhiza-install
fi
