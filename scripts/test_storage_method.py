#!/usr/bin/env python3
"""Test storage method directly"""

import sys
import os
sys.path.append('/opt/coinjecture/src')

from api.blockchain_storage import storage

# Test get_block_data method
print("Testing storage.get_block_data(1001)...")
block_data = storage.get_block_data(1001)

if block_data:
    print(f"✅ Block data retrieved:")
    print(f"  Height: {block_data.get('index', 'N/A')}")
    print(f"  Gas Used: {block_data.get('gas_used', 'N/A')}")
    print(f"  Gas Limit: {block_data.get('gas_limit', 'N/A')}")
    print(f"  Gas Price: {block_data.get('gas_price', 'N/A')}")
    print(f"  Reward: {block_data.get('reward', 'N/A')}")
    print(f"  Work Score: {block_data.get('work_score', 'N/A')}")
else:
    print("❌ No block data returned")
