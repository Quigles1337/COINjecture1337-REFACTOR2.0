#!/usr/bin/env python3
"""
Fetch all proof data from IPFS CIDs to display rich computational complexity data
"""

import sys
import os
sys.path.append('src')

from api.blockchain_storage import storage
from storage import IPFSClient
import json

def fetch_all_proof_data():
    # Initialize IPFS client
    ipfs_client = IPFSClient("http://localhost:5001")

    # Get all blocks from database
    print("🔍 Fetching all proof data from blockchain...")
    print("=" * 60)

    try:
        # Get latest block height
        latest_height = storage.get_latest_height()
        print(f"📊 Total blocks in chain: {latest_height + 1}")
        print()
        
        # Fetch proof data for each block
        for i in range(latest_height + 1):
            block_data = storage.get_block_data(i)
            if block_data:
                cid = block_data.get("cid")
                block_hash = block_data.get("block_hash", "unknown")
                
                print(f"📦 Block #{i} - {block_hash[:16]}...")
                print(f"   CID: {cid}")
                
                if cid and cid.startswith("Qm"):
                    try:
                        # Fetch proof bundle from IPFS
                        proof_data = ipfs_client.get(cid)
                        proof_json = json.loads(proof_data.decode("utf-8"))
                        
                        print(f"   ✅ Proof bundle retrieved: {len(proof_data)} bytes")
                        
                        # Display computational complexity data
                        if "complexity" in proof_json:
                            complexity = proof_json["complexity"]
                            print(f"   🧮 Computational Complexity:")
                            print(f"      Problem Class: {complexity.get('problem_class', 'unknown')}")
                            print(f"      Problem Size: {complexity.get('problem_size', 'unknown')}")
                            print(f"      Solution Size: {complexity.get('solution_size', 'unknown')}")
                            print(f"      Solve Time: {complexity.get('measured_solve_time', 'unknown')}s")
                            print(f"      Verify Time: {complexity.get('measured_verify_time', 'unknown')}s")
                            print(f"      Time Complexity: {complexity.get('time_solve_O', 'unknown')} solve, {complexity.get('time_verify_O', 'unknown')} verify")
                            print(f"      Space Complexity: {complexity.get('space_solve_O', 'unknown')} solve, {complexity.get('space_verify_O', 'unknown')} verify")
                            print(f"      Time Asymmetry: {complexity.get('asymmetry_time', 'unknown')}")
                            print(f"      Space Asymmetry: {complexity.get('asymmetry_space', 'unknown')}")
                        
                        # Display energy metrics
                        if "energy_metrics" in proof_json:
                            energy = proof_json["energy_metrics"]
                            print(f"   ⚡ Energy Metrics:")
                            print(f"      Solve Energy: {energy.get('solve_energy_joules', 'unknown')} J")
                            print(f"      Verify Energy: {energy.get('verify_energy_joules', 'unknown')} J")
                            print(f"      Solve Power: {energy.get('solve_power_watts', 'unknown')} W")
                            print(f"      CPU Utilization: {energy.get('cpu_utilization', 'unknown')}%")
                            print(f"      Memory Utilization: {energy.get('memory_utilization', 'unknown')}%")
                        
                        # Display problem data
                        if "problem" in proof_json:
                            problem = proof_json["problem"]
                            print(f"   🧩 Problem Data:")
                            print(f"      Type: {problem.get('type', 'unknown')}")
                            print(f"      Size: {problem.get('size', 'unknown')}")
                            if "numbers" in problem:
                                numbers = problem["numbers"]
                                if len(numbers) > 10:
                                    print(f"      Numbers: {numbers[:10]}...")
                                else:
                                    print(f"      Numbers: {numbers}")
                            if "target" in problem:
                                print(f"      Target: {problem.get('target')}")
                        
                        # Display solution data
                        if "solution" in proof_json:
                            solution = proof_json["solution"]
                            print(f"   ✅ Solution: {solution}")
                        
                        print(f"   📈 Work Score: {proof_json.get('cumulative_work_score', 'unknown')}")
                        print()
                        
                    except Exception as e:
                        print(f"   ❌ Failed to fetch proof bundle: {e}")
                        print()
                else:
                    print(f"   ⚠️  No valid CID found")
                    print()
                    
    except Exception as e:
        print(f"❌ Error fetching proof data: {e}")

if __name__ == "__main__":
    fetch_all_proof_data()
