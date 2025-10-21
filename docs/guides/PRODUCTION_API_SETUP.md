# Production API Setup Guide

## Overview
This guide will help you set up the production API at `https://api.coinjecture.com` with TLS certificate and IPv6 support.

## Prerequisites
- Access to the DigitalOcean droplet (167.172.213.70)
- Domain name `api.coinjecture.com` configured in your DNS provider
- SSH access to the droplet

## Step 1: DNS Configuration

### Configure DNS Records
In your DNS provider (e.g., Cloudflare, Route53):

1. **A Record**: `api.coinjecture.com` → `167.172.213.70`
2. **AAAA Record**: `api.coinjecture.com` → `[IPv6 address]` (if available)
3. Set TTL to 300 seconds for quick propagation

### Verify DNS
```bash
dig api.coinjecture.com
nslookup api.coinjecture.com
```

## Step 2: SSH Access Setup

### Add SSH Key to Droplet
1. Connect to the droplet using your current method
2. Add the SSH public key to authorized_keys:

```bash
# On the droplet
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGmC1cd/jiQn/0B4raxJB59fNJACLhWv26ZfeVEMMQ/C coinjecture-droplet-access" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Step 3: Install Required Software

### Connect to Droplet
```bash
ssh -i ~/.ssh/coinjecture_droplet_key coinjecture@167.172.213.70
```

### Install Nginx and Certbot
```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

## Step 4: Configure Nginx

### Create Nginx Configuration
```bash
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
```

### Enable the Site
```bash
sudo ln -sf /etc/nginx/sites-available/coinjecture-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Step 5: Obtain SSL Certificate

### Get Let's Encrypt Certificate
```bash
sudo certbot certonly --standalone -d api.coinjecture.com --non-interactive --agree-tos --email admin@coinjecture.com
```

### Test Certificate
```bash
sudo certbot renew --dry-run
```

## Step 6: Configure Firewall

### Allow HTTP/HTTPS Traffic
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable
```

## Step 7: Setup Auto-Renewal

### Add Cron Job
```bash
echo "0 0,12 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab
```

## Step 8: Test the Setup

### Test DNS Resolution
```bash
dig api.coinjecture.com
```

### Test HTTP Redirect
```bash
curl -I http://api.coinjecture.com
```

### Test HTTPS
```bash
curl -I https://api.coinjecture.com/health
```

### Test IPv6 (if configured)
```bash
curl -6 https://api.coinjecture.com/health
```

## Step 9: Update Application Code

### Update Web Interface
The web interface has already been updated to use `https://api.coinjecture.com`

### Update CLI
The CLI has already been updated to use `https://api.coinjecture.com`

### Deploy Updated Code
```bash
# Copy updated files to droplet
scp -i ~/.ssh/coinjecture_droplet_key web/app.js coinjecture@167.172.213.70:/home/coinjecture/COINjecture/web/
scp -i ~/.ssh/coinjecture_droplet_key src/cli.py coinjecture@167.172.213.70:/home/coinjecture/COINjecture/src/
scp -i ~/.ssh/coinjecture_droplet_key config/miner_config.json coinjecture@167.172.213.70:/home/coinjecture/COINjecture/config/
```

## Step 10: Deploy to S3

### Update Web Interface on S3
```bash
cd web
./deploy-s3.sh
```

## Step 11: Clear CloudFront Cache

### Invalidate CloudFront
```bash
python3 scripts/clear_cloudfront_cache.py
```

## Verification Checklist

- [ ] DNS resolves: `dig api.coinjecture.com`
- [ ] HTTP redirects to HTTPS: `curl -I http://api.coinjecture.com`
- [ ] HTTPS works: `curl https://api.coinjecture.com/health`
- [ ] TLS certificate valid: `openssl s_client -connect api.coinjecture.com:443`
- [ ] CORS headers present
- [ ] Mobile browser can access API
- [ ] Web interface works with new endpoint
- [ ] CLI commands work with new endpoint

## Troubleshooting

### If DNS doesn't resolve
- Check DNS configuration in your provider
- Wait for DNS propagation (up to 24 hours)
- Use `dig` to verify DNS records

### If certificate fails
- Ensure DNS is resolving correctly
- Check that port 80 is accessible
- Verify domain ownership

### If Nginx fails to start
- Check configuration: `sudo nginx -t`
- Check logs: `sudo journalctl -u nginx`
- Ensure no other services are using ports 80/443

### If API doesn't respond
- Check that the Flask API is running on port 5000
- Verify Nginx proxy configuration
- Check firewall settings

## Expected Outcome

After completing this setup:

- API accessible at `https://api.coinjecture.com` (port 443)
- Valid TLS certificate from Let's Encrypt
- IPv6 support enabled (if configured)
- Mobile OSes can access API without issues
- All documentation updated with new endpoint
- HTTP automatically redirects to HTTPS
- Proper security headers configured
