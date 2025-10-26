#!/usr/bin/env bash
set -euo pipefail

# COINjecture Web Interface Deployment to DigitalOcean Droplet
# Deploys the web CLI interface to the live network

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
WEB_PORT="8080"
LOCAL_PROJECT_DIR="$(pwd)"

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                                            ║"
    echo "║   ██████╗ ██████╗ ██╗███╗   ██╗     ██╗███████╗ ██████╗████████╗██╗   ██╗██████╗ ███████╗  ║"
    echo "║  ██╔════╝██╔═══██╗██║████╗  ██║     ██║██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝  ║"
    echo "║  ██║     ██║   ██║██║██╔██╗ ██║     ██║█████╗  ██║        ██║   ██║   ██║██████╔╝█████╗    ║"
    echo "║  ██║     ██║   ██║██║██║╚██╗██║██   ██║██╔══╝  ██║        ██║   ██║   ██║██╔══██╗██╔══╝    ║"
    echo "║  ╚██████╗╚██████╔╝██║██║ ╚████║╚█████╔╝███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║███████╗  ║"
    echo "║   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝  ║"
    echo "║                                                                                            ║"
    echo "║         🌐 Web CLI Interface Deployment to DigitalOcean                                     ║"
    echo "║         🚀 Deploy to: $DROPLET_IP:$WEB_PORT ║"
    echo "║         🔗 Mobile-optimized web interface for COINjecture                                  ║"
    echo "║                                                                                            ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

check_ssh_connection() {
    log "Checking SSH connection to droplet..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes $DROPLET_USER@$DROPLET_IP "echo 'SSH connection successful'" 2>/dev/null; then
        log "✅ SSH connection to $DROPLET_IP successful"
        return 0
    else
        error "❌ SSH connection to $DROPLET_IP failed"
        error "Please ensure:"
        error "1. SSH key is configured for $DROPLET_USER@$DROPLET_IP"
        error "2. Droplet is running and accessible"
        error "3. SSH service is running on the droplet"
        return 1
    fi
}

deploy_web_files() {
    log "Deploying web interface files to droplet..."
    
    # Create web directory on droplet
    ssh $DROPLET_USER@$DROPLET_IP "mkdir -p /opt/coinjecture-web"
    
    # Copy web files
    log "Copying web interface files..."
    scp web/index.html $DROPLET_USER@$DROPLET_IP:/opt/coinjecture-web/
    scp web/style.css $DROPLET_USER@$DROPLET_IP:/opt/coinjecture-web/
    scp web/app.js $DROPLET_USER@$DROPLET_IP:/opt/coinjecture-web/
    
    log "✅ Web interface files deployed"
}

setup_nginx() {
    log "Setting up nginx for web interface..."
    
    ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
        # Install nginx if not present
        if ! command -v nginx &> /dev/null; then
            echo "Installing nginx..."
            apt-get update
            apt-get install -y nginx
        fi
        
        # Create nginx configuration for COINjecture web interface
        cat > /etc/nginx/sites-available/coinjecture-web << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    
    root /opt/coinjecture-web;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Enable CORS for API calls
    location /api/ {
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # Serve static files with proper MIME types
    location ~* \.(js|css|html)$ {
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF
        
        # Enable the site
        ln -sf /etc/nginx/sites-available/coinjecture-web /etc/nginx/sites-enabled/
        
        # Remove default nginx site
        rm -f /etc/nginx/sites-enabled/default
        
        # Test nginx configuration
        nginx -t
        
        # Restart nginx
        systemctl restart nginx
        systemctl enable nginx
        
        echo "Nginx configured and started"
EOF
    
    log "✅ Nginx configured for web interface"
}

check_web_status() {
    log "Checking web interface status..."
    
    ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
        echo "Nginx status:"
        systemctl status nginx --no-pager
        
        echo ""
        echo "Port status:"
        netstat -tlnp | grep :80 || echo "Port 80 not listening"
        
        echo ""
        echo "Web files:"
        ls -la /opt/coinjecture-web/
        
        echo ""
        echo "Testing web interface:"
        curl -I http://localhost/ || echo "Web interface not accessible"
EOF
    
    log "✅ Web interface status checked"
}

main() {
    print_banner
    
    log "Starting COINjecture Web Interface deployment..."
    
    # Check SSH connection
    if ! check_ssh_connection; then
        exit 1
    fi
    
    # Deploy web files
    deploy_web_files
    
    # Setup nginx
    setup_nginx
    
    # Check status
    check_web_status
    
    log "🎉 Web interface deployment complete!"
    log "🌐 Web Interface: http://$DROPLET_IP/"
    log "📱 Mobile-optimized COINjecture CLI interface"
    log "🔗 API Backend: http://$DROPLET_IP:5000"
    log "📊 Monitor with: ssh $DROPLET_USER@$DROPLET_IP 'journalctl -u nginx -f'"
}

# Run main function
main "$@"
