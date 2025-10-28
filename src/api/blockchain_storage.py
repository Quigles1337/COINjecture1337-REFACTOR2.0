#!/usr/bin/env python3
"""
COINjecture Storage Module
Implements storage.md specification with proper DB schema and IPFS integration
"""

import os
import json
import time
import hashlib
import sqlite3
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class PruningMode(Enum):
    LIGHT = "light"      # Keep headers + commit_index only
    FULL = "full"        # Keep recent N epochs of bundles
    ARCHIVE = "archive"  # Keep all; disable IPFS GC; pin bundles

@dataclass
class Block:
    index: int
    block_hash: str
    previous_hash: str
    timestamp: float
    miner_address: str
    work_score: float
    cumulative_work_score: float
    proof_commitment: Optional[str]
    problem: Optional[dict]
    solution: Optional[list]
    transactions: List[dict]

class COINjectureStorage:
    """
    COINjecture Storage Implementation
    Follows storage.md specification with proper DB schema
    """
    
    def __init__(self, data_dir: str = "data", pruning_mode: PruningMode = PruningMode.FULL):
        self.data_dir = data_dir
        self.pruning_mode = pruning_mode
        # Use absolute path for database
        self.db_path = os.path.join(data_dir, "blockchain.db")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize database with proper schema
        self.init_database()
        
        # IPFS client (placeholder for now)
        self.ipfs_client = None
        
    def init_database(self):
        """Initialize database with storage.md schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables according to storage.md schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS headers (
                header_hash TEXT PRIMARY KEY,
                header_bytes BLOB NOT NULL,
                height INTEGER NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                block_hash TEXT PRIMARY KEY,
                block_bytes BLOB,
                height INTEGER NOT NULL,
                timestamp INTEGER,
                work_score REAL DEFAULT 0,
                gas_used INTEGER DEFAULT 0,
                gas_limit INTEGER DEFAULT 1000000,
                gas_price REAL DEFAULT 0.000001,
                reward REAL DEFAULT 0,
                cumulative_work REAL DEFAULT 0,
                is_full_block BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tips (
                id INTEGER PRIMARY KEY,
                tip_hash TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_index (
                height INTEGER PRIMARY KEY,
                cumulative_work INTEGER NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commit_index (
                commitment TEXT PRIMARY KEY,
                cid TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peer_index (
                peer_id TEXT PRIMARY KEY,
                meta TEXT NOT NULL,
                last_seen REAL NOT NULL
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_headers_height ON headers(height)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_height ON blocks(height)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_height ON work_index(height)')
        
        conn.commit()
        conn.close()
        
        print(f"📦 Database initialized: {self.db_path}")
    
    def add_header(self, header_hash: str, header_bytes: bytes, height: int, timestamp: float):
        """Add header to storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO headers (header_hash, header_bytes, height, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (header_hash, header_bytes, height, timestamp))
        
        conn.commit()
        conn.close()
    
    def add_block(self, block_hash: str, block_bytes: bytes, height: int, is_full_block: bool = True):
        """Add block to storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO blocks (block_hash, block_bytes, height, is_full_block)
            VALUES (?, ?, ?, ?)
        ''', (block_hash, block_bytes, height, is_full_block))
        
        conn.commit()
        conn.close()
    
    def add_tip(self, tip_hash: str):
        """Add tip hash"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tips (tip_hash, timestamp)
            VALUES (?, ?)
        ''', (tip_hash, time.time()))
        
        conn.commit()
        conn.close()
    
    def update_work_index(self, height: int, cumulative_work: int):
        """Update work index"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO work_index (height, cumulative_work)
            VALUES (?, ?)
        ''', (height, cumulative_work))
        
        conn.commit()
        conn.close()
    
    def add_commitment(self, commitment: str, cid: str):
        """Add commitment to IPFS index"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO commit_index (commitment, cid, timestamp)
            VALUES (?, ?, ?)
        ''', (commitment, cid, time.time()))
        
        conn.commit()
        conn.close()
    
    def add_peer(self, peer_id: str, meta: dict):
        """Add peer metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO peer_index (peer_id, meta, last_seen)
            VALUES (?, ?, ?)
        ''', (peer_id, json.dumps(meta), time.time()))
        
        conn.commit()
        conn.close()
    
    def get_header(self, header_hash: str) -> Optional[bytes]:
        """Get header by hash"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT header_bytes FROM headers WHERE header_hash = ?', (header_hash,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def get_block(self, block_hash: str) -> Optional[bytes]:
        """Get block by hash"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT block_bytes FROM blocks WHERE block_hash = ?', (block_hash,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def get_tips(self) -> List[str]:
        """Get all tip hashes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT tip_hash FROM tips ORDER BY timestamp DESC')
        results = cursor.fetchall()
        
        conn.close()
        return [row[0] for row in results]
    
    def get_work_at_height(self, height: int) -> Optional[int]:
        """Get cumulative work at height"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT cumulative_work FROM work_index WHERE height = ?', (height,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def get_commitment_cid(self, commitment: str) -> Optional[str]:
        """Get IPFS CID for commitment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT cid FROM commit_index WHERE commitment = ?', (commitment,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def get_peers(self) -> List[Tuple[str, dict]]:
        """Get all peers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT peer_id, meta FROM peer_index ORDER BY last_seen DESC')
        results = cursor.fetchall()
        
        conn.close()
        return [(row[0], json.loads(row[1])) for row in results]
    
    def get_latest_height(self) -> int:
        """Get latest block height"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(height) FROM blocks')
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result[0] is not None else 0
    
    def prune_old_data(self):
        """Prune old data based on pruning mode"""
        if self.pruning_mode == PruningMode.LIGHT:
            # Keep only headers and commit_index
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Remove full blocks, keep only headers
            cursor.execute('DELETE FROM blocks WHERE is_full_block = 1')
            
            conn.commit()
            conn.close()
            
        elif self.pruning_mode == PruningMode.FULL:
            # Keep recent N epochs (configurable)
            # Implementation would depend on epoch definition
            pass
            
        # ARCHIVE mode keeps everything
    
    def add_block_data(self, block_data: dict) -> bool:
        """Add complete block data to storage with all metrics"""
        try:
            # Extract block information
            block_hash = block_data['block_hash']
            height = block_data['index']
            timestamp = block_data['timestamp']
            
            # Extract metrics data
            work_score = block_data.get('work_score', 0)
            gas_used = block_data.get('gas_used', 0)
            gas_limit = block_data.get('gas_limit', 1000000)
            gas_price = block_data.get('gas_price', 0.000001)
            reward = block_data.get('reward', 0)
            cumulative_work = block_data.get('cumulative_work_score', 0)
            
            # Serialize block data
            block_bytes = json.dumps(block_data).encode('utf-8')
            
            # Add to storage with all metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO blocks 
                (block_hash, block_bytes, height, timestamp, work_score, 
                 gas_used, gas_limit, gas_price, reward, cumulative_work, is_full_block)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (block_hash, block_bytes, height, timestamp, work_score,
                  gas_used, gas_limit, gas_price, reward, cumulative_work, True))
            
            conn.commit()
            conn.close()
            
            # Add header
            self.add_header(block_hash, block_bytes, height, timestamp)
            
            # Update work index
            cumulative_work_int = int(cumulative_work * 1000000)  # Convert to integer
            self.update_work_index(height, cumulative_work_int)
            
            # Add as tip
            self.add_tip(block_hash)
            
            print(f"✅ Added block {height}: {block_hash[:16]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error adding block data: {e}")
            return False
    
    def get_latest_block_data(self) -> Optional[dict]:
        """Get latest block data"""
        try:
            latest_height = self.get_latest_height()
            if latest_height == 0:
                # Return genesis block
                return {
                    'index': 0,
                    'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
                    'timestamp': 1700000000.0,
                    'previous_hash': '0' * 64,
                    'miner_address': 'GENESIS',
                    'work_score': 0.0,
                    'cumulative_work_score': 0.0,
                    'proof_commitment': None,
                    'problem': None,
                    'solution': None,
                    'transactions': []
                }
            
            # Get latest block by height instead of tips
            return self.get_block_data(latest_height)
            
        except Exception as e:
            print(f"❌ Error getting latest block: {e}")
            return None
    
    def get_ipfs_data(self, cid: str) -> Optional[dict]:
        """Get IPFS data by CID"""
        try:
            # Actually retrieve data from IPFS
            from storage import IPFSClient
            
            ipfs_client = IPFSClient("http://localhost:5001")
            if not ipfs_client.health_check():
                print(f"❌ IPFS daemon not available for CID: {cid}")
                return None
            
            # Get data from IPFS
            data = ipfs_client.get(cid)
            if data:
                proof_json = json.loads(data.decode("utf-8"))
                return {
                    'problem_data': proof_json.get('problem', {}),
                    'solution_data': proof_json.get('solution', {}),
                    'complexity': proof_json.get('complexity', {}),
                    'energy_metrics': proof_json.get('energy_metrics', {}),
                    'cid': cid,
                    'raw_data': proof_json
                }
            else:
                print(f"❌ No data returned from IPFS for CID: {cid}")
                return None
                
        except Exception as e:
            print(f"❌ Error retrieving IPFS data for CID {cid}: {e}")
            return None

    def get_blocks_by_miner(self, miner_address: str) -> List[dict]:
        """Get all blocks mined by a specific address"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all blocks and filter by miner address in block_bytes
            cursor.execute('''
                SELECT height, block_bytes, work_score, gas_used, gas_limit, gas_price, 
                       reward, cumulative_work 
                FROM blocks 
                ORDER BY height DESC
            ''')
            results = cursor.fetchall()
            conn.close()
            
            blocks = []
            for result in results:
                height, block_bytes, work_score, gas_used, gas_limit, gas_price, reward, cumulative_work = result
                
                # Parse block data and check if miner matches
                try:
                    if block_bytes:
                        block_data = json.loads(block_bytes) if isinstance(block_bytes, str) else json.loads(block_bytes.decode('utf-8'))
                        # Check if this block was mined by the requested address
                        if block_data.get('miner_address') == miner_address:
                            block_data.update({
                                'work_score': work_score,
                                'gas_used': gas_used,
                                'gas_limit': gas_limit,
                                'gas_price': gas_price,
                                'reward': reward,
                                'cumulative_work': cumulative_work
                            })
                            blocks.append(block_data)
                except (json.JSONDecodeError, AttributeError):
                    # Skip blocks with invalid JSON or no block_bytes
                    continue
            
            return blocks
            
        except Exception as e:
            print(f"❌ Error getting blocks by miner {miner_address}: {e}")
            return []

    def get_block_data(self, index: int) -> Optional[dict]:
        """Get block data by index with all metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query block with all metrics
            cursor.execute('''
                SELECT block_bytes, work_score, gas_used, gas_limit, gas_price, 
                       reward, cumulative_work 
                FROM blocks WHERE height = ?
            ''', (index,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                block_data = json.loads(result[0]) if isinstance(result[0], str) else json.loads(result[0].decode('utf-8'))
                # Merge database columns with block data
                block_data.update({
                    'work_score': result[1] if result[1] is not None else 0,
                    'gas_used': result[2] if result[2] is not None else 0,
                    'gas_limit': result[3] if result[3] is not None else 1000000,
                    'gas_price': result[4] if result[4] is not None else 0.000001,
                    'reward': result[5] if result[5] is not None else 0,
                    'cumulative_work_score': result[6] if result[6] is not None else 0
                })
                return block_data
            else:
                return None
            
        except Exception as e:
            print(f"❌ Error getting block {index}: {e}")
            return None

    def update_block_gas(self, block_hash: str, new_gas: int) -> bool:
        """Update gas_used value for a specific block"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE blocks 
                SET gas_used = ? 
                WHERE block_hash = ?
            """, (new_gas, block_hash))
            
            conn.commit()
            conn.close()
            
            if cursor.rowcount > 0:
                print(f"✅ Updated gas for block {block_hash[:16]}... to {new_gas}")
                return True
            else:
                print(f"⚠️  No block found with hash {block_hash[:16]}...")
                return False
                
        except Exception as e:
            print(f"❌ Error updating gas for block {block_hash[:16]}...: {e}")
            return False

    def get_blocks_in_timeframe(self, start_time: float, end_time: float) -> List[dict]:
        """Get blocks within a time frame."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT height, block_bytes, work_score, gas_used, gas_limit, gas_price, 
                       reward, cumulative_work 
                FROM blocks 
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY height ASC
            ''', (start_time, end_time))
            
            results = cursor.fetchall()
            conn.close()
            
            blocks = []
            for result in results:
                height, block_bytes, work_score, gas_used, gas_limit, gas_price, reward, cumulative_work = result
                
                # Parse block data
                try:
                    block_data = json.loads(block_bytes) if block_bytes else {}
                except:
                    block_data = {}
                
                blocks.append({
                    'height': height,
                    'block_hash': block_data.get('block_hash', ''),
                    'timestamp': block_data.get('timestamp', 0),
                    'miner_address': block_data.get('miner_address', ''),
                    'work_score': work_score,
                    'gas_used': gas_used,
                    'gas_limit': gas_limit,
                    'gas_price': gas_price,
                    'reward': reward,
                    'cumulative_work_score': cumulative_work
                })
            
            return blocks
            
        except Exception as e:
            print(f"❌ Error getting blocks in timeframe: {e}")
            return []

    def get_unique_miners(self, start_time: float, end_time: float) -> Set[str]:
        """Get unique miner addresses in time frame."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT block_bytes 
                FROM blocks 
                WHERE timestamp >= ? AND timestamp <= ?
            ''', (start_time, end_time))
            
            results = cursor.fetchall()
            conn.close()
            
            miners = set()
            for result in results:
                block_bytes = result[0]
                try:
                    block_data = json.loads(block_bytes) if block_bytes else {}
                    miner = block_data.get('miner_address', '')
                    if miner:
                        miners.add(miner)
                except:
                    continue
            
            return miners
            
        except Exception as e:
            print(f"❌ Error getting unique miners: {e}")
            return set()

    def get_total_mining_attempts(self) -> int:
        """Get total mining attempts (estimated from block count)."""
        try:
            latest_height = self.get_latest_height()
            # Estimate: assume 10% success rate
            return latest_height * 10
        except Exception:
            return 0

    def calculate_success_rate(self) -> float:
        """Calculate mining success rate."""
        try:
            latest_height = self.get_latest_height()
            if latest_height <= 0:
                return 0.0
            
            # Estimate based on recent activity
            # This is a simplified calculation
            return 10.0  # 10% estimated success rate
        except Exception:
            return 0.0

# Global storage instance
storage = COINjectureStorage(data_dir="/opt/coinjecture/data")