#!/usr/bin/env python3
"""
Analyze Existing Equilibrium from Production Data
Analyzes 12,000+ blocks to validate equilibrium theory against real network behavior
"""

import json
import sqlite3
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict

# Try to import numpy and pandas, but make optional
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None


class EquilibriumAnalyzer:
    """Analyze existing blockchain data for equilibrium patterns."""
    
    def __init__(self, blockchain_db_path: str = "data/blockchain.db"):
        # Try multiple possible paths
        possible_paths = [
            blockchain_db_path,
            "data/blockchain.db",
            "/opt/coinjecture/data/blockchain.db",
            "/root/data/blockchain.db"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.db_path = path
                break
        else:
            self.db_path = blockchain_db_path
        
        self.conn = None
        self.blocks = []
        
    def load_blocks(self) -> List[Dict]:
        """Load all blocks from database."""
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return []
        
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        print(f"📦 Loading blocks from {self.db_path}...")
        
        try:
            # Try to get blocks with all fields
            cursor.execute('''
                SELECT block_hash, block_bytes, height, timestamp 
                FROM blocks 
                ORDER BY height ASC
            ''')
            rows = cursor.fetchall()
            
            blocks = []
            for block_hash, block_bytes, height, timestamp in rows:
                try:
                    # Parse block_bytes JSON
                    if block_bytes:
                        if isinstance(block_bytes, bytes):
                            block_data = json.loads(block_bytes.decode('utf-8'))
                        else:
                            block_data = json.loads(block_bytes)
                        
                        block = {
                            'index': height,
                            'block_hash': block_hash.decode('utf-8') if isinstance(block_hash, bytes) else block_hash,
                            'timestamp': block_data.get('timestamp', timestamp or 0),
                            'cid': block_data.get('cid') or block_data.get('offchain_cid') or block_data.get('ipfs_cid'),
                            'miner_address': block_data.get('miner_address', 'unknown'),
                            'mining_capacity': block_data.get('capacity', 'unknown'),
                            'work_score': block_data.get('work_score', block_data.get('cumulative_work_score', 0)),
                            'problem_data': block_data.get('problem_data', {}),
                            'solution_data': block_data.get('solution_data', [])
                        }
                        blocks.append(block)
                except Exception as e:
                    print(f"⚠️  Error parsing block {height}: {e}")
                    continue
            
            print(f"✅ Loaded {len(blocks)} blocks")
            self.blocks = blocks
            return blocks
            
        except Exception as e:
            print(f"❌ Error loading blocks: {e}")
            return []
    
    def calculate_block_intervals(self) -> List[float]:
        """Calculate time between consecutive blocks."""
        if len(self.blocks) < 2:
            return []
        
        intervals = []
        for i in range(1, len(self.blocks)):
            prev_time = self.blocks[i-1]['timestamp']
            curr_time = self.blocks[i]['timestamp']
            interval = curr_time - prev_time if curr_time > prev_time else 0
            intervals.append(interval)
        
        if not intervals:
            return []
        
        if HAS_NUMPY:
            intervals_arr = np.array(intervals)
            mean_interval = np.mean(intervals_arr)
            median_interval = np.median(intervals_arr)
            std_interval = np.std(intervals_arr)
            min_interval = np.min(intervals_arr)
            max_interval = np.max(intervals_arr)
        else:
            intervals_arr = intervals
            mean_interval = sum(intervals) / len(intervals)
            sorted_intervals = sorted(intervals)
            median_interval = sorted_intervals[len(sorted_intervals) // 2]
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            std_interval = variance ** 0.5
            min_interval = min(intervals)
            max_interval = max(intervals)
        
        print(f"\n⏱️  Block Interval Stats:")
        print(f"   Total intervals: {len(intervals)}")
        print(f"   Mean: {mean_interval:.2f}s")
        print(f"   Median: {median_interval:.2f}s")
        print(f"   Std Dev: {std_interval:.2f}s")
        print(f"   Min: {min_interval:.2f}s")
        print(f"   Max: {max_interval:.2f}s")
        print(f"   Target (from λ=0.7071): 14.14s")
        
        return intervals
    
    def detect_bursts(self, intervals: List[float], threshold: float = 5.0) -> List[tuple]:
        """Detect burst periods (multiple blocks < threshold seconds apart)."""
        bursts = []
        in_burst = False
        burst_start = 0
        
        for i, interval in enumerate(intervals):
            if interval < threshold and interval > 0:
                if not in_burst:
                    burst_start = i
                    in_burst = True
            else:
                if in_burst:
                    burst_end = i
                    burst_size = burst_end - burst_start
                    bursts.append((burst_start, burst_end, burst_size))
                    in_burst = False
        
        if bursts:
            avg_burst_size = sum(b[2] for b in bursts) / len(bursts)
            print(f"\n💥 Detected {len(bursts)} burst periods (blocks <{threshold}s apart)")
            print(f"   Average burst size: {avg_burst_size:.1f} blocks")
            print(f"   Largest burst: {max(b[2] for b in bursts)} blocks")
        else:
            print(f"\n✅ No burst periods detected (all intervals >{threshold}s)")
        
        return bursts
    
    def analyze_cid_failures(self) -> Dict:
        """Analyze CID upload success/failure patterns."""
        total_blocks = len(self.blocks)
        blocks_with_cid = sum(1 for b in self.blocks if b.get('cid'))
        blocks_without_cid = total_blocks - blocks_with_cid
        
        success_rate = (blocks_with_cid / total_blocks * 100) if total_blocks > 0 else 0
        
        print(f"\n📡 CID Upload Analysis:")
        print(f"   Total blocks: {total_blocks:,}")
        print(f"   Blocks with CID: {blocks_with_cid:,} ({success_rate:.1f}%)")
        print(f"   Blocks without CID: {blocks_without_cid:,} ({100-success_rate:.1f}%)")
        
        # Analyze CID distribution over time
        if total_blocks > 100:
            # Split into 10 windows
            window_size = total_blocks // 10
            cid_rates = []
            for i in range(0, total_blocks, window_size):
                window = self.blocks[i:i+window_size]
                window_cids = sum(1 for b in window if b.get('cid'))
                window_rate = (window_cids / len(window) * 100) if window else 0
                cid_rates.append(window_rate)
            
            if cid_rates:
                avg_rate = sum(cid_rates) / len(cid_rates)
                min_rate = min(cid_rates)
                max_rate = max(cid_rates)
                print(f"   CID rate over time: {min_rate:.1f}% - {max_rate:.1f}% (avg: {avg_rate:.1f}%)")
        
        return {
            'total': total_blocks,
            'success': blocks_with_cid,
            'failure': blocks_without_cid,
            'success_rate': success_rate
        }
    
    def calculate_network_lambda(self, window_size: int = 100) -> List[float]:
        """Estimate λ (coupling) from historical data."""
        intervals = self.calculate_block_intervals()
        
        if len(intervals) < window_size:
            return []
        
        lambda_values = []
        target = 14.14  # From λ = 0.7071 → 1/λ * 10
        
        for i in range(0, len(intervals) - window_size, window_size):
            window = intervals[i:i+window_size]
            
            if HAS_NUMPY:
                avg_interval = np.mean(window)
            else:
                avg_interval = sum(window) / len(window)
            
            # λ ≈ target / avg_interval
            # Higher λ = faster propagation = smaller intervals
            lambda_est = target / avg_interval if avg_interval > 0 else 0
            lambda_values.append(lambda_est)
        
        if lambda_values:
            if HAS_NUMPY:
                mean_lambda = np.mean(lambda_values)
                std_lambda = np.std(lambda_values)
            else:
                mean_lambda = sum(lambda_values) / len(lambda_values)
                variance = sum((x - mean_lambda) ** 2 for x in lambda_values) / len(lambda_values)
                std_lambda = variance ** 0.5
            
            print(f"\n📊 Network Coupling (λ) Analysis:")
            print(f"   Mean λ: {mean_lambda:.4f} ± {std_lambda:.4f}")
            print(f"   Target λ: 0.7071")
            print(f"   Deviation: {abs(mean_lambda - 0.7071):.4f}")
        
        return lambda_values
    
    def calculate_network_eta(self, intervals: List[float], window_size: int = 100) -> List[float]:
        """Estimate η (damping) from historical data."""
        if len(intervals) < window_size:
            return []
        
        eta_values = []
        
        for i in range(0, len(intervals) - window_size, window_size):
            window = intervals[i:i+window_size]
            
            if HAS_NUMPY:
                mean_interval = np.mean(window)
                std_interval = np.std(window)
            else:
                mean_interval = sum(window) / len(window)
                variance = sum((x - mean_interval) ** 2 for x in window) / len(window)
                std_interval = variance ** 0.5
            
            # η ≈ 1 / (1 + coefficient of variation)
            # Lower variance = higher damping = more stable
            cv = std_interval / mean_interval if mean_interval > 0 else 0
            eta_est = 1 / (1 + cv) if cv > 0 else 0
            eta_values.append(eta_est)
        
        if eta_values:
            if HAS_NUMPY:
                mean_eta = np.mean(eta_values)
                std_eta = np.std(eta_values)
            else:
                mean_eta = sum(eta_values) / len(eta_values)
                variance = sum((x - mean_eta) ** 2 for x in eta_values) / len(eta_values)
                std_eta = variance ** 0.5
            
            print(f"\n📊 Network Damping (η) Analysis:")
            print(f"   Mean η: {mean_eta:.4f} ± {std_eta:.4f}")
            print(f"   Target η: 0.7071")
            print(f"   Deviation: {abs(mean_eta - 0.7071):.4f}")
        
        return eta_values
    
    def correlate_failures_with_equilibrium(self, intervals: List[float]):
        """Check if CID failures correlate with equilibrium deviation."""
        failed_blocks = [b for b in self.blocks if not b.get('cid')]
        
        if len(failed_blocks) == 0:
            print("\n✅ No CID failures detected!")
            return
        
        print(f"\n🔍 Analyzing {len(failed_blocks)} blocks with CID failures...")
        
        # Calculate intervals around failed blocks
        intervals_before_failures = []
        target = 14.14
        
        for block in failed_blocks:
            block_index = block['index']
            if block_index > 0 and block_index < len(self.blocks):
                # Find previous block
                prev_block = None
                for b in self.blocks:
                    if b['index'] == block_index - 1:
                        prev_block = b
                        break
                
                if prev_block:
                    interval = block['timestamp'] - prev_block['timestamp']
                    if interval > 0:
                        intervals_before_failures.append(interval)
        
        if intervals_before_failures:
            if HAS_NUMPY:
                avg_interval_at_failure = np.mean(intervals_before_failures)
            else:
                avg_interval_at_failure = sum(intervals_before_failures) / len(intervals_before_failures)
            
            deviation = abs(avg_interval_at_failure - target)
            
            print(f"   Avg interval before failure: {avg_interval_at_failure:.2f}s")
            print(f"   Target interval: {target:.2f}s")
            print(f"   Deviation: {deviation:.2f}s")
            
            if deviation > 5.0:
                print(f"   ⚠️  Failures occur when intervals deviate significantly from target")
            else:
                print(f"   ✅ Failures don't correlate strongly with interval deviation")
    
    def plot_equilibrium_history(self, lambda_values: List[float], eta_values: List[float]):
        """Plot λ and η over blockchain history."""
        if not (HAS_MATPLOTLIB and HAS_NUMPY):
            print("\n⚠️  matplotlib/numpy not available - skipping plots")
            return
        
        if not lambda_values or not eta_values:
            print("\n⚠️  Insufficient data for plotting")
            return
        
        try:
            fig, axes = plt.subplots(3, 1, figsize=(14, 10))
            
            lambda_arr = np.array(lambda_values)
            eta_arr = np.array(eta_values)
            
            # Plot λ
            axes[0].plot(lambda_arr, label='Estimated λ', color='blue', alpha=0.7, linewidth=1.5)
            axes[0].axhline(y=0.7071, color='red', linestyle='--', linewidth=2, label='Target λ = 0.7071')
            axes[0].fill_between(range(len(lambda_arr)), 0.6571, 0.7571, alpha=0.2, color='red', label='Target Range ±0.05')
            axes[0].set_title('Network Coupling (λ) Over Blockchain History', fontsize=14, fontweight='bold')
            axes[0].set_ylabel('λ value', fontsize=12)
            axes[0].legend(loc='upper right')
            axes[0].grid(alpha=0.3)
            
            # Plot η
            axes[1].plot(eta_arr, label='Estimated η', color='green', alpha=0.7, linewidth=1.5)
            axes[1].axhline(y=0.7071, color='red', linestyle='--', linewidth=2, label='Target η = 0.7071')
            axes[1].fill_between(range(len(eta_arr)), 0.6571, 0.7571, alpha=0.2, color='red', label='Target Range ±0.05')
            axes[1].set_title('Network Damping (η) Over Blockchain History', fontsize=14, fontweight='bold')
            axes[1].set_ylabel('η value', fontsize=12)
            axes[1].legend(loc='upper right')
            axes[1].grid(alpha=0.3)
            
            # Plot λ/η ratio
            ratio = lambda_arr / np.maximum(eta_arr, 0.001)
            axes[2].plot(ratio, label='λ/η ratio', color='purple', alpha=0.7, linewidth=1.5)
            axes[2].axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Target = 1.0')
            axes[2].fill_between(range(len(ratio)), 0.9, 1.1, alpha=0.2, color='red', label='Target Range ±0.1')
            axes[2].set_title('Equilibrium Ratio (λ/η) Over Blockchain History', fontsize=14, fontweight='bold')
            axes[2].set_ylabel('Ratio', fontsize=12)
            axes[2].set_xlabel('Block Window (×100)', fontsize=12)
            axes[2].legend(loc='upper right')
            axes[2].grid(alpha=0.3)
            
            plt.tight_layout()
            
            output_path = 'historical_equilibrium.png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"\n📈 Plot saved to {output_path}")
            plt.close()
            
            # Calculate statistics
            mean_ratio = np.mean(ratio)
            std_ratio = np.std(ratio)
            at_equilibrium = np.sum((ratio > 0.9) & (ratio < 1.1))
            equilibrium_pct = (at_equilibrium / len(ratio) * 100) if len(ratio) > 0 else 0
            
            print(f"\n⚖️  Historical Equilibrium Summary:")
            print(f"   λ: {np.mean(lambda_arr):.4f} ± {np.std(lambda_arr):.4f}")
            print(f"   η: {np.mean(eta_arr):.4f} ± {np.std(eta_arr):.4f}")
            print(f"   λ/η ratio: {mean_ratio:.4f} ± {std_ratio:.4f}")
            print(f"   Time at equilibrium (0.9-1.1): {equilibrium_pct:.1f}%")
            
        except Exception as e:
            print(f"⚠️  Error generating plot: {e}")
    
    def generate_report(self):
        """Generate comprehensive equilibrium report."""
        print("=" * 70)
        print("COINjecture Historical Equilibrium Analysis")
        print("=" * 70)
        
        # Load blocks
        blocks = self.load_blocks()
        if not blocks:
            print("❌ No blocks loaded. Cannot generate report.")
            return
        
        print(f"\nAnalyzing {len(blocks)} blocks from production")
        print(f"Date range: Block {blocks[0]['index']} to Block {blocks[-1]['index']}")
        print(f"Time span: {(blocks[-1]['timestamp'] - blocks[0]['timestamp']) / 86400:.1f} days")
        
        # Basic metrics
        intervals = self.calculate_block_intervals()
        bursts = self.detect_bursts(intervals) if intervals else []
        cid_stats = self.analyze_cid_failures()
        
        # Equilibrium analysis
        lambda_values = self.calculate_network_lambda()
        eta_values = self.calculate_network_eta(intervals) if intervals else []
        
        # Plot if available
        if lambda_values and eta_values:
            self.plot_equilibrium_history(lambda_values, eta_values)
        
        # Correlation analysis
        if intervals:
            self.correlate_failures_with_equilibrium(intervals)
        
        # Final summary
        print("\n" + "=" * 70)
        print("📋 SUMMARY")
        print("=" * 70)
        print(f"Total Blocks: {len(blocks):,}")
        print(f"CID Success Rate: {cid_stats['success_rate']:.1f}%")
        print(f"Burst Events: {len(bursts)}")
        if intervals:
            if HAS_NUMPY:
                mean_interval = np.mean(intervals)
            else:
                mean_interval = sum(intervals) / len(intervals)
            print(f"Mean Block Interval: {mean_interval:.2f}s")
            print(f"Target Interval (from λ=0.7071): 14.14s")
            print(f"Interval Deviation: {abs(mean_interval - 14.14):.2f}s")
        
        if lambda_values and HAS_NUMPY:
            mean_lambda = np.mean(lambda_values)
            mean_eta = np.mean(eta_values) if eta_values else 0
            print(f"\nNetwork State:")
            print(f"  λ (Coupling): {mean_lambda:.4f} (target: 0.7071)")
            print(f"  η (Damping): {mean_eta:.4f} (target: 0.7071)")
            if mean_eta > 0:
                ratio = mean_lambda / mean_eta
                print(f"  λ/η Ratio: {ratio:.4f} (target: 1.0)")
        
        print("=" * 70)


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze existing blockchain for equilibrium patterns')
    parser.add_argument('--db', default='data/blockchain.db', help='Database path')
    
    args = parser.parse_args()
    
    analyzer = EquilibriumAnalyzer(blockchain_db_path=args.db)
    analyzer.generate_report()


if __name__ == "__main__":
    main()

