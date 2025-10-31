#!/usr/bin/env python3
"""
CID Catalog and Regeneration System
Catalogs all CIDs from 13,183 production blocks
Regenerates missing CIDs once equilibrium is stable

PRODUCTION DATA ANALYSIS:
- Total Blocks: 13,183
- Blocks with CID: 8,147 (61.8%)
- Blocks without CID: 5,036 (38.2%)
- Regeneration will restore missing CIDs after equilibrium stabilizes
"""

import sqlite3
import json
import os
import sys
import time
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from storage import IPFSClient
    HAS_IPFS = True
except ImportError:
    HAS_IPFS = False
    IPFSClient = None


class CIDCatalog:
    """Comprehensive CID catalog and regeneration system."""
    
    def __init__(self, db_path: str = "data/blockchain.db", ipfs_url: str = "http://localhost:5001"):
        self.db_path = db_path
        self.ipfs_url = ipfs_url
        self.ipfs_client = None
        self.catalog = {}  # cid -> block_info
        self.missing_cids = []  # blocks needing CIDs
        self.stats = {
            'total_blocks': 0,
            'blocks_with_cid': 0,
            'blocks_without_cid': 0,
            'unique_cids': set(),
            'invalid_cids': []
        }
    
    def initialize_ipfs(self) -> bool:
        """Initialize IPFS client if available."""
        if not HAS_IPFS:
            print("⚠️  IPFS client not available - regeneration will be skipped")
            return False
        
        try:
            self.ipfs_client = IPFSClient(self.ipfs_url)
            if self.ipfs_client.health_check():
                print("✅ IPFS client initialized")
                return True
            else:
                print("⚠️  IPFS daemon not available - regeneration will be skipped")
                return False
        except Exception as e:
            print(f"⚠️  IPFS initialization failed: {e}")
            return False
    
    def catalog_all_blocks(self) -> Dict:
        """Catalog all CIDs in the database."""
        print("📊 Cataloging all CIDs in production database...")
        print("=" * 70)
        
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get all blocks
            cursor.execute('''
                SELECT height, block_hash, block_bytes, timestamp
                FROM blocks
                ORDER BY height ASC
            ''')
            rows = cursor.fetchall()
            
            self.stats['total_blocks'] = len(rows)
            print(f"📦 Processing {len(rows):,} blocks...")
            
            for height, block_hash, block_bytes, timestamp in rows:
                try:
                    # Parse block data
                    if block_bytes:
                        if isinstance(block_bytes, bytes):
                            block_data = json.loads(block_bytes.decode('utf-8'))
                        else:
                            block_data = json.loads(block_bytes)
                    else:
                        block_data = {}
                    
                    cid = block_data.get('cid') or block_data.get('offchain_cid') or block_data.get('ipfs_cid')
                    
                    if cid:
                        # Validate CID format
                        if self._validate_cid_format(cid):
                            self.stats['blocks_with_cid'] += 1
                            self.stats['unique_cids'].add(cid)
                            
                            # Add to catalog
                            if cid not in self.catalog:
                                self.catalog[cid] = {
                                    'first_block': height,
                                    'last_block': height,
                                    'blocks': []
                                }
                            
                            self.catalog[cid]['blocks'].append({
                                'height': height,
                                'block_hash': block_hash.decode('utf-8') if isinstance(block_hash, bytes) else block_hash,
                                'timestamp': block_data.get('timestamp', timestamp or 0)
                            })
                            
                            # Update first/last
                            if height < self.catalog[cid]['first_block']:
                                self.catalog[cid]['first_block'] = height
                            if height > self.catalog[cid]['last_block']:
                                self.catalog[cid]['last_block'] = height
                        else:
                            self.stats['invalid_cids'].append({
                                'height': height,
                                'cid': cid
                            })
                    else:
                        # Missing CID
                        self.stats['blocks_without_cid'] += 1
                        self.missing_cids.append({
                            'height': height,
                            'block_hash': block_hash.decode('utf-8') if isinstance(block_hash, bytes) else block_hash,
                            'timestamp': block_data.get('timestamp', timestamp or 0),
                            'block_data': block_data
                        })
                    
                    # Progress
                    if (height + 1) % 1000 == 0:
                        print(f"   Processed {height + 1:,}/{len(rows):,} blocks...")
                
                except Exception as e:
                    print(f"⚠️  Error processing block {height}: {e}")
                    continue
            
            conn.close()
            
            # Finalize stats
            self.stats['unique_cids'] = len(self.stats['unique_cids'])
            
            return self.stats
            
        except Exception as e:
            print(f"❌ Error cataloging blocks: {e}")
            if conn:
                conn.close()
            return {}
    
    def _validate_cid_format(self, cid: str) -> bool:
        """Validate CID format (CIDv0: 46 chars, starts with Qm)."""
        if not cid:
            return False
        
        if len(cid) != 46:
            return False
        
        if not cid.startswith('Qm'):
            return False
        
        # Check base58btc characters (no 0, O, I, l)
        import re
        base58btc_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
        return bool(re.match(base58btc_pattern, cid))
    
    def create_cid_index_table(self) -> bool:
        """Create dedicated CID index table for fast lookups."""
        print("\n📑 Creating CID index table...")
        
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create CID index table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cid_index (
                    cid TEXT PRIMARY KEY,
                    first_block_height INTEGER,
                    last_block_height INTEGER,
                    block_count INTEGER DEFAULT 1,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cid_index_height ON cid_index(first_block_height, last_block_height)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cid_index_created ON cid_index(created_at)')
            
            # Populate from catalog
            print(f"   Populating CID index with {len(self.catalog)} CIDs...")
            for cid, info in self.catalog.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO cid_index 
                    (cid, first_block_height, last_block_height, block_count, updated_at)
                    VALUES (?, ?, ?, ?, strftime('%s', 'now'))
                ''', (
                    cid,
                    info['first_block'],
                    info['last_block'],
                    len(info['blocks'])
                ))
            
            conn.commit()
            print(f"✅ CID index created with {len(self.catalog):,} entries")
            
        except Exception as e:
            print(f"❌ Error creating CID index: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
        
        return True
    
    def create_missing_cid_index(self) -> bool:
        """Create index of blocks missing CIDs."""
        print("\n📋 Creating missing CID index...")
        
        if not os.path.exists(self.db_path):
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create missing CID index
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS missing_cid_index (
                    height INTEGER PRIMARY KEY,
                    block_hash TEXT NOT NULL,
                    timestamp INTEGER,
                    needs_regeneration BOOLEAN DEFAULT 1,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # Create index
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_missing_cid_height ON missing_cid_index(height)')
            
            # Populate from missing list
            print(f"   Indexing {len(self.missing_cids):,} blocks missing CIDs...")
            for block in self.missing_cids:
                cursor.execute('''
                    INSERT OR REPLACE INTO missing_cid_index 
                    (height, block_hash, timestamp, needs_regeneration)
                    VALUES (?, ?, ?, 1)
                ''', (
                    block['height'],
                    block['block_hash'],
                    block['timestamp']
                ))
            
            conn.commit()
            print(f"✅ Missing CID index created with {len(self.missing_cids):,} entries")
            
        except Exception as e:
            print(f"❌ Error creating missing CID index: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
        
        return True
    
    def generate_report(self) -> str:
        """Generate comprehensive catalog report."""
        report = []
        report.append("=" * 70)
        report.append("📊 CID Catalog Report")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("📈 Statistics:")
        report.append(f"  Total Blocks:           {self.stats['total_blocks']:,}")
        report.append(f"  Blocks with CID:        {self.stats['blocks_with_cid']:,} ({self.stats['blocks_with_cid']/max(self.stats['total_blocks'],1)*100:.1f}%)")
        report.append(f"  Blocks without CID:     {self.stats['blocks_without_cid']:,} ({self.stats['blocks_without_cid']/max(self.stats['total_blocks'],1)*100:.1f}%)")
        report.append(f"  Unique CIDs:            {self.stats['unique_cids']:,}")
        report.append("")
        
        if self.stats['invalid_cids']:
            report.append(f"⚠️  Invalid CIDs: {len(self.stats['invalid_cids'])}")
            for invalid in self.stats['invalid_cids'][:10]:
                report.append(f"    - Block {invalid['height']}: {invalid['cid'][:20]}...")
            if len(self.stats['invalid_cids']) > 10:
                report.append(f"    ... and {len(self.stats['invalid_cids']) - 10} more")
            report.append("")
        
        report.append("📋 Regeneration Status:")
        report.append(f"  Blocks needing regeneration: {len(self.missing_cids):,}")
        report.append(f"  Ready to regenerate: {'Yes' if self.ipfs_client else 'No (IPFS not available)'}")
        report.append("")
        
        report.append("🎯 Next Steps:")
        report.append("  1. Wait for equilibrium to stabilize (monitor λ/η ratio)")
        report.append("  2. Run regeneration: python scripts/catalog_and_regenerate_cids.py --regenerate")
        report.append("  3. Verify all CIDs restored")
        report.append("")
        
        return "\n".join(report)
    
    def regenerate_missing_cids(self, batch_size: int = 100, max_blocks: Optional[int] = None) -> Dict:
        """Regenerate missing CIDs for blocks."""
        if not self.ipfs_client:
            print("❌ IPFS client not available - cannot regenerate CIDs")
            return {'success': 0, 'failed': len(self.missing_cids)}
        
        print("\n🔄 Regenerating missing CIDs...")
        print(f"   Blocks to regenerate: {len(self.missing_cids):,}")
        
        if max_blocks:
            blocks_to_regenerate = self.missing_cids[:max_blocks]
        else:
            blocks_to_regenerate = self.missing_cids
        
        print(f"   Processing: {len(blocks_to_regenerate):,} blocks")
        print("   (This will run once equilibrium is stable)")
        print("")
        
        success_count = 0
        failed_count = 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for i, block in enumerate(blocks_to_regenerate, 1):
            try:
                height = block['height']
                block_data = block['block_data']
                
                # Generate proof bundle and CID
                cid = self._generate_cid_for_block(height, block_data)
                
                if cid:
                    # Update block in database
                    block_data['cid'] = cid
                    block_bytes = json.dumps(block_data).encode('utf-8')
                    
                    cursor.execute('''
                        UPDATE blocks 
                        SET block_bytes = ? 
                        WHERE height = ?
                    ''', (block_bytes, height))
                    
                    success_count += 1
                    
                    if i % batch_size == 0:
                        conn.commit()
                        print(f"   Regenerated {i:,}/{len(blocks_to_regenerate):,} blocks...")
                else:
                    failed_count += 1
                
            except Exception as e:
                print(f"⚠️  Error regenerating block {block['height']}: {e}")
                failed_count += 1
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Regeneration complete:")
        print(f"   Success: {success_count:,}")
        print(f"   Failed: {failed_count:,}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(blocks_to_regenerate)
        }
    
    def _generate_cid_for_block(self, height: int, block_data: Dict) -> Optional[str]:
        """Generate CID for a block by uploading proof bundle to IPFS."""
        try:
            # Create proof bundle from block data
            proof_bundle = {
                'bundle_version': '1.0',
                'block_hash': block_data.get('block_hash', ''),
                'block_index': height,
                'timestamp': block_data.get('timestamp', time.time()),
                'miner_address': block_data.get('miner_address', ''),
                'problem_data': block_data.get('problem_data', {}),
                'solution_data': block_data.get('solution_data', []),
                'complexity': block_data.get('complexity', {}),
                'energy_metrics': block_data.get('energy_metrics', {})
            }
            
            # Upload to IPFS
            bundle_bytes = json.dumps(proof_bundle, indent=2).encode('utf-8')
            cid = self.ipfs_client.add(bundle_bytes)
            
            return cid
            
        except Exception as e:
            print(f"⚠️  Error generating CID for block {height}: {e}")
            return None


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Catalog and regenerate CIDs')
    parser.add_argument('--db', default='data/blockchain.db', help='Database path')
    parser.add_argument('--ipfs', default='http://localhost:5001', help='IPFS API URL (e.g. http://127.0.0.1:5001)')
    parser.add_argument('--catalog', action='store_true', help='Catalog all CIDs')
    parser.add_argument('--create-index', action='store_true', help='Create CID index table')
    parser.add_argument('--regenerate', action='store_true', help='Regenerate missing CIDs')
    parser.add_argument('--max-blocks', type=int, help='Maximum blocks to regenerate')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for regeneration')
    parser.add_argument('--report', help='Save report to file')
    
    args = parser.parse_args()
    
    catalog = CIDCatalog(db_path=args.db, ipfs_url=args.ipfs)
    
    # Initialize IPFS if regenerating
    if args.regenerate:
        catalog.initialize_ipfs()
    
    # Catalog blocks
    if args.catalog or args.create_index or args.regenerate:
        stats = catalog.catalog_all_blocks()
        
        # Generate report
        report = catalog.generate_report()
        print("\n" + report)
        
        # Create index tables
        if args.create_index:
            catalog.create_cid_index_table()
            catalog.create_missing_cid_index()
        
        # Regenerate missing CIDs
        if args.regenerate:
            if not catalog.ipfs_client:
                print("\n❌ Cannot regenerate - IPFS not available")
                print("   Make sure IPFS daemon is running: ipfs daemon")
                return
            
            result = catalog.regenerate_missing_cids(
                batch_size=args.batch_size,
                max_blocks=args.max_blocks
            )
            
            print(f"\n✅ Regeneration complete: {result['success']:,} success, {result['failed']:,} failed")
        
        # Save report if requested
        if args.report:
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"\n✅ Report saved: {args.report}")
    else:
        # Default: just show what would be done
        print("CID Catalog and Regeneration System")
        print("=" * 70)
        print("\nUsage:")
        print("  1. Catalog all CIDs:")
        print("     python scripts/catalog_and_regenerate_cids.py --catalog")
        print("\n  2. Create CID index tables:")
        print("     python scripts/catalog_and_regenerate_cids.py --catalog --create-index")
        print("\n  3. Regenerate missing CIDs (once equilibrium is stable):")
        print("     python scripts/catalog_and_regenerate_cids.py --regenerate")
        print("\n  4. Regenerate first 100 blocks (test):")
        print("     python scripts/catalog_and_regenerate_cids.py --regenerate --max-blocks 100")


if __name__ == "__main__":
    main()

