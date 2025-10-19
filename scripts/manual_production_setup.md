# Manual Production API Setup

Since SSH access is not working, we need to manually configure the production API setup.

## Steps to Complete:

### 1. DNS Configuration
Configure the following DNS records with your DNS provider:

**A Record:**
- Name: `api.coinjecture.com`
- Value: `167.172.213.70`
- TTL: 300

**AAAA Record (if IPv6 is available):**
- Name: `api.coinjecture.com` 
- Value: `[IPv6 address of droplet]`
- TTL: 300

### 2. Droplet Configuration
SSH into the droplet and run these commands:

```bash
# Update system
sudo apt-get update

# Install Nginx and Certbot
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/coinjecture-api > /dev/null << 'EOF'
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
sudo ln -sf /etc/nginx/sites-available/coinjecture-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Stop conflicting services
sudo systemctl stop apache2 2>/dev/null || true

# Obtain SSL certificate
sudo certbot certonly --standalone -d api.coinjecture.com --non-interactive --agree-tos --email admin@coinjecture.com

# Test Nginx configuration again
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Setup certificate auto-renewal
echo "0 0,12 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab

# Test certificate renewal
sudo certbot renew --dry-run

# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable
```

### 3. Update Web Interface
Update the web interface files on the droplet:

```bash
# Update app.js
cd /home/coinjecture/COINjecture/web
sudo nano app.js

# Change this line:
# this.apiBase = window.location.hostname === '167.172.213.70' ? '' : 'https://167.172.213.70';
# To:
# this.apiBase = 'https://api.coinjecture.com';
```

### 4. Update CLI
Update the CLI files on the droplet:

```bash
# Update cli.py
cd /home/coinjecture/COINjecture/src
sudo nano cli.py

# Replace all instances of:
# http://167.172.213.70:5000
# With:
# https://api.coinjecture.com
```

### 5. Deploy Updated Web Interface to S3
```bash
cd /home/coinjecture/COINjecture/web
./deploy-s3.sh
```

### 6. Test the Setup
```bash
# Test DNS resolution
dig api.coinjecture.com

# Test HTTP redirect
curl -I http://api.coinjecture.com/health

# Test HTTPS
curl -I https://api.coinjecture.com/health

# Test API endpoints
curl https://api.coinjecture.com/v1/data/block/latest
```

### 7. Clear CloudFront Cache
```bash
cd /home/coinjecture/COINjecture
python3 scripts/clear_cloudfront_cache.py
```

## Expected Results:
- ✅ API accessible at `https://api.coinjecture.com`
- ✅ Valid TLS certificate from Let's Encrypt
- ✅ HTTP redirects to HTTPS
- ✅ Mobile OSes can access API without issues
- ✅ All documentation updated with new endpoint
