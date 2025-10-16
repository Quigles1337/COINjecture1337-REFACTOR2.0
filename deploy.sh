#!/bin/bash

# COINjecture Faucet API - DigitalOcean Deployment Script
# Usage: ./deploy.sh <droplet_ip>

if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <droplet_ip>"
    echo "Example: ./deploy.sh 164.92.89.62"
    exit 1
fi

DROPLET_IP=$1
echo "🚀 Deploying COINjecture Faucet API to $DROPLET_IP"

# Step 1: System setup
echo "📦 Setting up system..."
ssh root@$DROPLET_IP << 'EOF'
    apt update && apt upgrade -y
    apt install -y python3.9 python3.9-pip python3.9-venv nginx git
    adduser coinjecture
    usermod -aG sudo coinjecture
EOF

# Step 2: Deploy application
echo "📥 Deploying application..."
ssh coinjecture@$DROPLET_IP << 'EOF'
    git clone https://github.com/beanapologist/COINjecture.git
    cd COINjecture
    python3.9 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    mkdir -p data/cache
EOF

# Step 3: Create systemd services
echo "⚙️ Creating systemd services..."
ssh root@$DROPLET_IP << EOF
    cat > /etc/systemd/system/coinjecture-api.service << 'SERVICE_EOF'
[Unit]
Description=COINjecture Faucet API
After=network.target

[Service]
Type=simple
User=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
Environment=PATH=/home/coinjecture/COINjecture/venv/bin
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/faucet_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

    cat > /etc/systemd/system/coinjecture-cache.service << 'SERVICE_EOF'
[Unit]
Description=COINjecture Cache Updater
After=network.target

[Service]
Type=simple
User=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
Environment=PATH=/home/coinjecture/COINjecture/venv/bin
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/update_cache.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
SERVICE_EOF
EOF

# Step 4: Configure nginx
echo "🌐 Configuring nginx..."
ssh root@$DROPLET_IP << EOF
    cat > /etc/nginx/sites-available/coinjecture << 'NGINX_EOF'
server {
    listen 80;
    server_name $DROPLET_IP;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX_EOF

    ln -s /etc/nginx/sites-available/coinjecture /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
EOF

# Step 5: Enable services
echo "🚀 Starting services..."
ssh root@$DROPLET_IP << 'EOF'
    systemctl daemon-reload
    systemctl enable coinjecture-api
    systemctl enable coinjecture-cache
    systemctl start coinjecture-api
    systemctl start coinjecture-cache
EOF

# Step 6: Configure firewall
echo "🔥 Configuring firewall..."
ssh root@$DROPLET_IP << 'EOF'
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
EOF

# Step 7: Test deployment
echo "🧪 Testing deployment..."
sleep 10  # Wait for services to start

echo "Testing health endpoint..."
curl -s http://$DROPLET_IP/health | head -c 200
echo ""

echo "Testing latest block endpoint..."
curl -s http://$DROPLET_IP/v1/data/block/latest | head -c 200
echo ""

echo "🎉 Deployment complete!"
echo "🚰 COINjecture Faucet API is live at:"
echo "   Health: http://$DROPLET_IP/health"
echo "   Latest Block: http://$DROPLET_IP/v1/data/block/latest"
echo "   Block by Index: http://$DROPLET_IP/v1/data/block/{index}"
echo "   Block Range: http://$DROPLET_IP/v1/data/blocks?start={start}&end={end}"
echo ""
echo "📱 Ready to tweet:"
echo "🚰 COINjecture Faucet v3.1.0 is LIVE! Pull clean blockchain data at http://$DROPLET_IP/v1/data/block/latest. No auth, no BS, just pure data. #buildinginpublic #blockchain"
