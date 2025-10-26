#!/bin/bash

# Fix Nginx CORS Configuration
# Remove duplicate CORS headers from Nginx

echo "🔧 Fixing Nginx CORS Configuration"
echo "=================================="

# Check if Nginx config exists
if [ ! -f "/etc/nginx/sites-available/coinjecture-api" ]; then
    echo "❌ Nginx config not found: /etc/nginx/sites-available/coinjecture-api"
    exit 1
fi

# Backup the current config
sudo cp /etc/nginx/sites-available/coinjecture-api /etc/nginx/sites-available/coinjecture-api.backup

# Remove any existing CORS headers from Nginx
sudo sed -i '/add_header Access-Control-Allow-Origin/d' /etc/nginx/sites-available/coinjecture-api
sudo sed -i '/add_header Access-Control-Allow-Methods/d' /etc/nginx/sites-available/coinjecture-api
sudo sed -i '/add_header Access-Control-Allow-Headers/d' /etc/nginx/sites-available/coinjecture-api

# Test Nginx configuration
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    
    # Reload Nginx
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
    
    echo ""
    echo "🎯 CORS headers are now handled by the Flask application only"
    echo "   - No duplicate headers from Nginx"
    echo "   - Flask-CORS handles all CORS requirements"
    
else
    echo "❌ Nginx configuration test failed"
    echo "Restoring backup..."
    sudo cp /etc/nginx/sites-available/coinjecture-api.backup /etc/nginx/sites-available/coinjecture-api
    exit 1
fi

echo ""
echo "🧪 Test the API now:"
echo "   curl -H 'Origin: https://coinjecture.com' https://api.coinjecture.com/v1/data/block/latest"
