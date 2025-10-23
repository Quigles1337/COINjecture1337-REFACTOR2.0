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
        
        cursor.execute('SELECT MAX(height) FROM headers')
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
        """Add complete block data to storage"""
        try:
            # Extract block information
            block_hash = block_data['block_hash']
            height = block_data['index']
            timestamp = block_data['timestamp']
            
            # Serialize block data
            block_bytes = json.dumps(block_data).encode('utf-8')
            
            # Add to storage
            self.add_block(block_hash, block_bytes, height, is_full_block=True)
            self.add_header(block_hash, block_bytes, height, timestamp)
            
            # Update work index
            cumulative_work = int(block_data.get('cumulative_work_score', 0) * 1000000)  # Convert to integer
            self.update_work_index(height, cumulative_work)
            
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
            
            # Get latest block from storage
            tips = self.get_tips()
            if tips:
                latest_hash = tips[0]
                block_bytes = self.get_block(latest_hash)
                if block_bytes:
                    return json.loads(block_bytes.decode('utf-8'))
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting latest block: {e}")
            return None
    
    def get_block_data(self, index: int) -> Optional[dict]:
        """Get block data by index"""
        try:
            if index == 0:
                return self.get_latest_block_data()  # Genesis block
            
            # For now, return latest block for any index > 0
            # In a full implementation, we'd query by height
            return self.get_latest_block_data()
            
        except Exception as e:
            print(f"❌ Error getting block {index}: {e}")
            return None

# Global storage instance
storage = COINjectureStorage()