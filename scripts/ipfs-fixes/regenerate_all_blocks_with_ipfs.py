#!/usr/bin/env python3
"""
Regenerate All Blocks with Proper IPFS Storage
"""

import sys
import os
sys.path.append('src')

from consensus import ConsensusEngine, ConsensusConfig
from storage import StorageManager, StorageConfig, NodeRole, PruningMode
from pow import ProblemRegistry
from api.blockchain_storage import COINjectureStorage
from core.blockchain import mine_block, ProblemTier, ProblemType
import json
import time

def regenerate_all_blocks_with_ipfs():
    """Regenerate all blocks with proper IPFS storage."""
    print("🚀 Regenerating All Blocks with IPFS Storage")
    print("=" * 60)
    
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
    
    # Initialize API storage
    api_storage = COINjectureStorage(data_dir="/opt/coinjecture/data")
    
    # Get current blockchain state
    latest_height = api_storage.get_latest_height()
    print(f"📊 Current blockchain: {latest_height + 1} blocks")
    
    # Create consensus configuration
    consensus_config = ConsensusConfig(
        network_id="coinjecture-mainnet-v1",
        genesis_timestamp=1700000000.0,
        genesis_seed="coinjecture-genesis-2025"
    )
    
    problem_registry = ProblemRegistry()
    consensus_engine = ConsensusEngine(consensus_config, storage_manager, problem_registry)
    
    # Get genesis block
    genesis = consensus_engine.get_best_tip()
    print(f"✅ Genesis block: {genesis.block_hash[:16]}... (CID: {genesis.offchain_cid[:16]}...)")
    
    # Test genesis block IPFS access
    try:
        data = storage_manager.ipfs_client.get(genesis.offchain_cid)
        print(f"✅ Genesis IPFS data: {len(data)} bytes")
    except Exception as e:
        print(f"❌ Genesis IPFS error: {e}")
        return False
    
    # Regenerate blocks 1 through latest_height
    current_block = genesis
    regenerated_count = 0
    
    for i in range(1, latest_height + 1):
        try:
            print(f"\\n🔄 Regenerating Block {i}...")
            
            # Mine a new block
            new_block = mine_block(
                transactions=[f"Regenerated block {i}"],
                previous_block=current_block,
                capacity=ProblemTier.TIER_1_MOBILE,
                problem_type=ProblemType.SUBSET_SUM,
                miner_address="Regenerator"
            )
            
            # Verify IPFS storage
            if new_block.offchain_cid:
                try:
                    data = storage_manager.ipfs_client.get(new_block.offchain_cid)
                    print(f"   ✅ Block {i}: {new_block.block_hash[:16]}... (CID: {new_block.offchain_cid[:16]}...) - {len(data)} bytes")
                    regenerated_count += 1
                    current_block = new_block
                except Exception as e:
                    print(f"   ❌ Block {i} IPFS error: {e}")
                    return False
            else:
                print(f"   ❌ Block {i}: No CID generated")
                return False
                
        except Exception as e:
            print(f"   ❌ Block {i} generation error: {e}")
            return False
    
    print(f"\\n🎉 Successfully regenerated {regenerated_count} blocks with IPFS storage!")
    
    # Verify all blocks are accessible
    print(f"\\n🔍 Verifying all blocks...")
    accessible_count = 0
    
    for i in range(latest_height + 1):
        block_data = api_storage.get_block_data(i)
        if block_data:
            cid = block_data.get("cid")
            if cid:
                try:
                    data = storage_manager.ipfs_client.get(cid)
                    accessible_count += 1
                    if i % 10 == 0:  # Progress indicator
                        print(f"   ✅ Block {i}: {cid[:16]}... - {len(data)} bytes")
                except Exception as e:
                    print(f"   ❌ Block {i}: {cid[:16]}... - {str(e)[:50]}...")
    
    print(f"\\n📊 Final Results:")
    print(f"   Total blocks: {latest_height + 1}")
    print(f"   Accessible blocks: {accessible_count}")
    print(f"   Success rate: {accessible_count/(latest_height + 1)*100:.1f}%")
    
    return accessible_count == latest_height + 1

if __name__ == "__main__":
    success = regenerate_all_blocks_with_ipfs()
    sys.exit(0 if success else 1)
