#!/usr/bin/env python3
"""
Regenerate Genesis Block with Real IPFS CID
Preserves existing genesis hash: d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358
"""

import sys
import os
sys.path.append('src')

from consensus import ConsensusEngine, ConsensusConfig
from storage import StorageManager, StorageConfig, NodeRole, PruningMode
from pow import ProblemRegistry
from api.blockchain_storage import storage

def regenerate_genesis():
    # Verify IPFS is running
    storage_config = StorageConfig(
        data_dir="/opt/coinjecture/data",
        role=NodeRole.FULL,
        pruning_mode=PruningMode.FULL,
        ipfs_api_url="http://localhost:5001"
    )
    storage_manager = StorageManager(storage_config)
    
    if not storage_manager.ipfs_client.health_check():
        print("❌ IPFS daemon not available. Start IPFS first.")
        return False
    
    print("✅ IPFS daemon is healthy")
    
    # Initialize consensus with existing genesis hash
    consensus_config = ConsensusConfig(
        genesis_seed="coinjecture-genesis-2025",
        genesis_timestamp=1700000000.0
    )
    
    problem_registry = ProblemRegistry()
    consensus_engine = ConsensusEngine(consensus_config, storage_manager, problem_registry)
    
    # Genesis block is created in ConsensusEngine.__init__
    genesis = consensus_engine.get_best_tip()
    
    print(f"✅ Genesis block created with real IPFS CID")
    print(f"   Hash: {genesis.block_hash}")
    print(f"   CID: {genesis.offchain_cid}")
    print(f"   Height: {genesis.index}")
    
    # Initialize API storage database
    storage.init_database()
    
    # Store genesis in API database
    genesis_data = {
        "block_hash": genesis.block_hash,
        "index": genesis.index,
        "timestamp": genesis.timestamp,
        "previous_hash": genesis.previous_hash,
        "cid": genesis.offchain_cid,
        "work_score": genesis.cumulative_work_score,
        "gas_used": 0,
        "gas_limit": 1000000,
        "gas_price": 0.000001,
        "reward": 0.0
    }
    storage.add_block_data(genesis_data)
    
    print("✅ Genesis stored in API database")
    return True

if __name__ == "__main__":
    success = regenerate_genesis()
    sys.exit(0 if success else 1)
