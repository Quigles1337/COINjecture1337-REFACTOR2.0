#!/usr/bin/env python3
"""
Fix CORS Headers Issue
The API server is sending duplicate CORS headers causing browser rejection.
"""

import os
import sys

def fix_cors_headers():
    """Fix the CORS headers configuration to prevent duplicates."""
    
    print("🔧 Fixing CORS Headers Issue")
    print("============================")
    
    # Read the current faucet_server.py
    faucet_server_path = "src/api/faucet_server.py"
    
    if not os.path.exists(faucet_server_path):
        print(f"❌ File not found: {faucet_server_path}")
        return False
    
    with open(faucet_server_path, 'r') as f:
        content = f.read()
    
    # Check if CORS is already configured properly
    if "CORS(self.app, origins=" in content:
        print("✅ CORS is already properly configured")
        return True
    
    # Fix the CORS configuration
    old_cors = "CORS(self.app)"
    new_cors = '''CORS(self.app, 
            origins=["https://coinjecture.com", "https://api.coinjecture.com"],
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization", "X-User-ID", "X-Timestamp", "X-Signature"],
            supports_credentials=True)'''
    
    if old_cors in content:
        print("🔧 Updating CORS configuration...")
        content = content.replace(old_cors, new_cors)
        
        # Write the updated content
        with open(faucet_server_path, 'w') as f:
            f.write(content)
        
        print("✅ CORS configuration updated")
        print("   - Specific origins: https://coinjecture.com, https://api.coinjecture.com")
        print("   - Methods: GET, POST, PUT, DELETE, OPTIONS")
        print("   - Headers: Content-Type, Authorization, X-User-ID, X-Timestamp, X-Signature")
        print("   - Credentials: supported")
        
        return True
    else:
        print("❌ CORS configuration not found in expected format")
        return False

def create_nginx_cors_fix():
    """Create a script to fix Nginx CORS configuration."""
    
    nginx_fix_script = """#!/bin/bash

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
"""
    
    with open("scripts/fix_nginx_cors.sh", "w") as f:
        f.write(nginx_fix_script)
    
    os.chmod("scripts/fix_nginx_cors.sh", 0o755)
    print("✅ Created Nginx CORS fix script: scripts/fix_nginx_cors.sh")

def main():
    """Main function."""
    print("🚀 Starting CORS Headers Fix")
    print("============================")
    
    # Fix Flask CORS configuration
    if fix_cors_headers():
        print("✅ Flask CORS configuration fixed")
    else:
        print("❌ Failed to fix Flask CORS configuration")
        return False
    
    # Create Nginx fix script
    create_nginx_cors_fix()
    
    print("")
    print("🎯 Next Steps:")
    print("1. Deploy the updated faucet_server.py to the droplet")
    print("2. Run the Nginx CORS fix script on the droplet:")
    print("   ./scripts/fix_nginx_cors.sh")
    print("3. Restart the API service")
    print("4. Test the frontend")
    
    print("")
    print("✅ CORS headers fix completed!")
    return True

if __name__ == "__main__":
    main()
