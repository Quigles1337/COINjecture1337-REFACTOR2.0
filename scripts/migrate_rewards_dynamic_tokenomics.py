#!/usr/bin/env python3
"""
Migrate all existing miner rewards using correct dynamic tokenomics.
"""
import json
import sqlite3
import time
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from tokenomics.dynamic_tokenomics import DynamicWorkScoreTokenomics
from core.blockchain import ProblemTier, ComputationalComplexity

def create_complexity_from_block(block):
    """Create ComputationalComplexity object from block data."""
    work_score = block.get('work_score', 0.0)
    capacity = block.get('capacity', 'mobile')
    
    # Map capacity string to ProblemTier
    capacity_map = {
        'mobile': ProblemTier.TIER_1_MOBILE,
        'desktop': ProblemTier.TIER_2_DESKTOP,
        'workstation': ProblemTier.TIER_3_WORKSTATION,
        'server': ProblemTier.TIER_4_SERVER,
        'cluster': ProblemTier.TIER_5_CLUSTER
    }
    
    tier = capacity_map.get(capacity.lower(), ProblemTier.TIER_1_MOBILE)
    
    # Estimate problem size from work score (work_score = 2^problem_size)
    problem_size = int(work_score.bit_length()) if work_score > 0 else 8
    
    # Create complexity object
    complexity = ComputationalComplexity(
        problem_size=problem_size,
        measured_solve_time=work_score / 1000.0,  # Estimate solve time
        measured_verify_time=0.001,  # Fast verification
        solve_memory=1000000,  # 1MB
        verify_memory=10000,   # 10KB
        energy_metrics=None,
        asymmetry_time=work_score / 1000.0,  # Asymmetry ratio
        problem_tier=tier,
        hardware_type=None,
        solution_quality=1.0,
        optimization_level=1.0
    )
    
    return complexity

def create_mock_block(block_data, capacity):
    """Create mock Block object from block data."""
    from core.blockchain import Block
    
    # Map capacity string to ProblemTier
    capacity_map = {
        'mobile': ProblemTier.TIER_1_MOBILE,
        'desktop': ProblemTier.TIER_2_DESKTOP,
        'workstation': ProblemTier.TIER_3_WORKSTATION,
        'server': ProblemTier.TIER_4_SERVER,
        'cluster': ProblemTier.TIER_5_CLUSTER
    }
    
    tier = capacity_map.get(capacity.lower(), ProblemTier.TIER_1_MOBILE)
    
    # Create mock block
    block = Block(
        index=block_data.get('index', 0),
        timestamp=block_data.get('timestamp', time.time()),
        previous_hash=block_data.get('previous_hash', '0' * 64),
        transactions=[],
        merkle_root=block_data.get('merkle_root', '0' * 64),
        problem=None,  # Not needed for reward calculation
        solution=None,  # Not needed for reward calculation
        complexity=None,  # Will be set separately
        mining_capacity=tier,
        cumulative_work_score=block_data.get('work_score', 0.0),
        block_hash=block_data.get('block_hash', '0' * 64),
        offchain_cid=None
    )
    
    return block

def migrate_all_rewards():
    """Migrate all existing miner rewards using dynamic tokenomics."""
    print("🚀 Starting migration to dynamic tokenomics...")
    
    # Load blockchain state
    blockchain_path = '/opt/coinjecture-consensus/data/blockchain_state.json'
    if not os.path.exists(blockchain_path):
        print(f"❌ Blockchain state file not found: {blockchain_path}")
        return False
    
    with open(blockchain_path, 'r') as f:
        blockchain_data = json.load(f)
    
    print(f"📊 Found {len(blockchain_data.get('blocks', []))} blocks in blockchain state")
    
    # Initialize tokenomics system
    tokenomics = DynamicWorkScoreTokenomics()
    
    # Connect to rewards database
    db_path = '/opt/coinjecture-consensus/data/faucet_ingest.db'
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Backup existing rewards table
    print("💾 Backing up existing rewards...")
    cursor.execute('CREATE TABLE IF NOT EXISTS work_based_rewards_backup AS SELECT * FROM work_based_rewards')
    
    # Clear old data
    cursor.execute('DELETE FROM work_based_rewards')
    
    # Process all blocks in order
    blocks = blockchain_data.get('blocks', [])
    miner_rewards = {}  # address -> total_rewards
    
    print(f"🔄 Processing {len(blocks)} blocks...")
    
    for i, block in enumerate(blocks):
        if i % 1000 == 0:
            print(f"   Processed {i}/{len(blocks)} blocks...")
        
        # Extract block data
        miner_address = block.get('miner_address', 'unknown')
        work_score = block.get('work_score', 0.0)
        capacity = block.get('capacity', 'mobile')
        
        if work_score <= 0:
            continue  # Skip blocks with no work score
        
        # Create complexity object
        complexity = create_complexity_from_block(block)
        
        # Calculate reward using CORRECT tokenomics
        mock_block = create_mock_block(block, capacity)
        reward = tokenomics.calculate_block_reward(mock_block, complexity)
        
        # Record in tokenomics system
        tokenomics.record_block(mock_block, complexity, reward, miner_address)
        
        # Accumulate rewards per miner
        if miner_address not in miner_rewards:
            miner_rewards[miner_address] = {
                'total_rewards': 0.0,
                'blocks_mined': 0,
                'total_work_score': 0.0
            }
        
        miner_rewards[miner_address]['total_rewards'] += reward
        miner_rewards[miner_address]['blocks_mined'] += 1
        miner_rewards[miner_address]['total_work_score'] += work_score
    
    print(f"💰 Updating rewards for {len(miner_rewards)} miners...")
    
    # Update work_based_rewards table
    for address, data in miner_rewards.items():
        average_reward = data['total_rewards'] / data['blocks_mined']
        average_work_score = data['total_work_score'] / data['blocks_mined']
        
        cursor.execute('''
            INSERT INTO work_based_rewards 
            (miner_address, total_rewards, blocks_mined, total_work_score, 
             average_reward, average_work_score, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            address,
            data['total_rewards'],
            data['blocks_mined'],
            data['total_work_score'],
            average_reward,
            average_work_score,
            time.time()
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Migration completed successfully!")
    print(f"   Migrated rewards for {len(miner_rewards)} miners")
    print(f"   Total coins issued: {tokenomics.total_coins_issued:.6f}")
    print(f"   Cumulative work score: {tokenomics.cumulative_work_score:,.0f}")
    print(f"   Current deflation factor: {tokenomics._calculate_deflation_factor():.6f}")
    
    return True

if __name__ == "__main__":
    success = migrate_all_rewards()
    if success:
        print("🎉 Dynamic tokenomics migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)
