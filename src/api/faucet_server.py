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
except ImportError:
    # Fallback for direct execution
    from cache_manager import CacheManager


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
        
        # Enable CORS for browser access
        CORS(self.app)
        
        # Rate limiting: 100 requests/minute per IP
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["100 per minute"]
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        
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
            """Get latest block data."""
            try:
                block_data = self.cache_manager.get_latest_block()
                return jsonify({
                    "status": "success",
                    "data": block_data,
                    "meta": {
                        "cached_at": block_data.get("last_updated", time.time()),
                        "api_version": "v1"
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Cache unavailable",
                    "message": str(e)
                }), 503
        
        @self.app.route('/v1/data/block/<int:index>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_block_by_index(index: int):
            """Get block data by index."""
            try:
                # Validate index
                if index < 0:
                    return jsonify({
                        "status": "error",
                        "error": "Invalid block index",
                        "message": "Block index must be non-negative"
                    }), 400
                
                block_data = self.cache_manager.get_block_by_index(index)
                if block_data is None:
                    return jsonify({
                        "status": "error",
                        "error": "Block not found",
                        "message": f"Block with index {index} not found"
                    }), 404
                
                return jsonify({
                    "status": "success",
                    "data": block_data,
                    "meta": {
                        "cached_at": block_data.get("last_updated", time.time()),
                        "api_version": "v1"
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/data/blocks', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_blocks_range():
            """Get range of blocks."""
            try:
                # Get query parameters
                start = request.args.get('start', type=int)
                end = request.args.get('end', type=int)
                
                if start is None or end is None:
                    return jsonify({
                        "status": "error",
                        "error": "Missing parameters",
                        "message": "Both 'start' and 'end' parameters are required"
                    }), 400
                
                # Validate range
                if start < 0 or end < 0:
                    return jsonify({
                        "status": "error",
                        "error": "Invalid range",
                        "message": "Start and end must be non-negative"
                    }), 400
                
                if start > end:
                    return jsonify({
                        "status": "error",
                        "error": "Invalid range",
                        "message": "Start must be less than or equal to end"
                    }), 400
                
                # Limit range size
                if end - start > 100:
                    return jsonify({
                        "status": "error",
                        "error": "Range too large",
                        "message": "Range cannot exceed 100 blocks"
                    }), 400
                
                blocks = self.cache_manager.get_blocks_range(start, end)
                
                return jsonify({
                    "status": "success",
                    "data": blocks,
                    "meta": {
                        "count": len(blocks),
                        "range": f"{start}-{end}",
                        "api_version": "v1"
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/data/ipfs/<cid>', methods=['GET'])
        @self.limiter.limit("50 per minute")
        def get_ipfs_data(cid: str):
            """Get IPFS data by CID (placeholder for future implementation)."""
            return jsonify({
                "status": "error",
                "error": "Not implemented",
                "message": "IPFS integration coming soon"
            }), 501
        
        # Error handlers
        @self.app.errorhandler(429)
        def ratelimit_handler(e):
            """Handle rate limit exceeded."""
            return jsonify({
                "status": "error",
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": e.retry_after
            }), 429
        
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
