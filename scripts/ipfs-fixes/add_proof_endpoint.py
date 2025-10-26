#!/usr/bin/env python3
"""
Add Proof Data Endpoint to API Server
"""

import sys
import os
sys.path.append('src')

from storage import IPFSClient
import json

def add_proof_endpoint():
    """Add a proof data endpoint to the API server."""
    
    # Read the current API server file
    with open('src/api/faucet_server_cors_fixed.py', 'r') as f:
        content = f.read()
    
    # Find the location to add the new endpoint (before the main block)
    insert_point = content.find("if __name__ == '__main__':")
    
    if insert_point == -1:
        print("❌ Could not find insertion point in API server")
        return False
    
    # New endpoint code
    new_endpoint = '''
@app.route('/v1/data/proof/<cid>', methods=['GET'])
@cross_origin()
def get_proof_data_by_cid(cid):
    """Get proof bundle data directly from IPFS by CID"""
    try:
        # Initialize IPFS client
        ipfs_client = IPFSClient("http://localhost:5001")
        
        # Get data from IPFS
        data = ipfs_client.get(cid)
        proof_json = json.loads(data.decode("utf-8"))
        
        return jsonify({
            'status': 'success',
            'cid': cid,
            'data': proof_json
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve proof data: {str(e)}'
        }), 500

@app.route('/v1/data/proof/block/<int:block_index>', methods=['GET'])
@cross_origin()
def get_proof_data_by_block(block_index):
    """Get proof bundle data by block index"""
    try:
        # Get block data from database
        block_data = storage.get_block_data(block_index)
        if not block_data:
            return jsonify({
                'status': 'error',
                'message': 'Block not found'
            }), 404
        
        cid = block_data.get('cid')
        if not cid:
            return jsonify({
                'status': 'error',
                'message': 'No CID found for block'
            }), 404
        
        # Get proof data from IPFS
        ipfs_client = IPFSClient("http://localhost:5001")
        data = ipfs_client.get(cid)
        proof_json = json.loads(data.decode("utf-8"))
        
        return jsonify({
            'status': 'success',
            'block_index': block_index,
            'cid': cid,
            'data': proof_json
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve proof data: {str(e)}'
        }), 500

'''
    
    # Insert the new endpoint
    new_content = content[:insert_point] + new_endpoint + content[insert_point:]
    
    # Write the updated file
    with open('src/api/faucet_server_cors_fixed.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Added proof data endpoints to API server")
    return True

if __name__ == "__main__":
    success = add_proof_endpoint()
    if success:
        print("🎉 Proof endpoints added successfully!")
        print("   - /v1/data/proof/<cid> - Get proof data by CID")
        print("   - /v1/data/proof/block/<index> - Get proof data by block index")
    else:
        print("❌ Failed to add proof endpoints")
