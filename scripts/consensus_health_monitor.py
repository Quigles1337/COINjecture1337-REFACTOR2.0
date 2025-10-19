#!/usr/bin/env python3
"""
Consensus Health Monitor
Monitors consensus service for desync issues and automatically restarts when needed.
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture-consensus/logs/health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('consensus-health-monitor')

class ConsensusHealthMonitor:
    """Monitors consensus service health and handles desync recovery."""
    
    def __init__(self):
        self.consensus_service = "coinjecture-consensus"
        self.blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
        self.consensus_db_path = "/opt/coinjecture-consensus/data/blockchain.db"
        self.last_restart = None
        self.desync_detected = False
        
    def check_consensus_status(self):
        """Check if consensus service is running."""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", self.consensus_service],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking consensus status: {e}")
            return False
    
    def detect_desync(self):
        """Detect if consensus service has desync issues."""
        try:
            # Check recent logs for desync indicators
            result = subprocess.run([
                "journalctl", "-u", self.consensus_service, "--no-pager", "-n", "50"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return False
            
            log_output = result.stdout
            
            # Look for desync indicators
            desync_indicators = [
                "Invalid block height:",
                "Parent block not found:",
                "Basic header validation failed",
                "expected 1"
            ]
            
            for indicator in desync_indicators:
                if indicator in log_output:
                    logger.warning(f"Desync indicator detected: {indicator}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting desync: {e}")
            return False
    
    def get_blockchain_state(self):
        """Get current blockchain state."""
        try:
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error reading blockchain state: {e}")
            return None
    
    def clear_consensus_state(self):
        """Clear consensus service state to force fresh bootstrap."""
        try:
            # Stop consensus service
            logger.info("Stopping consensus service...")
            subprocess.run(["systemctl", "stop", self.consensus_service], check=True)
            time.sleep(2)
            
            # Remove consensus database to force fresh bootstrap
            if os.path.exists(self.consensus_db_path):
                os.remove(self.consensus_db_path)
                logger.info("Removed consensus database for fresh bootstrap")
            
            # Clear any other consensus state files
            consensus_data_dir = "/opt/coinjecture-consensus/data"
            for file in os.listdir(consensus_data_dir):
                if file.endswith('.db') and file != 'faucet_ingest.db':
                    file_path = os.path.join(consensus_data_dir, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Removed {file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing consensus state: {e}")
            return False
    
    def restart_consensus(self):
        """Restart consensus service."""
        try:
            logger.info("Starting consensus service...")
            subprocess.run(["systemctl", "start", self.consensus_service], check=True)
            
            # Wait for service to start
            time.sleep(5)
            
            # Verify it's running
            if self.check_consensus_status():
                logger.info("Consensus service restarted successfully")
                self.last_restart = datetime.now().isoformat()
                return True
            else:
                logger.error("Consensus service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error restarting consensus: {e}")
            return False
    
    def verify_consensus_health(self):
        """Verify consensus service is healthy after restart."""
        try:
            # Wait a bit for service to initialize
            time.sleep(10)
            
            # Check if it's still running
            if not self.check_consensus_status():
                return False
            
            # Check logs for successful bootstrap
            result = subprocess.run([
                "journalctl", "-u", self.consensus_service, "--no-pager", "-n", "20"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                log_output = result.stdout
                # Look for successful bootstrap indicators
                success_indicators = [
                    "Consensus service initialized",
                    "Bootstrapped block",
                    "Processed block"
                ]
                
                for indicator in success_indicators:
                    if indicator in log_output:
                        logger.info(f"Consensus health verified: {indicator}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying consensus health: {e}")
            return False
    
    def handle_desync(self):
        """Handle consensus desync by restarting and rebuilding."""
        logger.warning("Consensus desync detected - initiating recovery...")
        
        # Clear state and restart
        if not self.clear_consensus_state():
            logger.error("Failed to clear consensus state")
            return False
        
        if not self.restart_consensus():
            logger.error("Failed to restart consensus service")
            return False
        
        # Verify health
        if not self.verify_consensus_health():
            logger.error("Consensus service not healthy after restart")
            return False
        
        logger.info("Consensus desync recovery completed successfully")
        self.desync_detected = False
        return True
    
    def get_health_status(self):
        """Get current health status."""
        blockchain_state = self.get_blockchain_state()
        
        status = {
            "consensus_running": self.check_consensus_status(),
            "desync_detected": self.desync_detected,
            "last_restart": self.last_restart,
            "blockchain_blocks": 0,
            "latest_block_index": 0
        }
        
        if blockchain_state:
            status["blockchain_blocks"] = len(blockchain_state.get("blocks", []))
            latest_block = blockchain_state.get("latest_block", {})
            status["latest_block_index"] = latest_block.get("index", 0)
        
        return status
    
    def run_monitoring_loop(self):
        """Run the monitoring loop."""
        logger.info("Starting consensus health monitoring...")
        
        while True:
            try:
                # Check if consensus is running
                if not self.check_consensus_status():
                    logger.warning("Consensus service is not running")
                    time.sleep(30)
                    continue
                
                # Check for desync
                if self.detect_desync():
                    self.desync_detected = True
                    logger.warning("Desync detected - initiating recovery")
                    if self.handle_desync():
                        logger.info("Desync recovery successful")
                    else:
                        logger.error("Desync recovery failed")
                else:
                    # Reset desync flag if no issues detected
                    if self.desync_detected:
                        logger.info("Desync resolved - consensus is healthy")
                        self.desync_detected = False
                
                # Log current status
                status = self.get_health_status()
                logger.info(f"Health status: {status}")
                
                # Wait before next check
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)

def main():
    """Main function."""
    logger.info("Starting consensus health monitor...")
    
    # Check if we're on the droplet
    if not os.path.exists("/opt/coinjecture-consensus"):
        logger.error("This script must be run on the droplet")
        return 1
    
    # Create monitor
    monitor = ConsensusHealthMonitor()
    
    # Run monitoring
    try:
        monitor.run_monitoring_loop()
    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
