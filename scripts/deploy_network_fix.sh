#!/bin/bash
# Deploy Network Stalling Fix to Remote Server
# This script deploys the enhanced signature validation fix

echo "🚀 Deploying Network Stalling Fix to Remote Server"
echo "=================================================="

# Check if we have the enhanced wallet.py
if [ ! -f "src/tokenomics/wallet.py" ]; then
    echo "❌ Enhanced wallet.py not found"
    exit 1
fi

echo "📤 Step 1: Copying enhanced wallet.py to remote server..."

# Create a temporary deployment package
mkdir -p /tmp/coinjecture_deploy
cp src/tokenomics/wallet.py /tmp/coinjecture_deploy/wallet.py

echo "📦 Deployment package created at /tmp/coinjecture_deploy/"
echo "📋 Manual deployment instructions:"
echo ""
echo "1. Copy the enhanced wallet.py to remote server:"
echo "   scp /tmp/coinjecture_deploy/wallet.py coinjecture@167.172.213.70:/tmp/wallet_enhanced.py"
echo ""
echo "2. SSH to remote server and apply the fix:"
echo "   ssh coinjecture@167.172.213.70"
echo ""
echo "3. On remote server, execute:"
echo "   sudo cp /tmp/wallet_enhanced.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py"
echo "   sudo chown coinjecture:coinjecture /home/coinjecture/COINjecture/src/tokenomics/wallet.py"
echo "   sudo systemctl restart coinjecture-api.service"
echo "   sudo systemctl status coinjecture-api.service"
echo ""
echo "4. Test the fix:"
echo "   curl -k https://167.172.213.70/v1/data/block/latest"
echo ""
echo "✅ Enhanced wallet.py ready for deployment!"
echo "🔧 This fix will resolve the signature validation errors causing network stalling"



