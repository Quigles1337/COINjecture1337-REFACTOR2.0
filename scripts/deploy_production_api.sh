#!/bin/bash
# Deploy Production API Setup to Droplet

set -euo pipefail

DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"

echo "🚀 Deploying Production API Setup to Droplet"
echo "============================================="

# Copy setup script to droplet
echo "📤 Copying setup script to droplet..."
scp -i $SSH_KEY scripts/setup_production_api.sh coinjecture@$DROPLET_IP:/home/coinjecture/

# Copy updated web interface
echo "📤 Copying updated web interface..."
scp -i $SSH_KEY web/app.js coinjecture@$DROPLET_IP:/home/coinjecture/COINjecture/web/

# Copy updated CLI
echo "📤 Copying updated CLI..."
scp -i $SSH_KEY src/cli.py coinjecture@$DROPLET_IP:/home/coinjecture/COINjecture/src/

# Copy updated config
echo "📤 Copying updated config..."
scp -i $SSH_KEY config/miner_config.json coinjecture@$DROPLET_IP:/home/coinjecture/COINjecture/config/

# Execute setup script on droplet
echo "⚙️  Executing production API setup on droplet..."
ssh -i $SSH_KEY coinjecture@$DROPLET_IP << 'EOF'
cd /home/coinjecture
chmod +x setup_production_api.sh
sudo ./setup_production_api.sh
EOF

echo "✅ Production API setup deployed!"
echo "🌐 API should be accessible at: https://api.coinjecture.com"
echo "📋 Next steps:"
echo "   1. Configure DNS A record: api.coinjecture.com → $DROPLET_IP"
echo "   2. Configure DNS AAAA record: api.coinjecture.com → [IPv6 address]"
echo "   3. Wait for DNS propagation (5-15 minutes)"
echo "   4. Test: curl https://api.coinjecture.com/health"
