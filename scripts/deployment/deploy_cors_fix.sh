#!/bin/bash

# Deploy CORS Fix to Droplet
# This script fixes the duplicate CORS headers issue

set -e

echo "🔧 Deploying CORS Fix to Droplet"
echo "================================"

# Configuration
DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
USER="root"

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found at $SSH_KEY"
    echo "Please ensure the SSH key is in the correct location"
    exit 1
fi

echo "🔑 Using SSH key: $SSH_KEY"
echo "🌐 Connecting to droplet: $DROPLET_IP"
echo ""

# Create a comprehensive fix script for the droplet
cat > /tmp/fix_cors_droplet.sh << 'EOF'
#!/bin/bash

echo "🔧 Fixing CORS Headers on Droplet"
echo "================================"

# 1. Update the Flask CORS configuration
echo "📝 Updating Flask CORS configuration..."

# Create the fixed faucet_server.py
cat > /tmp/faucet_server_fixed.py << 'FAUCET_SERVER'
"""
COINjecture Faucet API Server

Flask-based REST API server for streaming blockchain data.
Implements the specification from FAUCET_API.README.md.
"""

import time
from flask import Flask, jsonify, request, Response  # type: ignore
from flask_cors import CORS  # type: ignore
from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from api.cache_manager import CacheManager
    from api.schema import TelemetryEvent, BlockEvent
    from api.ingest_store import IngestStore
    from api.auth import HMACAuth
    from api.user_auth import auth_manager
    from api.user_registration import user_bp
except ImportError:
    # Fallback for direct execution
    from cache_manager import CacheManager
    from schema import TelemetryEvent, BlockEvent
    from ingest_store import IngestStore
    from auth import HMACAuth
    from user_auth import auth_manager
    from user_registration import user_bp


