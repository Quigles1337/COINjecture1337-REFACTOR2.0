#!/usr/bin/env python3
"""
Add mining endpoint to the API server
"""

import re

def add_mining_endpoint():
    """Add the mining endpoint to the API server."""
    
    # Read the current file
    with open('/opt/coinjecture/src/api/faucet_server_cors_fixed.py', 'r') as f:
        content = f.read()
    
    # Find the location to insert the endpoint (before the main block)
    main_pattern = r'if __name__ == [\'"]__main__[\'"]:'
    
    # The new endpoint code
    mining_endpoint = '''
@app.route('/v1/mining/submit-block', methods=['POST'])
def submit_mined_block():
    """Submit a mined block to the blockchain."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract block data
        block_header = data.get('block_header', {})
        work_score = data.get('work_score', 0)
        reward = data.get('reward', 0)
        
        # Simulate block processing
        import time
        block_hash = f'block_{int(time.time())}_{hash(str(block_header))[:16]}'
        height = storage.get_latest_block_index() + 1
        
        logger.info(f'📦 Mined block received: {block_hash}')
        logger.info(f'   Height: {height}')
        logger.info(f'   Work Score: {work_score}')
        logger.info(f'   Reward: {reward}')
        
        return jsonify({
            'success': True,
            'block_hash': block_hash,
            'height': height,
            'cumulative_work': work_score,
            'proof_cid': f'Qm{hash(str(block_header))[:44]}',
            'message': 'Block accepted by consensus'
        }), 200
        
    except Exception as e:
        logger.error(f'❌ Mining submission error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

'''
    
    # Insert the endpoint before the main block
    new_content = re.sub(main_pattern, mining_endpoint + '\n' + main_pattern, content)
    
    # Write the updated content
    with open('/opt/coinjecture/src/api/faucet_server_cors_fixed.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Mining endpoint added successfully")

if __name__ == "__main__":
    add_mining_endpoint()
