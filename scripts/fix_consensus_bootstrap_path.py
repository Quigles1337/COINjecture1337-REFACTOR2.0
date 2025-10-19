#!/usr/bin/env python3
"""
Fix Consensus Bootstrap Path
Updates the consensus service to use absolute paths and improve bootstrap logic.
"""

import os
import sys
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_consensus_service():
    """Fix the consensus service bootstrap path and logic."""
    
    consensus_service_path = "/opt/coinjecture-consensus/consensus_service.py"
    
    if not os.path.exists(consensus_service_path):
        logger.error(f"Consensus service not found at {consensus_service_path}")
        return False
    
    logger.info("🔧 Fixing consensus service bootstrap path...")
    
    # Read the current consensus service
    with open(consensus_service_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = f"{consensus_service_path}.backup_{int(time.time())}"
    with open(backup_path, 'w') as f:
        f.write(content)
    logger.info(f"📁 Backup created: {backup_path}")
    
    # Fix 1: Update blockchain state path to absolute path
    old_path = 'self.blockchain_state_path = "data/blockchain_state.json"'
    new_path = 'self.blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"'
    
    if old_path in content:
        content = content.replace(old_path, new_path)
        logger.info("✅ Updated blockchain state path to absolute path")
    else:
        logger.warning("⚠️  Could not find blockchain state path to update")
    
    # Fix 2: Enhance bootstrap_from_cache method
    old_bootstrap = '''    def bootstrap_from_cache(self):
        """Bootstrap consensus engine with existing blockchain state."""
        try:
            # Check if blockchain state file exists
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                blocks = blockchain_state.get('blocks', [])
                logger.info(f"Found {len(blocks)} blocks in blockchain state")
                
                # Add each block to consensus engine
                for block_data in blocks:
                    block = self._convert_cache_block_to_block(block_data)
                    if block:
                        # Add to block tree without validation
                        self.consensus_engine._add_block_to_tree(block, receipt_time=block.timestamp)
                        logger.info(f"Bootstrapped block #{block.index}")
                
                return True
            else:
                logger.info("No blockchain state found, starting from genesis")
                return True
        except Exception as e:
            logger.error(f"Failed to bootstrap from cache: {e}")
            return False'''
    
    new_bootstrap = '''    def bootstrap_from_cache(self):
        """Bootstrap consensus engine with existing blockchain state."""
        try:
            # Check if blockchain state file exists
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                blocks = blockchain_state.get('blocks', [])
                logger.info(f"📊 Found {len(blocks)} blocks in blockchain state")
                
                if not blocks:
                    logger.info("No blocks found in blockchain state, starting from genesis")
                    return True
                
                # Sort blocks by index to ensure proper sequence
                blocks.sort(key=lambda x: x.get('index', 0))
                
                # Add each block to consensus engine in sequence
                for i, block_data in enumerate(blocks):
                    block = self._convert_cache_block_to_block(block_data)
                    if block:
                        # Add to block tree without validation
                        self.consensus_engine._add_block_to_tree(block, receipt_time=block.timestamp)
                        if i % 100 == 0 or i == len(blocks) - 1:
                            logger.info(f"📦 Bootstrapped block #{block.index} ({i+1}/{len(blocks)})")
                
                logger.info(f"✅ Successfully bootstrapped {len(blocks)} blocks")
                return True
            else:
                logger.info("No blockchain state found, starting from genesis")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to bootstrap from cache: {e}")
            return False'''
    
    if old_bootstrap in content:
        content = content.replace(old_bootstrap, new_bootstrap)
        logger.info("✅ Enhanced bootstrap_from_cache method")
    else:
        logger.warning("⚠️  Could not find bootstrap_from_cache method to update")
    
    # Write the fixed consensus service
    with open(consensus_service_path, 'w') as f:
        f.write(content)
    
    logger.info("✅ Consensus service updated")
    return True

def restart_consensus_service():
    """Restart the consensus service."""
    logger.info("🔄 Restarting consensus service...")
    
    # Stop the service
    os.system("sudo systemctl stop coinjecture-consensus")
    time.sleep(2)
    
    # Start the service
    os.system("sudo systemctl start coinjecture-consensus")
    time.sleep(5)
    
    # Check status
    result = os.system("sudo systemctl is-active coinjecture-consensus")
    if result == 0:
        logger.info("✅ Consensus service restarted successfully")
        return True
    else:
        logger.error("❌ Consensus service failed to start")
        return False

def main():
    """Main function."""
    logger.info("🚀 Starting consensus bootstrap path fix...")
    
    # Check if we're on the droplet
    if not os.path.exists("/opt/coinjecture-consensus"):
        logger.error("❌ This script must be run on the droplet")
        return 1
    
    # Fix the consensus service
    if not fix_consensus_service():
        logger.error("❌ Failed to fix consensus service")
        return 1
    
    # Restart the service
    if not restart_consensus_service():
        logger.error("❌ Failed to restart consensus service")
        return 1
    
    logger.info("✅ Consensus bootstrap path fix completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
