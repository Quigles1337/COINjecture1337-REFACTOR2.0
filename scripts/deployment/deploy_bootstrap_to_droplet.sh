#!/usr/bin/env bash
set -euo pipefail

# COINjecture Bootstrap Node Deployment to DigitalOcean Droplet
# Deploys the P2P bootstrap node to the live network

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DROPLET_IP="167.172.213.70"
DROPLET_USER="root"  # Adjust if different
BOOTSTRAP_PORT="12345"
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
    echo "║         🌐 P2P Bootstrap Node Deployment to DigitalOcean                                  ║"
    echo "║         🚀 Deploy to: $DROPLET_IP:$BOOTSTRAP_PORT ║"
    echo "║         🔗 Create P2P network infrastructure                                               ║"
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

deploy_bootstrap_node() {
    log "Deploying bootstrap node to droplet..."
    
    # Create deployment directory on droplet
    ssh $DROPLET_USER@$DROPLET_IP "mkdir -p /opt/coinjecture-bootstrap"
    
    # Copy bootstrap node files
    log "Copying bootstrap node files..."
    scp scripts/bootstrap/start_bootstrap_node.py $DROPLET_USER@$DROPLET_IP:/opt/coinjecture-bootstrap/
    scp -r src/ $DROPLET_USER@$DROPLET_IP:/opt/coinjecture-bootstrap/
    scp requirements.txt $DROPLET_USER@$DROPLET_IP:/opt/coinjecture-bootstrap/
    
    # Create logs directory
    ssh $DROPLET_USER@$DROPLET_IP "mkdir -p /opt/coinjecture-bootstrap/logs"
    
    log "✅ Bootstrap node files deployed"
}

setup_python_environment() {
    log "Setting up Python environment on droplet..."
    
    ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
        cd /opt/coinjecture-bootstrap
        
        # Check if Python 3 is available
        if ! command -v python3 &> /dev/null; then
            echo "Installing Python 3..."
            apt-get update
            apt-get install -y python3 python3-pip python3-venv
        fi
        
        # Create virtual environment
        python3 -m venv .venv
        source .venv/bin/activate
        
        # Install dependencies
        pip install -r requirements.txt
        
        echo "Python environment setup complete"
EOF
    
    log "✅ Python environment configured"
}

create_systemd_service() {
    log "Creating systemd service for bootstrap node..."
    
    ssh $DROPLET_USER@$DROPLET_IP << EOF
        cat > /etc/systemd/system/coinjecture-bootstrap.service << 'SERVICE_EOF'
[Unit]
Description=COINjecture P2P Bootstrap Node
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/coinjecture-bootstrap
Environment=PATH=/opt/coinjecture-bootstrap/.venv/bin
ExecStart=/opt/coinjecture-bootstrap/.venv/bin/python3 start_bootstrap_node.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

        systemctl daemon-reload
        systemctl enable coinjecture-bootstrap.service
        echo "Systemd service created and enabled"
EOF
    
    log "✅ Systemd service configured"
}

start_bootstrap_service() {
    log "Starting bootstrap node service..."
    
    ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
        systemctl start coinjecture-bootstrap.service
        sleep 3
        
        if systemctl is-active --quiet coinjecture-bootstrap.service; then
            echo "✅ Bootstrap node service started successfully"
        else
            echo "❌ Failed to start bootstrap node service"
            systemctl status coinjecture-bootstrap.service
            exit 1
        fi
EOF
    
    log "✅ Bootstrap node service started"
}

check_bootstrap_status() {
    log "Checking bootstrap node status..."
    
    ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
        echo "Service status:"
        systemctl status coinjecture-bootstrap.service --no-pager
        
        echo ""
        echo "Recent logs:"
        journalctl -u coinjecture-bootstrap.service -n 10 --no-pager
        
        echo ""
        echo "Port status:"
        netstat -tlnp | grep :12345 || echo "Port 12345 not listening"
EOF
    
    log "✅ Bootstrap node status checked"
}

update_mining_node_config() {
    log "Updating local mining node to connect to droplet bootstrap..."
    
    # Update the mining node configuration to use the droplet bootstrap
    sed -i.bak "s/bootstrap_peers=\['localhost:12345'\]/bootstrap_peers=['$DROPLET_IP:$BOOTSTRAP_PORT']/" start_p2p_miner.py
    
    log "✅ Mining node configuration updated"
    log "💡 Mining nodes can now connect to: $DROPLET_IP:$BOOTSTRAP_PORT"
}

main() {
    print_banner
    
    log "Starting COINjecture P2P Bootstrap Node deployment..."
    
    # Check SSH connection
    if ! check_ssh_connection; then
        exit 1
    fi
    
    # Deploy bootstrap node
    deploy_bootstrap_node
    
    # Setup Python environment
    setup_python_environment
    
    # Create systemd service
    create_systemd_service
    
    # Start bootstrap service
    start_bootstrap_service
    
    # Check status
    check_bootstrap_status
    
    # Update local mining node config
    update_mining_node_config
    
    log "🎉 Bootstrap node deployment complete!"
    log "🌐 P2P Bootstrap Node: $DROPLET_IP:$BOOTSTRAP_PORT"
    log "🔗 Mining nodes can connect to: $DROPLET_IP:$BOOTSTRAP_PORT"
    log "📊 Monitor with: ssh $DROPLET_USER@$DROPLET_IP 'journalctl -u coinjecture-bootstrap.service -f'"
}

# Run main function
main "$@"
