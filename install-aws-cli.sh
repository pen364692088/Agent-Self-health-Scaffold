#!/bin/bash

# AWS CLI installer script for local user installation
set -e

echo "Installing AWS CLI v2 to ~/.local/aws-cli..."

# Create directories
mkdir -p ~/.local/aws-cli
mkdir -p ~/.local/bin

# Download AWS CLI v2
if [ ! -f "awscliv2.zip" ]; then
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
fi

# Extract
unzip -q awscliv2.zip

# Install to local directory with overwrite flag
./aws/install --bin-dir ~/.local/bin --install-dir ~/.local/aws-cli --update

# Update PATH
if ! grep -q '~/.local/aws-cli/bin' ~/.bashrc; then
    echo 'export PATH="$HOME/.local/aws-cli/bin:$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# Clean up
rm -rf aws
rm -f awscliv2.zip

echo "AWS CLI installed successfully!"
echo "Run 'source ~/.bashrc' or restart your shell to use it."