#!/bin/bash
# Complete SSL Setup for api.coinjecture.com
# This script will help you get SSH access and SSL certificate

set -euo pipefail

DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEp9oX7sldpli9HVqt+/CsRR49npRqDX92hsB1eC7oyX coinjecture-droplet-access"

echo "🔐 Complete SSL Setup for api.coinjecture.com"
echo "============================================="

echo "📋 SSH Public Key to add to droplet:"
echo "$PUBLIC_KEY"
echo ""

echo "🔧 Step 1: Add SSH Key to Droplet"
echo "=================================="
echo "You need to add the SSH key above to the droplet's authorized_keys file."
echo ""
echo "Option A - If you have console access to the droplet:"
echo "1. Log into the droplet console"
echo "2. Run these commands:"
echo "   mkdir -p ~/.ssh"
echo "   chmod 700 ~/.ssh"
echo "   echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "Option B - If you have another way to access the droplet:"
echo "Add the key above to ~/.ssh/authorized_keys on the droplet"
echo ""

echo "🧪 Step 2: Test SSH Connection"
echo "=============================="
echo "After adding the key, test the connection:"
echo "ssh -i $SSH_KEY coinjecture@$DROPLET_IP 'echo SSH connection successful'"
echo ""

echo "🔐 Step 3: Get SSL Certificate"
echo "=============================="
echo "Once SSH works, run this command to get the SSL certificate:"
echo "ssh -i $SSH_KEY coinjecture@$DROPLET_IP 'sudo ./setup_ssl_manual.sh'"
echo ""

echo "📤 Step 4: Copy SSL Setup Script to Droplet"
echo "==========================================="
echo "First, copy the SSL setup script to the droplet:"
echo "scp -i $SSH_KEY scripts/setup_ssl_manual.sh coinjecture@$DROPLET_IP:/home/coinjecture/"
echo ""

echo "🎯 Expected Result"
echo "=================="
echo "After completing these steps:"
echo "- https://api.coinjecture.com will work with valid SSL certificate"
echo "- Mobile devices will be able to access the API"
echo "- All security headers will be configured"
echo ""

echo "🧪 Step 5: Test the API"
echo "======================"
echo "After SSL is set up, test with:"
echo "curl https://api.coinjecture.com/health"
echo "python3 scripts/test_production_api.py"