class FaucetAPI:
    """
    COINjecture Faucet API server.
    
    Provides one-way access to blockchain data via REST endpoints.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize faucet API.
        
        Args:
            cache_dir: Directory containing cache files
        """
        self.app = Flask(__name__)
        self.cache_manager = CacheManager(cache_dir)
        self.ingest_store = IngestStore()
        # TODO: load from env or config
        self.auth = HMACAuth(secret=os.environ.get("FAUCET_HMAC_SECRET", "dev-secret"))
        
        # Enable CORS for browser access - FIXED CONFIGURATION
        CORS(self.app, 
            origins=["https://coinjecture.com", "https://api.coinjecture.com"],
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization", "X-User-ID", "X-Timestamp", "X-Signature"],
            supports_credentials=True)
        
        # Rate limiting: 100 requests/minute per IP
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["100 per minute"]
        )
        
        # Register user management routes
        self.app.register_blueprint(user_bp)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/', methods=['GET'])
        def root():
            """Root endpoint with API information."""
            return jsonify({
                "name": "COINjecture Faucet API",
                "version": "3.7.0",
                "description": "One-way faucet API for streaming blockchain data",
                "token_name": "COINjecture",
                "token_symbol": "$BEANS",
                "endpoints": {
                    "health": "/health",
                    "latest_block": "/v1/data/block/latest",
                    "block_by_index": "/v1/data/block/{index}",
                    "block_range": "/v1/data/blocks?start={start}&end={end}",
                    "all_blocks": "/v1/data/blocks/all",
                    "ipfs_data": "/v1/data/ipfs/{cid}",
                    "ipfs_list": "/v1/data/ipfs/list",
                    "ipfs_search": "/v1/data/ipfs/search?q={query}",
                    "telemetry_ingest": "/v1/ingest/telemetry",
                    "block_ingest": "/v1/ingest/block",
                    "latest_telemetry": "/v1/display/telemetry/latest",
                    "latest_blocks": "/v1/display/blocks/latest"
                },
                "server": "https://api.coinjecture.com",
                "status": "operational"
            })
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            cache_info = self.cache_manager.get_cache_info()
            return jsonify({
                "status": "healthy",
                "timestamp": time.time(),
                "cache": cache_info
            })
        
        @self.app.route('/v1/data/block/latest', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_latest_block():
            """Get the latest block from the blockchain."""
            try:
                block = self.cache_manager.get_latest_block()
                if block:
                    return jsonify({
                        "status": "success",
                        "data": block
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "No blocks found"
                    }), 404
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/data/block/<int:index>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_block_by_index(index):
            """Get a specific block by index."""
            try:
                block = self.cache_manager.get_block_by_index(index)
                if block:
                    return jsonify({
                        "status": "success",
                        "data": block
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": f"Block {index} not found"
                    }), 404
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/data/blocks', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_blocks_range():
            """Get blocks in a range."""
            try:
                start = request.args.get('start', type=int)
                end = request.args.get('end', type=int)
                
                if start is None or end is None:
                    return jsonify({
                        "status": "error",
                        "message": "start and end parameters are required"
                    }), 400
                
                blocks = self.cache_manager.get_blocks_range(start, end)
                return jsonify({
                    "status": "success",
                    "data": blocks
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/data/blocks/all', methods=['GET'])
        @self.limiter.limit("10 per minute")
        def get_all_blocks():
            """Get all blocks in the blockchain."""
            try:
                blocks = self.cache_manager.get_all_blocks()
                return jsonify({
                    "status": "success",
                    "data": blocks,
                    "meta": {
                        "api_version": "v1",
                        "cached_at": time.time(),
                        "total_blocks": len(blocks)
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/peers', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_peers():
            """Get connected peers."""
            try:
                # Mock peer data for now
                peers = [
                    {"address": "167.172.213.70", "port": 12345, "status": "connected"},
                    {"address": "bootstrap.coinjecture.com", "port": 12345, "status": "connected"}
                ]
                return jsonify({
                    "status": "success",
                    "data": peers
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/display/telemetry/latest', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_latest_telemetry():
            """Get latest network telemetry."""
            try:
                # Mock telemetry data
                telemetry = {
                    "active_miners": 5,
                    "total_blocks": 5000,
                    "hash_rate": "1.2 TH/s",
                    "timestamp": time.time()
                }
                return jsonify({
                    "status": "success",
                    "data": telemetry
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/mine', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def start_mining():
            """Start mining operation."""
            try:
                data = request.get_json()
                tier = data.get('tier', 'mobile')
                miner_address = data.get('miner_address', '')
                
                # Mock mining response
                return jsonify({
                    "status": "success",
                    "data": {
                        "mining_id": f"mine_{int(time.time())}",
                        "tier": tier,
                        "miner_address": miner_address,
                        "started_at": time.time()
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.errorhandler(404)
        def not_found_handler(e):
            """Handle 404 errors."""
            return jsonify({
                "status": "error",
                "error": "Not found",
                "message": "The requested resource was not found"
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error_handler(e):
            """Handle 500 errors."""
            return jsonify({
                "status": "error",
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }), 500
    
    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """
        Run the API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        print(f"🚰 COINjecture Faucet API starting on {host}:{port}")
        print(f"📊 Cache directory: {self.cache_manager.cache_dir}")
        print(f"🔗 Health check: http://{host}:{port}/health")
        print(f"📈 Latest block: http://{host}:{port}/v1/data/block/latest")
        
        self.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    # Create and run API server
    api = FaucetAPI()
    api.run(debug=True)
FAUCET_SERVER

# Copy the fixed faucet_server.py to the API directory
cp /tmp/faucet_server_fixed.py /home/coinjecture/COINjecture/src/api/faucet_server.py
echo "✅ Updated faucet_server.py with fixed CORS configuration"

# 2. Fix Nginx CORS configuration
echo "🔧 Fixing Nginx CORS configuration..."

# Backup current Nginx config
cp /etc/nginx/sites-available/coinjecture-api /etc/nginx/sites-available/coinjecture-api.backup

# Remove any existing CORS headers from Nginx
sed -i '/add_header Access-Control-Allow-Origin/d' /etc/nginx/sites-available/coinjecture-api
sed -i '/add_header Access-Control-Allow-Methods/d' /etc/nginx/sites-available/coinjecture-api
sed -i '/add_header Access-Control-Allow-Headers/d' /etc/nginx/sites-available/coinjecture-api

echo "✅ Removed duplicate CORS headers from Nginx"

# 3. Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    
    # Reload Nginx
    systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration test failed"
    echo "Restoring backup..."
    cp /etc/nginx/sites-available/coinjecture-api.backup /etc/nginx/sites-available/coinjecture-api
    exit 1
fi

# 4. Restart the API service
echo "🔄 Restarting API service..."
systemctl restart coinjecture-api
echo "✅ API service restarted"

# 5. Test the fix
echo "🧪 Testing CORS fix..."
sleep 2

# Test the API endpoint
curl -s -H "Origin: https://coinjecture.com" https://api.coinjecture.com/v1/data/block/latest | head -5

echo ""
echo "✅ CORS fix completed!"
echo "======================"
echo ""
echo "🎯 What was fixed:"
echo "   ✅ Flask CORS configured with specific origins"
echo "   ✅ Removed duplicate CORS headers from Nginx"
echo "   ✅ API service restarted"
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "The CORS error should be resolved!"

# Clean up
rm -f /tmp/faucet_server_fixed.py

EOF

# Make the script executable
chmod +x /tmp/fix_cors_droplet.sh

echo "📤 Copying CORS fix script to droplet..."
scp -i "$SSH_KEY" /tmp/fix_cors_droplet.sh "$USER@$DROPLET_IP:/tmp/"

echo "🚀 Running CORS fix on droplet..."
ssh -i "$SSH_KEY" "$USER@$DROPLET_IP" "chmod +x /tmp/fix_cors_droplet.sh && /tmp/fix_cors_droplet.sh"

# Clean up
rm -f /tmp/fix_cors_droplet.sh

echo ""
echo "🎉 CORS fix deployment completed!"
echo "================================="
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "The CORS error should be resolved and the frontend should work!"
