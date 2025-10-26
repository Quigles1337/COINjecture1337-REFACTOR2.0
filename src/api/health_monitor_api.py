#!/usr/bin/env python3
"""
Health Monitor API
Provides REST endpoints for monitoring system health and consensus status.
"""

import os
import json
import time
import subprocess
from datetime import datetime
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

class HealthMonitorAPI:
    """Health monitoring API for COINjecture services."""
    
    def __init__(self):
        self.consensus_service = "coinjecture-consensus"
        self.automatic_processor = "coinjecture-automatic-processor"
        self.blockchain_state_path = "/opt/coinjecture/data/blockchain_state.json"
        self.cache_path = "/home/coinjecture/COINjecture/data/cache/latest_block.json"
    
    def check_service_status(self, service_name):
        """Check if a systemd service is running."""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_consensus_logs(self, lines=20):
        """Get recent consensus service logs."""
        try:
            result = subprocess.run([
                "journalctl", "-u", self.consensus_service, "--no-pager", "-n", str(lines)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception:
            return None
    
    def detect_consensus_desync(self):
        """Detect if consensus service has desync issues."""
        logs = self.get_consensus_logs(50)
        if not logs:
            return False
        
        desync_indicators = [
            "Invalid block height:",
            "Parent block not found:",
            "Basic header validation failed",
            "expected 1"
        ]
        
        for indicator in desync_indicators:
            if indicator in logs:
                return True
        
        return False
    
    def get_blockchain_state(self):
        """Get current blockchain state."""
        try:
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception:
            return None
    
    def get_cache_state(self):
        """Get current API cache state."""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception:
            return None
    
    def get_consensus_health(self):
        """Get consensus service health status."""
        is_running = self.check_service_status(self.consensus_service)
        desync_detected = self.detect_consensus_desync()
        
        blockchain_state = self.get_blockchain_state()
        total_blocks = len(blockchain_state.get("blocks", [])) if blockchain_state else 0
        latest_block = blockchain_state.get("latest_block", {}) if blockchain_state else {}
        latest_index = latest_block.get("index", 0)
        
        # Determine status
        if not is_running:
            status = "stopped"
        elif desync_detected:
            status = "desynced"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "running": is_running,
            "desync_detected": desync_detected,
            "block_tree_height": total_blocks,
            "latest_block": latest_index,
            "total_blocks": total_blocks,
            "last_updated": latest_block.get("timestamp", 0)
        }
    
    def get_blockchain_health(self):
        """Get blockchain health status."""
        blockchain_state = self.get_blockchain_state()
        cache_state = self.get_cache_state()
        
        if not blockchain_state:
            return {
                "status": "error",
                "message": "Blockchain state not found"
            }
        
        total_blocks = len(blockchain_state.get("blocks", []))
        latest_block = blockchain_state.get("latest_block", {})
        
        # Check if cache is in sync
        cache_synced = False
        if cache_state:
            cache_index = cache_state.get("index", 0)
            blockchain_index = latest_block.get("index", 0)
            cache_synced = cache_index == blockchain_index
        
        return {
            "total_blocks": total_blocks,
            "latest_block_index": latest_block.get("index", 0),
            "latest_block_hash": latest_block.get("block_hash", ""),
            "automatic_processor_status": "running" if self.check_service_status(self.automatic_processor) else "stopped",
            "cache_synced": cache_synced,
            "last_updated": latest_block.get("timestamp", 0)
        }
    
    def get_services_health(self):
        """Get all services health status."""
        return {
            "consensus_service": "running" if self.check_service_status(self.consensus_service) else "stopped",
            "automatic_processor": "running" if self.check_service_status(self.automatic_processor) else "stopped",
            "faucet_api": "running" if self.check_service_status("faucet") else "unknown",
            "p2p_discovery": "running" if self.check_service_status("p2p") else "unknown"
        }
    
    def restart_consensus(self):
        """Manually trigger consensus restart."""
        try:
            # Stop consensus service
            subprocess.run(["systemctl", "stop", self.consensus_service], check=True)
            time.sleep(2)
            
            # Clear consensus database
            consensus_db = "/opt/coinjecture/data/blockchain.db"
            if os.path.exists(consensus_db):
                os.remove(consensus_db)
            
            # Start consensus service
            subprocess.run(["systemctl", "start", self.consensus_service], check=True)
            
            return {
                "status": "restarting",
                "message": "Consensus service restart initiated",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to restart consensus: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

# Initialize health monitor
health_monitor = HealthMonitorAPI()

# API Routes
@app.route('/v1/health/consensus', methods=['GET'])
@limiter.limit("10 per minute")
def get_consensus_health():
    """Get consensus service health status."""
    try:
        health = health_monitor.get_consensus_health()
        return jsonify({
            "status": "success",
            "data": health
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/v1/health/blockchain', methods=['GET'])
@limiter.limit("10 per minute")
def get_blockchain_health():
    """Get blockchain health status."""
    try:
        health = health_monitor.get_blockchain_health()
        return jsonify({
            "status": "success",
            "data": health
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/v1/health/services', methods=['GET'])
@limiter.limit("10 per minute")
def get_services_health():
    """Get all services health status."""
    try:
        health = health_monitor.get_services_health()
        return jsonify({
            "status": "success",
            "data": health
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/v1/health/consensus/restart', methods=['POST'])
@limiter.limit("1 per minute")
def restart_consensus():
    """Manually trigger consensus restart."""
    try:
        result = health_monitor.restart_consensus()
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/v1/health/status', methods=['GET'])
@limiter.limit("10 per minute")
def get_overall_health():
    """Get overall system health status."""
    try:
        consensus_health = health_monitor.get_consensus_health()
        blockchain_health = health_monitor.get_blockchain_health()
        services_health = health_monitor.get_services_health()
        
        # Determine overall status
        overall_status = "healthy"
        if consensus_health["status"] == "stopped":
            overall_status = "critical"
        elif consensus_health["status"] == "desynced":
            overall_status = "warning"
        elif not blockchain_health.get("cache_synced", False):
            overall_status = "warning"
        
        return jsonify({
            "status": "success",
            "data": {
                "overall_status": overall_status,
                "consensus": consensus_health,
                "blockchain": blockchain_health,
                "services": services_health,
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)
