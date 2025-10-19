#!/bin/bash
# Manual SSL Setup for api.coinjecture.com
# Run this on the droplet after SSH access is configured

set -euo pipefail

echo "🔐 Setting up SSL certificate for api.coinjecture.com"
echo "=================================================="

# Install certbot if not already installed
echo "📦 Installing Certbot..."
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Stop any services that might be using port 80
echo "🛑 Stopping conflicting services..."
sudo systemctl stop apache2 2>/dev/null || true

# Get SSL certificate
echo "🔐 Obtaining SSL certificate for api.coinjecture.com..."
sudo certbot certonly --standalone -d api.coinjecture.com --non-interactive --agree-tos --email admin@coinjecture.com

# Update Nginx configuration to use the new certificate
echo "⚙️  Updating Nginx configuration..."
sudo tee /etc/nginx/sites-available/coinjecture-api << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name api.coinjecture.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.coinjecture.com;
    
    # TLS Configuration
    ssl_certificate /etc/letsencrypt/live/api.coinjecture.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.coinjecture.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # CORS Headers
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    
    # Handle preflight requests
    location / {
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type "text/plain; charset=utf-8";
            add_header Content-Length 0;
            return 204;
        }
        
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# Enable the site
echo "🔗 Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/coinjecture-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Reload Nginx
echo "🔄 Reloading Nginx..."
sudo systemctl reload nginx

# Setup certificate auto-renewal
echo "⏰ Setting up certificate auto-renewal..."
echo "0 0,12 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab

# Test certificate renewal
echo "🧪 Testing certificate renewal..."
sudo certbot renew --dry-run

# Test the setup
echo "🧪 Testing API endpoint..."
sleep 5
curl -I https://api.coinjecture.com/health || echo "⚠️  API not yet accessible (may need a moment to propagate)"

echo "✅ SSL setup completed!"
echo "🌐 API should now be accessible at: https://api.coinjecture.com"
echo "🔐 SSL certificate is valid for api.coinjecture.com"
