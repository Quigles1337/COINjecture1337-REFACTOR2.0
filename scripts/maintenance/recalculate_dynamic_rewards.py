#!/usr/bin/env python3
"""
Recalculate all mining rewards using dynamic tokenomics instead of static rewards.
This fixes the issue where rewards are showing 100 BEANS per block instead of dynamic values.
"""

import sqlite3
import json
import time
import math
from typing import Dict, List, Any

def calculate_dynamic_reward(work_score: float, cumulative_work: float, block_index: int) -> float:
    """
    Calculate reward using dynamic tokenomics formula:
    reward = log(1 + work_ratio) * deflation_factor * diversity_bonus
    """
    
    # 1. Work ratio: this block's work relative to recent average
    # For simplicity, use a rolling average of recent work scores
    recent_avg_work = max(1.0, cumulative_work / max(1, block_index))  # Prevent division by zero
    
    if recent_avg_work > 0:
        work_ratio = work_score / recent_avg_work
        base_reward = math.log1p(work_ratio)  # log(1 + x) for smooth scaling
    else:
        base_reward = 1.0
    
    # 2. Deflation factor: decreases as cumulative work grows
    # Natural deflation as network matures
    deflation_factor = 1.0 / (1.0 + cumulative_work * 0.0001)  # Gradual deflation
    deflation_factor = max(0.1, deflation_factor)  # Minimum 10% of original reward
    
    # 3. Diversity bonus: encourage different mining capacities
    # For now, use a simple bonus based on work score magnitude
    diversity_bonus = 1.0 + (work_score * 0.01)  # Small bonus for higher work scores
    diversity_bonus = min(2.0, diversity_bonus)  # Cap at 2x bonus
    
    # 4. Final reward
    reward = base_reward * deflation_factor * diversity_bonus
    
    # Ensure minimum reward of 0.1 BEANS
    reward = max(0.1, reward)
    
    return reward

def recalculate_all_rewards():
    """Recalculate all mining rewards using dynamic tokenomics."""
    
    db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
    
    print("🔄 Recalculating all mining rewards using dynamic tokenomics...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all mining events from block_events table
        cursor.execute('''
            SELECT miner_address, work_score, block_index, ts
            FROM block_events 
            WHERE work_score > 0
            ORDER BY block_index
        ''')
        
        events = cursor.fetchall()
        print(f"📊 Found {len(events)} mining events to recalculate")
        
        # Group by miner address
        miner_data = {}
        for event in events:
            miner_address, work_score, block_index, timestamp = event
            
            if miner_address not in miner_data:
                miner_data[miner_address] = {
                    'events': [],
                    'total_work_score': 0.0,
                    'total_rewards': 0.0,
                    'blocks_mined': 0
                }
            
            miner_data[miner_address]['events'].append({
                'work_score': work_score,
                'block_index': block_index,
                'timestamp': timestamp
            })
            miner_data[miner_address]['total_work_score'] += work_score
            miner_data[miner_address]['blocks_mined'] += 1
        
        # Clear existing work_based_rewards table
        cursor.execute('DELETE FROM work_based_rewards')
        print("🗑️  Cleared existing static rewards")
        
        # Recalculate rewards for each miner using dynamic tokenomics
        for miner_address, data in miner_data.items():
            total_rewards = 0.0
            rewards_breakdown = []
            
            for event in data['events']:
                work_score = event['work_score']
                block_index = event['block_index']
                
                # Calculate cumulative work up to this point
                cumulative_work = sum(e['work_score'] for e in data['events'] if e['block_index'] <= block_index)
                
                # Calculate dynamic reward
                dynamic_reward = calculate_dynamic_reward(work_score, cumulative_work, block_index)
                
                total_rewards += dynamic_reward
                rewards_breakdown.append({
                    'block_index': block_index,
                    'work_score': work_score,
                    'reward': dynamic_reward
                })
            
            # Calculate average reward
            average_reward = total_rewards / data['blocks_mined'] if data['blocks_mined'] > 0 else 0.0
            
            # Insert into work_based_rewards table
            cursor.execute('''
                INSERT INTO work_based_rewards 
                (miner_address, total_rewards, blocks_mined, total_work_score, average_reward)
                VALUES (?, ?, ?, ?, ?)
            ''', (miner_address, total_rewards, data['blocks_mined'], 
                  data['total_work_score'], average_reward))
            
            print(f"💰 {miner_address[:20]}... : {total_rewards:.2f} BEANS ({data['blocks_mined']} blocks, avg: {average_reward:.2f})")
        
        # Commit changes
        conn.commit()
        print(f"✅ Successfully recalculated rewards for {len(miner_data)} miners")
        
        # Show summary statistics
        cursor.execute('SELECT COUNT(*), SUM(total_rewards), AVG(average_reward) FROM work_based_rewards')
        count, total_rewards, avg_reward = cursor.fetchone()
        
        print(f"\n📊 Summary:")
        print(f"   Miners: {count}")
        print(f"   Total rewards distributed: {total_rewards:.2f} BEANS")
        print(f"   Average reward per block: {avg_reward:.2f} BEANS")
        
    except Exception as e:
        print(f"❌ Error recalculating rewards: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    recalculate_all_rewards()
