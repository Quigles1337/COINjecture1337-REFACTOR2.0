#!/usr/bin/env python3
"""
Recalculate gas and rewards for existing blocks using metrics engine
"""

import sys
import os
import sqlite3
import json
import time
import math

# Add src to path
sys.path.append('src')

from metrics_engine import get_metrics_engine, SATOSHI_CONSTANT, ComputationalComplexity

def recalculate_block_metrics():
    """Recalculate gas and rewards for all blocks"""
    print(f"🔄 Recalculating block metrics with Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
    
    # Connect to database
    db_path = 'data/blockchain.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get metrics engine
    metrics_engine = get_metrics_engine()
    
    # Get all blocks
    cursor.execute("SELECT block_hash, height, block_bytes FROM blocks ORDER BY height")
    blocks = cursor.fetchall()
    
    print(f"📊 Found {len(blocks)} blocks to recalculate")
    
    cumulative_work = 0.0
    
    for i, (block_hash, height, block_bytes) in enumerate(blocks):
        try:
            # Parse block data
            if block_bytes:
                block_data = json.loads(block_bytes)
            else:
                print(f"⚠️  Block {height} has no data, skipping")
                continue
            
            # Get work score from block
            work_score = block_data.get('work_score', 1.0)
            
            # Calculate complexity metrics (simplified)
            complexity = ComputationalComplexity(
                time_asymmetry=1.0,
                space_asymmetry=1.0,
                problem_weight=1.0,
                size_factor=math.log(work_score + 1),
                quality_score=1.0,
                energy_efficiency=1.0
            )
            
            # Calculate gas cost
            gas_used = metrics_engine.calculate_gas_cost("block_validation", complexity)
            gas_limit = 1000000
            gas_price = 0.000001
            
            # Calculate reward
            network_state = metrics_engine.network_state
            network_state.cumulative_work = cumulative_work
            network_state.block_count = height
            
            reward = metrics_engine.calculate_block_reward(work_score, network_state)
            
            # Update cumulative work
            cumulative_work += work_score
            
            # Update database
            cursor.execute('''
                UPDATE blocks 
                SET work_score = ?, gas_used = ?, gas_limit = ?, gas_price = ?, reward = ?, cumulative_work = ?
                WHERE block_hash = ?
            ''', (work_score, gas_used, gas_limit, gas_price, reward, cumulative_work, block_hash))
            
            if i % 100 == 0:
                print(f"✅ Processed block {height}: gas={gas_used}, reward={reward:.6f}")
                
        except Exception as e:
            print(f"❌ Error processing block {height}: {e}")
            continue
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"✅ Recalculated metrics for {len(blocks)} blocks")
    print(f"📊 Final cumulative work: {cumulative_work:.6f}")

if __name__ == "__main__":
    recalculate_block_metrics()
