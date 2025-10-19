#!/usr/bin/env python3
"""
Fix Cache Manager to Use Only 3 Data Sources
"""

import os
import sys

# Read the current cache manager
with open('/home/coinjecture/COINjecture/src/api/cache_manager.py', 'r') as f:
    content = f.read()

# Update the get_all_blocks method to use only the primary source
updated_content = content.replace(
    '''    def get_all_blocks(self) -> List[Dict[str, Any]]:
        """
        Get all blocks in the blockchain.
        
        Returns:
            List of all blocks
        """
        try:
            # Read from blockchain state
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                # Get all blocks from blockchain state
                all_blocks = []
                if 'blocks' in blockchain_state:
                    all_blocks = blockchain_state['blocks']
                elif 'block_history' in blockchain_state:
                    all_blocks = blockchain_state['block_history']
                
                return all_blocks
            else:
                # Fallback to cache files
                blocks_history = self._read_json(self.blocks_history_file)
                return blocks_history if blocks_history else []
        except Exception as e:
            print(f"Error getting all blocks: {e}")
            return []''',
    '''    def get_all_blocks(self) -> List[Dict[str, Any]]:
        """
        Get all blocks from primary source only.
        
        Returns:
            List of all blocks from blockchain state
        """
        try:
            # Use only primary blockchain state source
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                # Get all blocks from blockchain state
                all_blocks = blockchain_state.get('blocks', [])
                return all_blocks
            else:
                print("Warning: Primary blockchain state not found")
                return []
        except Exception as e:
            print(f"Error getting all blocks: {e}")
            return []'''
)

# Update the get_latest_block method to use only the primary source
updated_content = updated_content.replace(
    '''    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest block from the blockchain.
        
        Returns:
            Latest block data or None
        """
        try:
            # Try to read from blockchain state first
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                if 'latest_block' in blockchain_state:
                    return blockchain_state['latest_block']
            
            # Fallback to cache file
            latest_block = self._read_json(self.latest_block_file)
            return latest_block if latest_block else None
            
        except Exception as e:
            print(f"Error getting latest block: {e}")
            return None''',
    '''    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest block from primary source only.
        
        Returns:
            Latest block data or None
        """
        try:
            # Use only primary blockchain state source
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                return blockchain_state.get('latest_block')
            else:
                print("Warning: Primary blockchain state not found")
                return None
            
        except Exception as e:
            print(f"Error getting latest block: {e}")
            return None'''
)

# Write the updated content
with open('/home/coinjecture/COINjecture/src/api/cache_manager.py', 'w') as f:
    f.write(updated_content)

print("✅ Cache manager updated to use only 3 data sources")
