#!/usr/bin/env python3
"""
Check Regeneration Readiness
Verifies all conditions are met before regenerating missing CIDs
"""

import sqlite3
import json
import os
import sys
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class RegenerationReadinessChecker:
    """Check if system is ready for CID regeneration."""
    
    def __init__(self, db_path: str = "data/blockchain.db", ipfs_url: str = "http://localhost:5001"):
        self.db_path = db_path
        self.ipfs_url = ipfs_url
        self.checks = {}
    
    def check_ipfs(self) -> bool:
        """Check if IPFS daemon is running."""
        print("🌐 Checking IPFS daemon...")
        try:
            response = requests.post(f"{self.ipfs_url}/api/v0/version", timeout=5)
            if response.status_code == 200:
                version = response.json().get('Version', 'unknown')
                print(f"   ✅ IPFS daemon is running (version: {version})")
                self.checks['ipfs'] = True
                return True
            else:
                print(f"   ❌ IPFS daemon returned status {response.status_code}")
                self.checks['ipfs'] = False
                return False
        except requests.exceptions.ConnectionError:
            print(f"   ❌ IPFS daemon not available (connection refused)")
            print(f"      Start with: ipfs daemon")
            self.checks['ipfs'] = False
            return False
        except Exception as e:
            print(f"   ❌ IPFS check failed: {e}")
            self.checks['ipfs'] = False
            return False
    
    def check_recent_cid_rate(self, window_size: int = 100) -> Dict:
        """Check CID success rate in recent blocks."""
        print(f"\n📊 Checking recent CID success rate (last {window_size} blocks)...")
        
        if not os.path.exists(self.db_path):
            print(f"   ❌ Database not found: {self.db_path}")
            self.checks['cid_rate'] = False
            return {'rate': 0, 'total': 0}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT height, block_bytes 
                FROM blocks 
                ORDER BY height DESC 
                LIMIT ?
            ''', (window_size,))
            
            blocks = cursor.fetchall()
            recent_with_cid = 0
            
            for height, block_bytes in blocks:
                try:
                    if block_bytes:
                        block_data = json.loads(
                            block_bytes.decode('utf-8') if isinstance(block_bytes, bytes) else block_bytes
                        )
                        if block_data.get('cid') or block_data.get('offchain_cid') or block_data.get('ipfs_cid'):
                            recent_with_cid += 1
                except:
                    pass
            
            cid_rate = (recent_with_cid / len(blocks) * 100) if blocks else 0
            
            print(f"   Recent blocks: {len(blocks)}")
            print(f"   Blocks with CID: {recent_with_cid} ({cid_rate:.1f}%)")
            print(f"   Target: >90%")
            
            if cid_rate >= 90:
                print(f"   ✅ CID rate is good (>=90%)")
                self.checks['cid_rate'] = True
            elif cid_rate >= 75:
                print(f"   ⚠️  CID rate is improving but not stable yet ({cid_rate:.1f}%)")
                self.checks['cid_rate'] = False
            else:
                print(f"   ❌ CID rate too low ({cid_rate:.1f}%)")
                self.checks['cid_rate'] = False
            
            return {'rate': cid_rate, 'total': len(blocks), 'with_cid': recent_with_cid}
            
        except Exception as e:
            print(f"   ❌ Error checking CID rate: {e}")
            self.checks['cid_rate'] = False
            return {'rate': 0, 'total': 0}
        finally:
            conn.close()
    
    def check_block_intervals(self, window_size: int = 100) -> Dict:
        """Check if block intervals are close to target (14.14s)."""
        print(f"\n⏱️  Checking block intervals (last {window_size} blocks)...")
        
        if not os.path.exists(self.db_path):
            print(f"   ❌ Database not found: {self.db_path}")
            self.checks['intervals'] = False
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT height, timestamp 
                FROM blocks 
                ORDER BY height DESC 
                LIMIT ?
            ''', (window_size,))
            
            blocks = cursor.fetchall()
            intervals = []
            
            # Calculate intervals
            prev_time = None
            for height, timestamp in reversed(blocks):
                if prev_time and timestamp:
                    interval = timestamp - prev_time if timestamp > prev_time else 0
                    if interval > 0 and interval < 3600:  # Ignore huge gaps
                        intervals.append(interval)
                prev_time = timestamp
            
            if not intervals:
                print(f"   ⚠️  Not enough interval data")
                self.checks['intervals'] = False
                return {}
            
            avg_interval = sum(intervals) / len(intervals)
            target = 14.14
            
            print(f"   Average interval: {avg_interval:.2f}s")
            print(f"   Target interval: {target:.2f}s")
            print(f"   Deviation: {abs(avg_interval - target):.2f}s")
            
            if abs(avg_interval - target) < 30:  # Within 30 seconds
                print(f"   ✅ Intervals are close to target (<30s deviation)")
                self.checks['intervals'] = True
            elif abs(avg_interval - target) < 60:
                print(f"   ⚠️  Intervals improving but not stable yet")
                self.checks['intervals'] = False
            else:
                print(f"   ❌ Intervals too far from target (>60s deviation)")
                self.checks['intervals'] = False
            
            return {
                'avg': avg_interval,
                'target': target,
                'deviation': abs(avg_interval - target)
            }
            
        except Exception as e:
            print(f"   ❌ Error checking intervals: {e}")
            self.checks['intervals'] = False
            return {}
        finally:
            conn.close()
    
    def check_equilibrium_logs(self, minutes: int = 30) -> bool:
        """Check for equilibrium activity in logs."""
        print(f"\n⚖️  Checking equilibrium logs (last {minutes} minutes)...")
        
        # This would require systemctl/journalctl access
        # For now, just report
        print(f"   ℹ️  Check logs manually:")
        print(f"      journalctl -u coinjecture-api --since '{minutes} minutes ago' | grep Equilibrium")
        print(f"   Look for: ⚖️  Equilibrium update: λ=0.7071, η=0.7130, ratio=1.0000")
        
        self.checks['equilibrium_logs'] = True  # Assume OK for now
        return True
    
    def check_missing_cid_count(self) -> int:
        """Check how many CIDs need regeneration."""
        print(f"\n📋 Checking missing CID count...")
        
        if not os.path.exists(self.db_path):
            print(f"   ❌ Database not found: {self.db_path}")
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if missing_cid_index exists
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='missing_cid_index'
            ''')
            
            if cursor.fetchone():
                cursor.execute('SELECT COUNT(*) FROM missing_cid_index WHERE needs_regeneration = 1')
                count = cursor.fetchone()[0]
                print(f"   Blocks needing regeneration: {count:,}")
                self.checks['missing_count'] = count
                return count
            else:
                print(f"   ⚠️  missing_cid_index table not found")
                print(f"      Run: python scripts/catalog_and_regenerate_cids.py --catalog --create-index")
                return 0
                
        except Exception as e:
            print(f"   ❌ Error checking missing CIDs: {e}")
            return 0
        finally:
            conn.close()
    
    def check_all(self) -> bool:
        """Run all readiness checks."""
        print("=" * 70)
        print("🔍 CID Regeneration Readiness Check")
        print("=" * 70)
        print("")
        
        # Run all checks
        ipfs_ok = self.check_ipfs()
        cid_stats = self.check_recent_cid_rate()
        interval_stats = self.check_block_intervals()
        missing_count = self.check_missing_cid_count()
        self.check_equilibrium_logs()
        
        # Summary
        print("\n" + "=" * 70)
        print("📋 Readiness Summary")
        print("=" * 70)
        print("")
        
        all_checks = [
            ('IPFS Available', ipfs_ok),
            ('CID Rate >= 90%', self.checks.get('cid_rate', False)),
            ('Intervals Stable', self.checks.get('intervals', False)),
            ('Missing CIDs Indexed', missing_count > 0)
        ]
        
        passed = sum(1 for _, ok in all_checks if ok)
        total = len(all_checks)
        
        for name, ok in all_checks:
            status = "✅" if ok else "❌"
            print(f"  {status} {name}")
        
        print("")
        
        if passed == total:
            print("✅ READY TO REGENERATE!")
            print("")
            print("Run:")
            print("  python scripts/catalog_and_regenerate_cids.py --regenerate --max-blocks 100  # Test first")
            print("  python scripts/catalog_and_regenerate_cids.py --regenerate  # Full regeneration")
            return True
        else:
            print(f"⏳ NOT READY YET ({passed}/{total} checks passed)")
            print("")
            print("Waiting for:")
            for name, ok in all_checks:
                if not ok:
                    print(f"  • {name}")
            print("")
            print("Once all checks pass, run regeneration.")
            return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check readiness for CID regeneration')
    parser.add_argument('--db', default='data/blockchain.db', help='Database path')
    parser.add_argument('--ipfs', default='http://localhost:5001', help='IPFS API URL')
    
    args = parser.parse_args()
    
    checker = RegenerationReadinessChecker(db_path=args.db, ipfs_url=args.ipfs)
    ready = checker.check_all()
    
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()

