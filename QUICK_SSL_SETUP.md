# Quick SSL Setup for api.coinjecture.com

## Current Status ✅
- DNS A record configured: `api.coinjecture.com` → `167.172.213.70`
- Nginx is running and redirecting HTTP to HTTPS
- Need SSL certificate for `api.coinjecture.com`

## Next Steps

### 1. Copy SSL Setup Script to Droplet
```bash
scp -i ~/.ssh/coinjecture_droplet_key scripts/setup_ssl_manual.sh coinjecture@167.172.213.70:/home/coinjecture/
```

### 2. SSH to Droplet and Run Setup
```bash
ssh -i ~/.ssh/coinjecture_droplet_key coinjecture@167.172.213.70
cd /home/coinjecture
chmod +x setup_ssl_manual.sh
sudo ./setup_ssl_manual.sh
```

### 3. Test the API
After the script completes, test:
```bash
curl https://api.coinjecture.com/health
```

## What the Script Does
1. Installs Certbot
2. Gets SSL certificate for `api.coinjecture.com`
3. Updates Nginx configuration
4. Sets up auto-renewal
5. Tests the setup

## Expected Result
- `https://api.coinjecture.com` will work with valid SSL certificate
- Mobile devices will be able to access the API
- All security headers will be configured

## If SSH Access Issues
If you can't SSH, you can:
1. Use DigitalOcean console to access the droplet
2. Copy the script content manually
3. Run the commands step by step

The script is ready at: `scripts/setup_ssl_manual.sh`
