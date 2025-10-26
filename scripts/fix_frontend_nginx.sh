#!/bin/bash
# Fix Nginx configuration to serve frontend properly

set -euo pipefail

echo "🔧 Fixing Nginx configuration for frontend"
echo "=========================================="

# Update Nginx configuration to serve frontend
tee /etc/nginx/sites-available/coinjecture-api << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name coinjecture.com api.coinjecture.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name coinjecture.com api.coinjecture.com;
    
    # TLS Configuration
    ssl_certificate /etc/letsencrypt/live/coinjecture.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/coinjecture.com/privkey.pem;
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
    
    # Serve static files for frontend
    location / {
        root /home/coinjecture/COINjecture/web;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API endpoints
    location /v1/ {
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
    
    # Health endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Test and reload Nginx
echo "🧪 Testing Nginx configuration..."
nginx -t

echo "🔄 Reloading Nginx..."
systemctl reload nginx

echo "✅ Frontend configuration updated!"
echo "🌐 Frontend should now be accessible at:"
echo "   - https://coinjecture.com"
echo "   - https://api.coinjecture.com"
echo "🔧 API endpoints still work at:"
echo "   - https://coinjecture.com/v1/..."
echo "   - https://api.coinjecture.com/v1/..."
