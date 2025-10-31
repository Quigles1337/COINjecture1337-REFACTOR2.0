#!/usr/bin/env python3
"""
CID Catalog Script
Audits, catalogs, and logs all CIDs in the database
Creates a comprehensive CID index for fast lookups
"""

import sqlite3
import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class CIDCatalog:
    """Comprehensive CID catalog and audit system."""
    
    def __init__(self, db_path: str = "data/blockchain.db"):
        self.db_path = db_path
        self.cid_catalog = {}  # cid -> block_info
        self.missing_cids = []
        self.invalid_cids = []
        self.duplicate_cids = defaultdict(list)
    
    def audit_database(self) -> Dict:
        """Audit all CIDs in the database."""
        print("📊 Auditing CID catalog in database...")
        print("=" * 60)
        
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_blocks': 0,
            'blocks_with_cid': 0,
            'blocks_without_cid': 0,
            'unique_cids': set(),
            'invalid_cids': [],
            'duplicate_cids': defaultdict(list),
            'cid_sources': {
                'block_bytes': 0,
                'commit_index': 0,
                'block_events': 0
            }
        }
        
        # 1. Check blocks table (block_bytes JSON)
        print("\n1️⃣  Checking blocks table (block_bytes)...")
        try:
            cursor.execute('''
                SELECT height, block_hash, block_bytes 
                FROM blocks 
                ORDER BY height ASC
            ''')
            blocks = cursor.fetchall()
            stats['total_blocks'] = len(blocks)
            
            for height, block_hash, block_bytes in blocks:
                try:
                    if block_bytes:
                        block_data = json.loads(block_bytes.decode('utf-8'))
                        cid = block_data.get('cid') or block_data.get('offchain_cid') or block_data.get('ipfs_cid')
                        
                        if cid:
                            stats['blocks_with_cid'] += 1
                            stats['unique_cids'].add(cid)
                            stats['cid_sources']['block_bytes'] += 1
                            
                            # Track CID -> block mapping
                            if cid not in self.cid_catalog:
                                self.cid_catalog[cid] = {
                                    'sources': [],
                                    'blocks': [],
                                    'first_seen': height,
                                    'last_seen': height
                                }
                            
                            self.cid_catalog[cid]['blocks'].append({
                                'height': height,
                                'block_hash': block_hash.decode('utf-8') if isinstance(block_hash, bytes) else block_hash,
                                'source': 'block_bytes'
                            })
                            
                            # Check for duplicates
                            if len(self.cid_catalog[cid]['blocks']) > 1:
                                stats['duplicate_cids'][cid].append(height)
                            
                            # Validate CID format
                            if not self._validate_cid_format(cid):
                                stats['invalid_cids'].append({
                                    'cid': cid,
                                    'block': height,
                                    'reason': 'Invalid format'
                                })
                        else:
                            stats['blocks_without_cid'] += 1
                except Exception as e:
                    print(f"⚠️  Error processing block {height}: {e}")
        except Exception as e:
            print(f"⚠️  Error querying blocks: {e}")
        
        # 2. Check commit_index table
        print("\n2️⃣  Checking commit_index table...")
        try:
            cursor.execute('SELECT commitment, cid, created_at FROM commit_index')
            commits = cursor.fetchall()
            
            for commitment, cid, created_at in commits:
                if cid:
                    stats['unique_cids'].add(cid)
                    stats['cid_sources']['commit_index'] += 1
                    
                    if cid not in self.cid_catalog:
                        self.cid_catalog[cid] = {
                            'sources': [],
                            'blocks': [],
                            'first_seen': None,
                            'last_seen': None
                        }
                    
                    if 'commit_index' not in self.cid_catalog[cid]['sources']:
                        self.cid_catalog[cid]['sources'].append('commit_index')
        except Exception as e:
            print(f"⚠️  Error querying commit_index: {e}")
        
        # 3. Check block_events table (if exists)
        print("\n3️⃣  Checking block_events table...")
        try:
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="block_events"')
            if cursor.fetchone():
                cursor.execute('SELECT block_index, block_hash, cid FROM block_events WHERE cid IS NOT NULL')
                events = cursor.fetchall()
                
                for block_index, block_hash, cid in events:
                    if cid:
                        stats['unique_cids'].add(cid)
                        stats['cid_sources']['block_events'] += 1
                        
                        if cid not in self.cid_catalog:
                            self.cid_catalog[cid] = {
                                'sources': [],
                                'blocks': [],
                                'first_seen': block_index,
                                'last_seen': block_index
                            }
                        
                        if 'block_events' not in self.cid_catalog[cid]['sources']:
                            self.cid_catalog[cid]['sources'].append('block_events')
        except Exception as e:
            print(f"⚠️  Info: block_events table not found or error: {e}")
        
        conn.close()
        
        # Summary
        stats['unique_cids'] = len(stats['unique_cids'])
        stats['duplicate_cids'] = dict(stats['duplicate_cids'])
        
        return stats
    
    def _validate_cid_format(self, cid: str) -> bool:
        """Validate CID format (CIDv0: 46 chars, starts with Qm)."""
        if not cid:
            return False
        
        # CIDv0 format: Qm + 44 base58btc characters = 46 total
        if len(cid) != 46:
            return False
        
        if not cid.startswith('Qm'):
            return False
        
        # Check base58btc characters (no 0, O, I, l)
        import re
        base58btc_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
        return bool(re.match(base58btc_pattern, cid))
    
    def create_cid_index_table(self) -> bool:
        """Create a dedicated CID index table for fast lookups."""
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
                    sources TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # Create index for fast lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cid_index_height ON cid_index(first_block_height, last_block_height)')
            
            # Populate from catalog
            print("   Populating CID index...")
            for cid, info in self.cid_catalog.items():
                heights = [b['height'] for b in info['blocks']]
                first_height = min(heights) if heights else None
                last_height = max(heights) if heights else None
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cid_index 
                    (cid, first_block_height, last_block_height, block_count, sources, updated_at)
                    VALUES (?, ?, ?, ?, ?, strftime('%s', 'now'))
                ''', (
                    cid,
                    first_height,
                    last_height,
                    len(info['blocks']),
                    ','.join(info['sources']) if info['sources'] else 'unknown'
                ))
            
            conn.commit()
            print(f"✅ CID index created with {len(self.cid_catalog)} entries")
            
        except Exception as e:
            print(f"❌ Error creating CID index: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
        
        return True
    
    def generate_report(self, stats: Dict) -> str:
        """Generate comprehensive CID catalog report."""
        report = []
        report.append("=" * 60)
        report.append("📊 CID Catalog Report")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("📈 Statistics:")
        report.append(f"  Total Blocks:           {stats['total_blocks']:,}")
        report.append(f"  Blocks with CID:        {stats['blocks_with_cid']:,} ({stats['blocks_with_cid']/max(stats['total_blocks'],1)*100:.1f}%)")
        report.append(f"  Blocks without CID:     {stats['blocks_without_cid']:,} ({stats['blocks_without_cid']/max(stats['total_blocks'],1)*100:.1f}%)")
        report.append(f"  Unique CIDs:            {stats['unique_cids']:,}")
        report.append("")
        
        report.append("📦 CID Sources:")
        for source, count in stats['cid_sources'].items():
            report.append(f"  {source}: {count:,}")
        report.append("")
        
        if stats['invalid_cids']:
            report.append(f"⚠️  Invalid CIDs: {len(stats['invalid_cids'])}")
            for invalid in stats['invalid_cids'][:10]:
                report.append(f"    - {invalid['cid'][:16]}... (block {invalid['block']})")
            if len(stats['invalid_cids']) > 10:
                report.append(f"    ... and {len(stats['invalid_cids']) - 10} more")
            report.append("")
        
        if stats['duplicate_cids']:
            report.append(f"⚠️  Duplicate CIDs: {len(stats['duplicate_cids'])}")
            for cid, blocks in list(stats['duplicate_cids'].items())[:5]:
                report.append(f"    - {cid[:16]}... appears in {len(blocks)} blocks")
            if len(stats['duplicate_cids']) > 5:
                report.append(f"    ... and {len(stats['duplicate_cids']) - 5} more")
            report.append("")
        
        return "\n".join(report)
    
    def export_catalog(self, output_file: str = "cid_catalog.json") -> bool:
        """Export CID catalog to JSON file."""
        print(f"\n💾 Exporting catalog to {output_file}...")
        
        catalog_data = {
            'generated_at': datetime.now().isoformat(),
            'total_cids': len(self.cid_catalog),
            'catalog': self.cid_catalog
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(catalog_data, f, indent=2, default=str)
            print(f"✅ Catalog exported: {output_file}")
            return True
        except Exception as e:
            print(f"❌ Error exporting catalog: {e}")
            return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CID Catalog and Audit Tool')
    parser.add_argument('--db', default='data/blockchain.db', help='Database path')
    parser.add_argument('--create-index', action='store_true', help='Create CID index table')
    parser.add_argument('--export', help='Export catalog to JSON file')
    parser.add_argument('--report', help='Save report to file')
    
    args = parser.parse_args()
    
    catalog = CIDCatalog(db_path=args.db)
    
    # Audit database
    stats = catalog.audit_database()
    
    # Generate report
    report = catalog.generate_report(stats)
    print("\n" + report)
    
    # Create index table if requested
    if args.create_index:
        catalog.create_cid_index_table()
    
    # Export catalog if requested
    if args.export:
        catalog.export_catalog(args.export)
    
    # Save report if requested
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"\n✅ Report saved: {args.report}")


if __name__ == "__main__":
    main()

