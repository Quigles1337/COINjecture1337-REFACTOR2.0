#!/bin/bash
# Get SSL certificate for api.coinjecture.com

set -euo pipefail

DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"

echo "🔐 Getting SSL certificate for api.coinjecture.com"
echo "================================================="

# Test SSH connection first
echo "🧪 Testing SSH connection..."
ssh -i $SSH_KEY -o ConnectTimeout=10 coinjecture@$DROPLET_IP "echo 'SSH connection successful'" || {
    echo "❌ SSH connection failed. Please add the SSH key to the droplet first."
    echo "SSH key to add:"
    cat ~/.ssh/coinjecture_droplet_key.pub
    exit 1
}

echo "✅ SSH connection successful"

# Get SSL certificate
echo "🔐 Obtaining SSL certificate..."
ssh -i $SSH_KEY coinjecture@$DROPLET_IP << 'EOF'
sudo certbot certonly --standalone -d api.coinjecture.com --non-interactive --agree-tos --email admin@coinjecture.com
EOF

echo "✅ SSL certificate obtained successfully!"
echo "🌐 API should now be accessible at: https://api.coinjecture.com"
