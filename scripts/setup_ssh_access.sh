#!/bin/bash
# Setup SSH access to droplet

set -euo pipefail

DROPLET_IP="167.172.213.70"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGmC1cd/jiQn/0B4raxJB59fNJACLhWv26ZfeVEMMQ/C coinjecture-droplet-access"

echo "🔑 Setting up SSH access to droplet"
echo "=================================="

# Try to connect with password authentication first to add the key
echo "📤 Adding SSH public key to droplet..."
ssh -o StrictHostKeyChecking=no coinjecture@$DROPLET_IP << EOF
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo "✅ SSH key added successfully"
EOF

echo "🧪 Testing SSH connection with key..."
ssh -i ~/.ssh/coinjecture_droplet_key -o StrictHostKeyChecking=no coinjecture@$DROPLET_IP "echo 'SSH connection successful'"

echo "✅ SSH access configured successfully!"
