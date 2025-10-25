#!/usr/bin/env python3
"""
Initialize Genesis Block with Proper Metrics
Uses existing genesis hash and initializes with proper metrics
"""

import sys
import os
import time
import json
import logging

# Add src to path
sys.path.append('src')

from api.blockchain_storage import storage
from metrics_engine import SATOSHI_CONSTANT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_genesis_block():
    """Initialize genesis block with proper metrics."""
    logger.info(f"🚀 Initializing genesis block with Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
    
    # Existing genesis hash
    GENESIS_HASH = "d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358"
    
    # Initialize database
    storage.init_database()
    
    # Create genesis block data
    genesis_block = {
        "block_hash": GENESIS_HASH,
        "index": 0,
        "timestamp": int(time.time()),
        "previous_hash": "0" * 64,  # Genesis has no previous hash
        "merkle_root": "0" * 64,
        "miner_address": "GENESIS",
        "work_score": 0.0,
        "capacity": "genesis",
        "cid": "QmGenesis",
        "gas_used": 0,
        "gas_limit": 1000000,
        "gas_price": 0.000001,
        "reward": 0.0,
        "cumulative_work_score": 0.0,
        "damping_ratio": SATOSHI_CONSTANT,
        "stability_metric": 1.0,
        "problem_type": "genesis",
        "tier": "genesis"
    }
    
    # Serialize block data
    block_bytes = json.dumps(genesis_block).encode('utf-8')
    
    # Store genesis block
    storage.add_block_data(genesis_block)
    
    logger.info(f"✅ Genesis block initialized:")
    logger.info(f"   Hash: {GENESIS_HASH}")
    logger.info(f"   Height: 0")
    logger.info(f"   Work Score: 0.0")
    logger.info(f"   Gas Used: 0")
    logger.info(f"   Reward: 0.0")
    logger.info(f"   Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
    
    return genesis_block

def verify_genesis_block():
    """Verify genesis block was stored correctly."""
    try:
        # Get genesis block data
        genesis_data = storage.get_block_data(0)
        
        if not genesis_data:
            logger.error("❌ Genesis block not found in database")
            return False
        
        # Verify key fields
        if genesis_data.get('work_score') != 0.0:
            logger.warning(f"⚠️  Genesis work_score should be 0.0, got {genesis_data.get('work_score')}")
        
        if genesis_data.get('gas_used') != 0:
            logger.warning(f"⚠️  Genesis gas_used should be 0, got {genesis_data.get('gas_used')}")
        
        if genesis_data.get('reward') != 0.0:
            logger.warning(f"⚠️  Genesis reward should be 0.0, got {genesis_data.get('reward')}")
        
        logger.info("✅ Genesis block verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Genesis block verification failed: {e}")
        return False

def main():
    """Main function to initialize genesis block."""
    try:
        # Initialize genesis block
        genesis_block = initialize_genesis_block()
        
        # Verify genesis block
        if verify_genesis_block():
            logger.info("🎉 Genesis block initialization completed successfully")
        else:
            logger.error("❌ Genesis block initialization failed verification")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error in genesis initialization: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
