#!/usr/bin/env python3
"""
Database Migration Script for v3.13.2
Adds missing columns for gas data and metrics
"""

import sqlite3
import os
import sys

def migrate_to_v3_13_2():
    """Add missing columns to existing database"""
    db_path = "data/blockchain.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add columns if they don't exist
        columns_to_add = [
            ('work_score', 'REAL DEFAULT 0'),
            ('gas_used', 'INTEGER DEFAULT 0'),
            ('gas_limit', 'INTEGER DEFAULT 1000000'),
            ('gas_price', 'REAL DEFAULT 0.000001'),
            ('reward', 'REAL DEFAULT 0'),
            ('cumulative_work', 'REAL DEFAULT 0'),
            ('timestamp', 'INTEGER DEFAULT 0')
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f'ALTER TABLE blocks ADD COLUMN {col_name} {col_type}')
                print(f"✅ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"ℹ️  Column {col_name} already exists")
                else:
                    print(f"❌ Error adding column {col_name}: {e}")
        
        # Add indexes for performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_blocks_height ON blocks(height)',
            'CREATE INDEX IF NOT EXISTS idx_blocks_work ON blocks(work_score)',
            'CREATE INDEX IF NOT EXISTS idx_blocks_gas ON blocks(gas_used)',
            'CREATE INDEX IF NOT EXISTS idx_blocks_reward ON blocks(reward)'
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✅ Created index: {index_sql.split()[-1]}")
            except sqlite3.Error as e:
                print(f"❌ Error creating index: {e}")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Migrating database schema to v3.13.2...")
    success = migrate_to_v3_13_2()
    sys.exit(0 if success else 1)
