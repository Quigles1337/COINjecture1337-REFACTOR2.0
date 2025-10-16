#!/bin/bash

# Check COINjecture Faucet API droplet status
# Based on: https://docs.digitalocean.com/reference/api/

TOKEN="${DO_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "❌ Error: DO_TOKEN environment variable not set"
    exit 1
fi

echo "🔍 Checking COINjecture Faucet API droplet status..."

# Get droplet information
DROPLET_INFO=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.digitalocean.com/v2/droplets" | \
    jq '.droplets[] | select(.name=="coinjecture-faucet-api")')

if [ "$DROPLET_INFO" = "null" ] || [ -z "$DROPLET_INFO" ]; then
    echo "❌ Droplet 'coinjecture-faucet-api' not found"
    echo "Available droplets:"
    curl -s -H "Authorization: Bearer $TOKEN" \
        "https://api.digitalocean.com/v2/droplets" | \
        jq -r '.droplets[] | "  - \(.name) (\(.status))"'
    exit 1
fi

# Extract droplet details
NAME=$(echo "$DROPLET_INFO" | jq -r '.name')
STATUS=$(echo "$DROPLET_INFO" | jq -r '.status')
IPV4=$(echo "$DROPLET_INFO" | jq -r '.networks.v4[] | select(.type=="public") | .ip_address')
IPV6=$(echo "$DROPLET_INFO" | jq -r '.networks.v6[] | select(.type=="public") | .ip_address')
REGION=$(echo "$DROPLET_INFO" | jq -r '.region.name')
SIZE=$(echo "$DROPLET_INFO" | jq -r '.size_slug')

echo "✅ Droplet Found!"
echo "📋 Droplet Details:"
echo "   Name: $NAME"
echo "   Status: $STATUS"
echo "   IPv4: $IPV4"
echo "   IPv6: $IPV6"
echo "   Region: $REGION"
echo "   Size: $SIZE"

if [ "$STATUS" = "active" ]; then
    echo ""
    echo "🚀 Droplet is ready for deployment!"
    echo "📡 API Endpoints will be available at:"
    echo "   Health: http://$IPV4/health"
    echo "   Latest Block: http://$IPV4/v1/data/block/latest"
    echo ""
    echo "🔧 To deploy the API, run:"
    echo "   ./deploy.sh $IPV4"
elif [ "$STATUS" = "new" ]; then
    echo ""
    echo "⏳ Droplet is still being created... Please wait a few more minutes."
    echo "🔄 Run this script again to check status."
else
    echo ""
    echo "⚠️  Droplet status: $STATUS"
    echo "🔄 Run this script again to check status."
fi
