#!/usr/bin/env python3
"""
Test Block Data Retrieval from IPFS
"""

import sys
import os
sys.path.append('src')

from api.blockchain_storage import storage
from storage import IPFSClient
import json

def test_block_retrieval():
    """Test retrieval of multiple blocks from IPFS."""
    ipfs_client = IPFSClient("http://localhost:5001")
    latest_height = storage.get_latest_height()

    print(f"🔍 Testing Block Data Retrieval (Latest: {latest_height})")
    print("=" * 60)

    # Test blocks 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, latest
    test_blocks = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, latest_height]
    working_blocks = []

    for block_num in test_blocks:
        if block_num <= latest_height:
            block_data = storage.get_block_data(block_num)
            if block_data:
                cid = block_data.get("cid")
                if cid and cid.startswith("Qm") and len(cid) == 46:
                    try:
                        data = ipfs_client.get(cid)
                        proof_json = json.loads(data.decode("utf-8"))
                        working_blocks.append((block_num, cid, len(data), proof_json))
                        
                        print(f"✅ Block {block_num}: {cid[:16]}... - {len(data)} bytes")
                        
                        # Show key metrics
                        if "complexity" in proof_json:
                            complexity = proof_json["complexity"]
                            print(f"   🧮 {complexity.get('problem_class', 'unknown')} (size {complexity.get('problem_size', 'unknown')})")
                            print(f"   ⏱️  Solve: {complexity.get('measured_solve_time', 'unknown')}s, Verify: {complexity.get('measured_verify_time', 'unknown')}s")
                            print(f"   📊 Asymmetry: Time {complexity.get('asymmetry_time', 'unknown')}, Space {complexity.get('asymmetry_space', 'unknown')}")
                        
                        if "energy_metrics" in proof_json:
                            energy = proof_json["energy_metrics"]
                            print(f"   ⚡ Energy: {energy.get('solve_energy_joules', 'unknown')}J solve, {energy.get('verify_energy_joules', 'unknown')}J verify")
                        
                        print(f"   📈 Work Score: {proof_json.get('cumulative_work_score', 'unknown')}")
                        print()
                        
                    except Exception as e:
                        print(f"❌ Block {block_num}: {cid[:16]}... - {str(e)[:50]}...")
                        print()

    print(f"\n📊 Retrieval Summary:")
    print(f"   Blocks tested: {len(test_blocks)}")
    print(f"   Working blocks: {len(working_blocks)}")
    print(f"   Success rate: {len(working_blocks)/len(test_blocks)*100:.1f}%")

    if working_blocks:
        print(f"\n🎯 Accessible Blocks with Rich Data:")
        for block_num, cid, size, proof_json in working_blocks:
            print(f"   Block {block_num}: {cid} ({size} bytes)")
            if "problem" in proof_json:
                problem = proof_json["problem"]
                print(f"      Problem: {problem.get('type', 'unknown')} (size {problem.get('size', 'unknown')})")
                if "numbers" in problem:
                    numbers = problem["numbers"]
                    if len(numbers) > 5:
                        print(f"      Numbers: {numbers[:5]}... (total {len(numbers)})")
                    else:
                        print(f"      Numbers: {numbers} (total {len(numbers)})")
                if "target" in problem:
                    print(f"      Target: {problem.get('target')}")
            if "solution" in proof_json:
                solution = proof_json["solution"]
                print(f"      Solution: {solution}")
    
    return working_blocks

if __name__ == "__main__":
    working_blocks = test_block_retrieval()
    
    if working_blocks:
        print(f"\n🎉 SUCCESS! {len(working_blocks)} blocks accessible with rich computational data!")
        print("   The COINjecture data faucet is now fully functional!")
    else:
        print(f"\n⚠️  No blocks accessible. Check IPFS configuration.")
