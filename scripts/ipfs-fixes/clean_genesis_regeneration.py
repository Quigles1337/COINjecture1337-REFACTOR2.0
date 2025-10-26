#!/usr/bin/env python3
"""
Clean Genesis Regeneration - Create fresh blockchain with only real IPFS CIDs
"""

import sys
import os
sys.path.append('src')

from consensus import ConsensusEngine, ConsensusConfig
from storage import StorageManager, StorageConfig, NodeRole, PruningMode
from pow import ProblemRegistry
from api.blockchain_storage import COINjectureStorage

def clean_genesis_regeneration():
    """Regenerate genesis block with clean data and real IPFS CIDs."""
    print("🚀 Clean Genesis Regeneration")
    print("=" * 50)
    
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
    
    # Initialize API storage (for API database)
    api_storage = COINjectureStorage(data_dir="/opt/coinjecture/data")
    
    # Create consensus configuration
    consensus_config = ConsensusConfig(
        network_id="coinjecture-mainnet-v1",
        genesis_timestamp=1700000000.0,  # Use a fixed timestamp for deterministic genesis
        genesis_seed="coinjecture-genesis-2025"
    )
    
    problem_registry = ProblemRegistry()
    consensus_engine = ConsensusEngine(consensus_config, storage_manager, problem_registry)
    
    # Genesis block is created in ConsensusEngine.__init__
    genesis = consensus_engine.get_best_tip()
    
    print(f"✅ Genesis block created with real IPFS CID")
    print(f"   Hash: {genesis.block_hash}")
    print(f"   CID: {genesis.offchain_cid}")
    print(f"   Height: {genesis.index}")
    
    # Initialize API database
    api_storage.init_database()
    
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
    api_storage.add_block_data(genesis_data)
    
    print("✅ Genesis stored in API database")
    
    # Verify the CID is real and accessible
    try:
        data = storage_manager.ipfs_client.get(genesis.offchain_cid)
        proof_json = json.loads(data.decode("utf-8"))
        print(f"✅ Genesis proof data verified: {len(data)} bytes")
        print(f"   Problem: {proof_json.get('problem', {}).get('type', 'unknown')}")
        print(f"   Solution: {proof_json.get('solution', 'unknown')}")
        print(f"   Work Score: {proof_json.get('cumulative_work_score', 'unknown')}")
    except Exception as e:
        print(f"❌ Failed to verify genesis proof data: {e}")
        return False
    
    print(f"\n🎉 Clean genesis regeneration completed!")
    print(f"   - Genesis hash: {genesis.block_hash}")
    print(f"   - Real IPFS CID: {genesis.offchain_cid}")
    print(f"   - Proof data accessible: ✅")
    print(f"   - API database initialized: ✅")
    
    return True

if __name__ == "__main__":
    import json
    success = clean_genesis_regeneration()
    sys.exit(0 if success else 1)
