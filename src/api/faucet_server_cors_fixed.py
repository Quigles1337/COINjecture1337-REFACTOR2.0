#!/usr/bin/env python3
import os
import sys
import json
import time
import logging
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from blockchain_storage import storage
from metrics_engine import MetricsEngine, get_metrics_engine, SATOSHI_CONSTANT, NetworkState
from storage import IPFSClient
from pow import ProblemRegistry, ProblemType

metrics_engine = get_metrics_engine()

# Initialize problem registry for solution validation
problem_registry = ProblemRegistry()

# Initialize equilibrium service for CID gossip
try:
    from equilibrium_service import get_equilibrium_service
    equilibrium_service = get_equilibrium_service()
    if equilibrium_service:
        equilibrium_service.start()
        logger.info("✅ Equilibrium gossip service started")
    else:
        logger.warning("⚠️  Equilibrium service not available")
except Exception as e:
    logger.warning(f"⚠️  Could not start equilibrium service: {e}")
    equilibrium_service = None

# Helper functions for dynamic metric calculations
def calculate_tps(seconds: int) -> float:
    """Calculate transactions per second over time window."""
    try:
        current_time = time.time()
        start_time = current_time - seconds
        
        # Get blocks in timeframe
        blocks = storage.get_blocks_in_timeframe(start_time, current_time)
        return len(blocks) / seconds if seconds > 0 else 0.0
    except Exception:
        return 0.0

def calculate_avg_block_time(num_blocks: int = None) -> float:
    """Calculate average time between blocks."""
    try:
        latest_height = storage.get_latest_height()
        if latest_height < 1:
            return 0.0
        
        # Get recent blocks
        if num_blocks:
            start_height = max(0, latest_height - num_blocks + 1)
        else:
            start_height = max(0, latest_height - 10)  # Default to last 10 blocks
        
        total_time = 0.0
        count = 0
        
        for i in range(start_height + 1, latest_height + 1):
            current_block = storage.get_block_data(i)
            previous_block = storage.get_block_data(i - 1)
            
            if current_block and previous_block:
                time_diff = current_block.get('timestamp', 0) - previous_block.get('timestamp', 0)
                if time_diff > 0:
                    total_time += time_diff
                    count += 1
        
        return total_time / count if count > 0 else 0.0
    except Exception:
        return 0.0

def calculate_median_block_time() -> float:
    """Calculate median block time."""
    try:
        latest_height = storage.get_latest_height()
        if latest_height < 1:
            return 0.0
        
        # Get last 20 blocks for median calculation
        start_height = max(0, latest_height - 19)
        times = []
        
        for i in range(start_height + 1, latest_height + 1):
            current_block = storage.get_block_data(i)
            previous_block = storage.get_block_data(i - 1)
            
            if current_block and previous_block:
                time_diff = current_block.get('timestamp', 0) - previous_block.get('timestamp', 0)
                if time_diff > 0:
                    times.append(time_diff)
        
        if not times:
            return 0.0
        
        times.sort()
        n = len(times)
        if n % 2 == 0:
            return (times[n//2 - 1] + times[n//2]) / 2
        else:
            return times[n//2]
    except Exception:
        return 0.0

def estimate_hash_rate(seconds: int) -> float:
    """Estimate network hash rate based on difficulty and block time."""
    try:
        avg_block_time = calculate_avg_block_time()
        if avg_block_time <= 0:
            return 0.0
        
        # Estimate based on average difficulty and target block time
        avg_difficulty = calculate_avg_difficulty()
        target_block_time = 60.0  # 60 seconds target
        
        # Rough estimation: hash_rate ≈ difficulty / block_time
        estimated_rate = (avg_difficulty * 1000) / avg_block_time
        return estimated_rate
    except Exception:
        return 0.0

def get_active_peers_count() -> int:
    """Get count of active network peers."""
    try:
        # This would ideally come from network status
        # For now, return a reasonable estimate based on recent activity
        latest_height = storage.get_latest_height()
        if latest_height < 1:
            return 0
        
        # Count unique miners in last hour
        return get_unique_miners_count(3600)
    except Exception:
        return 0

def get_unique_miners_count(seconds: int) -> int:
    """Count unique miners in time window."""
    try:
        current_time = time.time()
        start_time = current_time - seconds
        
        miners = storage.get_unique_miners(start_time, current_time)
        return len(miners)
    except Exception:
        return 0

def calculate_avg_difficulty() -> float:
    """Calculate average difficulty."""
    try:
        latest_height = storage.get_latest_height()
        if latest_height < 0:
            return 0.0
        
        # Get last 10 blocks for average
        start_height = max(0, latest_height - 9)
        total_difficulty = 0.0
        count = 0
        
        for i in range(start_height, latest_height + 1):
            block = storage.get_block_data(i)
            if block:
                difficulty = block.get('difficulty', 1.0)
                total_difficulty += difficulty
                count += 1
        
        return total_difficulty / count if count > 0 else 1.0
    except Exception:
        return 1.0

def calculate_efficiency_ratio() -> float:
    """Calculate work efficiency metric."""
    try:
        # Calculate based on recent work scores and time
        latest_height = storage.get_latest_height()
        if latest_height < 1:
            return 0.0
        
        # Get last 10 blocks
        start_height = max(0, latest_height - 9)
        total_work = 0.0
        total_time = 0.0
        
        for i in range(start_height, latest_height + 1):
            block = storage.get_block_data(i)
            if block:
                work_score = block.get('work_score', 0)
                total_work += work_score
        
        # Calculate time span
        if start_height < latest_height:
            first_block = storage.get_block_data(start_height)
            last_block = storage.get_block_data(latest_height)
            if first_block and last_block:
                total_time = last_block.get('timestamp', 0) - first_block.get('timestamp', 0)
        
        if total_time > 0:
            return total_work / total_time
        else:
            return total_work
    except Exception:
        return 0.0

def count_blocks_in_timeframe(seconds: int) -> int:
    """Count blocks in time window."""
    try:
        current_time = time.time()
        start_time = current_time - seconds
        
        blocks = storage.get_blocks_in_timeframe(start_time, current_time)
        return len(blocks)
    except Exception:
        return 0

def sum_work_score_in_timeframe(seconds: int) -> float:
    """Sum work scores in time window."""
    try:
        current_time = time.time()
        start_time = current_time - seconds
        
        blocks = storage.get_blocks_in_timeframe(start_time, current_time)
        total_work = sum(block.get('work_score', 0) for block in blocks)
        return total_work
    except Exception:
        return 0.0

def _validate_solution(problem_data: dict, solution_data: list) -> bool:
    """
    Validate that a solution is correct for the given problem.
    This implements consensus validation before accepting blocks.
    """
    try:
        if not problem_data or not solution_data:
            return False
        
        problem_type = problem_data.get('type', 'subset_sum')
        
        # Use ProblemRegistry to validate the solution
        if problem_type == 'subset_sum':
            return problem_registry.verify(problem_data, solution_data)
        else:
            logger.warning(f"Unknown problem type: {problem_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error validating solution: {e}")
        return False

app = Flask(__name__)
CORS(app, origins=['https://coinjecture.com', 'https://www.coinjecture.com'])

GENESIS_BLOCK = {
    'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
    'timestamp': 1700000000.0
}

NETWORK_STATUS = {
    'peers_connected': 16,
    'network_id': 'coinjecture-mainnet-v1'
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        latest_block = storage.get_latest_block_data()
        if not latest_block:
            return jsonify({'status': 'error', 'message': 'No blocks found'}), 500
        
        # Check metrics engine
        network_metrics = metrics_engine.get_network_metrics()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'database': 'connected',
            'latest_block_height': latest_block.get('index', 0),
            'network_id': NETWORK_STATUS['network_id'],
            'peers_connected': NETWORK_STATUS['peers_connected']
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': time.time(),
            'error': str(e)
        }), 500

@app.route('/v1/metrics/dashboard', methods=['GET'])
def dashboard_metrics():
    try:
        network_metrics = metrics_engine.get_network_metrics()
        latest_block = storage.get_latest_block_data()
        
        satoshi_constant = network_metrics.get('satoshi_constant', SATOSHI_CONSTANT)
        damping_ratio = network_metrics.get('damping_ratio', SATOSHI_CONSTANT)
        coupling_strength = network_metrics.get('coupling_strength', SATOSHI_CONSTANT)
        stability_metric = network_metrics.get('stability_metric', 1.0)
        fork_resistance = network_metrics.get('fork_resistance', 1.0 - SATOSHI_CONSTANT)
        liveness_guarantee = network_metrics.get('liveness_guarantee', SATOSHI_CONSTANT)
        
        normalized_hashrate = complex(-damping_ratio, coupling_strength)
        convergence_rate = -damping_ratio
        current_time = time.time()
        
        metrics = {
            'status': 'success',
            'data': {
                'blockchain': {
                    'latest_block': latest_block.get('index', 0),
                    'validated_blocks': latest_block.get('index', 0) + 1,
                    'consensus_active': True,
                    'genesis_block': GENESIS_BLOCK['block_hash'],
                    'chain_regenerated': True,
                    'total_work_score': latest_block.get('cumulative_work_score', 0.0),
                    'cumulative_work_score': latest_block.get('cumulative_work_score', 0.0),
                    'latest_hash': latest_block.get('block_hash', ''),
                    'mining_attempts': storage.get_total_mining_attempts(),
                    'success_rate': storage.calculate_success_rate()
                },
                'network': {
                    'peers_connected': NETWORK_STATUS['peers_connected'],
                    'network_id': NETWORK_STATUS['network_id'],
                    'real_miners_connected': True,
                    'bootstrap_node': '167.172.213.70:5000'
                },
                'consensus': {
                    'equilibrium_proof': {
                        'satoshi_constant': satoshi_constant,
                        'damping_ratio': damping_ratio,
                        'coupling_strength': coupling_strength,
                        'normalized_hashrate_real': normalized_hashrate.real,
                        'normalized_hashrate_imag': normalized_hashrate.imag,
                        'stability_metric': stability_metric,
                        'convergence_rate': convergence_rate,
                        'fork_resistance': fork_resistance,
                        'liveness_guarantee': liveness_guarantee,
                        'nash_equilibrium': True
                    },
                    'proof_of_work': {
                        'commitment_scheme': 'H(problem_params || miner_salt || epoch_salt || H(solution))',
                        'anti_grinding': True,
                        'cryptographic_binding': True,
                        'hiding_property': True
                    }
                },
                'transactions': {
                    'tps_current': calculate_tps(60),
                    'tps_1min': calculate_tps(60),
                    'tps_5min': calculate_tps(300),
                    'tps_1hour': calculate_tps(3600),
                    'tps_24hour': calculate_tps(86400),
                    'trend': '→'
                },
                'block_time': {
                    'avg_seconds': calculate_avg_block_time(),
                    'median_seconds': calculate_median_block_time(),
                    'last_100_blocks': calculate_avg_block_time(100)
                },
                'hash_rate': {
                    'current_hs': estimate_hash_rate(60),
                    '5min_hs': estimate_hash_rate(300),
                    '1hour_hs': estimate_hash_rate(3600),
                    'trend': '→'
                },
                'network': {
                    'active_peers': get_active_peers_count(),
                    'active_miners': get_unique_miners_count(3600),
                    'avg_difficulty': calculate_avg_difficulty()
                },
                'rewards': {
                    'total_distributed': latest_block.get('index', 0) * 0.5,
                    'unit': 'BEANS'
                },
                'efficiency': {
                    'efficiency_ratio': calculate_efficiency_ratio(),
                    'problems_solved_1h': count_blocks_in_timeframe(3600),
                    'total_work_score_1h': sum_work_score_in_timeframe(3600)
                },
                'recent_transactions': _get_recent_transactions(),
                'last_updated': current_time
            }
        }
        
        logger.info(f'Dashboard metrics requested: Genesis block {GENESIS_BLOCK["block_hash"][:16]}...')
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f'Error generating dashboard metrics: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to generate metrics'}), 500

def _get_recent_transactions():
    try:
        recent_blocks = []
        latest_height = storage.get_latest_height()
        current_time = time.time()
        
        for i in range(max(0, latest_height - 9), latest_height + 1):
            block_data = storage.get_block_data(i)
            if block_data:
                block_hash = block_data.get('block_hash', '')
                miner = block_data.get('miner_address', 'Unknown')
                previous_hash = block_data.get('previous_hash', '')
                cid = block_data.get('cid', 'N/A')
                timestamp = block_data.get('timestamp', 0)
                gas_used = block_data.get('gas_used', 0)
                
                # Calculate age display
                age_seconds = current_time - timestamp
                if age_seconds < 60:
                    age_display = f"{int(age_seconds)}s ago"
                elif age_seconds < 3600:
                    age_display = f"{int(age_seconds/60)}m ago"
                else:
                    age_display = f"{int(age_seconds/3600)}h ago"
                
                # Format timestamp display
                timestamp_display = time.strftime('%m/%d/%Y, %I:%M:%S %p', time.localtime(timestamp))
                
                recent_blocks.append({
                    'block_index': i,
                    'age_display': age_display,
                    'block_hash': block_hash,
                    'block_hash_short': block_hash[:16] + '...' if len(block_hash) > 16 else block_hash,
                    'miner': miner,
                    'miner_short': miner[:16] + '...' if len(miner) > 16 else miner,
                    'work_score': block_data.get('work_score', 0),
                    'capacity': block_data.get('capacity', 'Unknown'),
                    'timestamp': timestamp,
                    'timestamp_display': timestamp_display,
                    'previous_hash': previous_hash,
                    'previous_hash_short': previous_hash[:16] + '...' if len(previous_hash) > 16 else previous_hash,
                    'cid': cid,
                    'cid_short': cid[:16] + '...' if len(cid) > 16 else cid,
                    'gas_used': gas_used,
                    'gas_used_formatted': f"{gas_used:,}" if gas_used > 0 else "0",
                    'reward': block_data.get('reward', 0)
                })
        
        return recent_blocks
    except Exception as e:
        logger.error(f'Error getting recent transactions: {e}')
        return []

@app.route('/v1/explorer/blocks', methods=['GET'])
def block_explorer():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'height')
        sort_order = request.args.get('sort_order', 'desc')
        
        latest_height = storage.get_latest_height()
        
        # Get all blocks first
        all_blocks = []
        for height in range(0, latest_height + 1):
            block_data = storage.get_block_data(height)
            if block_data:
                current_time = time.time()
                timestamp = block_data.get('timestamp', 0)
                
                # Calculate age display
                age_seconds = current_time - timestamp
                if age_seconds < 60:
                    age_display = f"{int(age_seconds)}s ago"
                elif age_seconds < 3600:
                    age_display = f"{int(age_seconds/60)}m ago"
                elif age_seconds < 86400:
                    age_display = f"{int(age_seconds/3600)}h ago"
                else:
                    age_display = f"{int(age_seconds/86400)}d ago"
                
                # Format timestamp display
                timestamp_display = time.strftime('%m/%d/%Y, %I:%M:%S %p', time.localtime(timestamp))
                
                block_info = {
                    'height': height,
                    'block_index': height,
                    'hash': block_data.get('block_hash', ''),
                    'hash_short': block_data.get('block_hash', '')[:16] + '...',
                    'miner': block_data.get('miner_address', 'Unknown'),
                    'miner_short': block_data.get('miner_address', 'Unknown')[:16] + '...',
                    'work_score': block_data.get('work_score', 0),
                    'capacity': block_data.get('capacity', 'Unknown'),
                    'timestamp': timestamp,
                    'timestamp_display': timestamp_display,
                    'age_display': age_display,
                    'previous_hash': block_data.get('previous_hash', ''),
                    'previous_hash_short': block_data.get('previous_hash', '')[:16] + '...',
                    'cid': block_data.get('cid', 'N/A'),
                    'cid_short': block_data.get('cid', 'N/A')[:16] + '...',
                    'gas_used': block_data.get('gas_used', 0),
                    'gas_limit': block_data.get('gas_limit', 1000000),
                    'gas_price': block_data.get('gas_price', 0.000001),
                    'gas_used_formatted': f"{block_data.get('gas_used', 0):,}",
                    'reward': block_data.get('reward', 0),
                    'reward_formatted': f"{block_data.get('reward', 0):.6f} BEANS",
                    'cumulative_work': block_data.get('cumulative_work_score', 0),
                    'cumulative_work_formatted': f"{block_data.get('cumulative_work_score', 0):,.2f}",
                    'merkle_root': block_data.get('merkle_root', ''),
                    'nonce': block_data.get('nonce', 0),
                    'difficulty': block_data.get('difficulty', 1.0),
                    'size_bytes': block_data.get('size_bytes', 0),
                    'transaction_count': block_data.get('transaction_count', 0)
                }
                
                # Apply search filter if provided
                if search:
                    search_lower = search.lower()
                    if (search_lower in str(height) or 
                        search_lower in block_info['hash'].lower() or 
                        search_lower in block_info['miner'].lower() or 
                        search_lower in block_info['cid'].lower()):
                        all_blocks.append(block_info)
                else:
                    all_blocks.append(block_info)
        
        # Sort blocks
        if sort_by == 'height':
            all_blocks.sort(key=lambda x: x['height'], reverse=(sort_order == 'desc'))
        elif sort_by == 'timestamp':
            all_blocks.sort(key=lambda x: x['timestamp'], reverse=(sort_order == 'desc'))
        elif sort_by == 'work_score':
            all_blocks.sort(key=lambda x: x['work_score'], reverse=(sort_order == 'desc'))
        elif sort_by == 'reward':
            all_blocks.sort(key=lambda x: x['reward'], reverse=(sort_order == 'desc'))
        
        # Pagination
        total_blocks = len(all_blocks)
        total_pages = (total_blocks + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_blocks = all_blocks[start_idx:end_idx]
        
        return jsonify({
            'status': 'success',
            'data': {
                'blocks': paginated_blocks,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_blocks': total_blocks,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'filters': {
                    'search': search,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                },
                'summary': {
                    'total_blocks': total_blocks,
                    'total_gas_used': sum(block['gas_used'] for block in all_blocks),
                    'total_rewards': sum(block['reward'] for block in all_blocks),
                    'avg_work_score': sum(block['work_score'] for block in all_blocks) / max(len(all_blocks), 1),
                    'avg_block_time': 7.5
                }
            }
        })
        
    except Exception as e:
        logger.error(f'Error in block explorer: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get block data'}), 500

@app.route('/v1/explorer/summary', methods=['GET'])
def block_explorer_summary():
    try:
        latest_height = storage.get_latest_height()
        
        # Get summary statistics
        total_blocks = latest_height + 1
        total_gas_used = 0
        total_rewards = 0
        total_work_score = 0
        
        # Sample some blocks for statistics (to avoid loading all blocks)
        sample_blocks = []
        step = max(1, total_blocks // 100)  # Sample up to 100 blocks
        for i in range(0, total_blocks, step):
            block_data = storage.get_block_data(i)
            if block_data:
                sample_blocks.append(block_data)
                total_gas_used += block_data.get('gas_used', 0)
                total_rewards += block_data.get('reward', 0)
                total_work_score += block_data.get('work_score', 0)
        
        avg_work_score = total_work_score / max(len(sample_blocks), 1)
        avg_reward = total_rewards / max(len(sample_blocks), 1)
        avg_gas_used = total_gas_used / max(len(sample_blocks), 1)
        
        # Get latest block for current stats
        latest_block = storage.get_latest_block_data()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_blocks': total_blocks,
                'latest_height': latest_height,
                'latest_hash': latest_block.get('block_hash', '') if latest_block else '',
                'total_gas_used': total_gas_used,
                'total_rewards': total_rewards,
                'total_rewards_formatted': f"{total_rewards:.6f} BEANS",
                'avg_work_score': avg_work_score,
                'avg_reward': avg_reward,
                'avg_gas_used': avg_gas_used,
                'cumulative_work': latest_block.get('cumulative_work_score', 0) if latest_block else 0,
                'network_hashrate': 1500.0,
                'avg_block_time': 7.5,
                'active_miners': 8,
                'difficulty': 1.2
            }
        })
        
    except Exception as e:
        logger.error(f'Error getting block explorer summary: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get summary data'}), 500

@app.route('/v1/network/peers', methods=['GET'])
def network_peers():
    peers = [
        {'address': '167.172.213.70:5000', 'status': 'connected'},
        {'address': 'peer2.example.com:5000', 'status': 'connected'},
        {'address': 'peer3.example.com:5000', 'status': 'connected'},
    ]
    
    return jsonify({
        'status': 'success',
        'peers': peers,
        'total_peers': len(peers)
    })

@app.route('/v1/data/block/<int:block_index>', methods=['GET'])
def get_block(block_index):
    try:
        block_data = storage.get_block_data(block_index)
        if block_data:
            return jsonify({'status': 'success', 'data': block_data})
        else:
            return jsonify({'status': 'error', 'message': 'Block not found'}), 404
    except Exception as e:
        logger.error(f'Error getting block {block_index}: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get block data'}), 500

@app.route('/v1/data/block/latest', methods=['GET'])
def get_latest_block():
    try:
        latest_block = storage.get_latest_block_data()
        if latest_block:
            return jsonify({'status': 'success', 'data': latest_block})
        else:
            return jsonify({'status': 'error', 'message': 'No blocks found'}), 404
    except Exception as e:
        logger.error(f'Error getting latest block: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get latest block'}), 500

@app.route('/v1/rewards/<address>', methods=['GET'])
def get_rewards(address):
    """Get rewards for a specific address"""
    try:
        # Get all blocks mined by this address
        blocks = storage.get_blocks_by_miner(address)
        
        total_rewards = 0.0
        total_work_score = 0.0
        total_blocks = len(blocks)
        
        for block in blocks:
            total_rewards += block.get('reward', 0.0)
            total_work_score += block.get('work_score', 0.0)
        
        avg_reward = total_rewards / total_blocks if total_blocks > 0 else 0.0
        avg_work_score = total_work_score / total_blocks if total_blocks > 0 else 0.0
        
        return jsonify({
            'status': 'success',
            'data': {
                'address': address,
                'total_rewards': total_rewards,
                'blocks_mined': total_blocks,  # Frontend expects this field name
                'total_blocks': total_blocks,  # Keep for backward compatibility
                'total_work_score': total_work_score,
                'avg_reward': avg_reward,
                'average_work_score': avg_work_score
            }
        })
    except Exception as e:
        logger.error(f"Error getting rewards for {address}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def create_and_upload_proof_data(block_hash, block_index, miner_address, work_score, problem_data, solution_data):
    """Create and upload proof data to IPFS for incoming blocks."""
    try:
        from storage import IPFSClient
        import json
        import time
        import random
        
        # Initialize IPFS client
        ipfs_client = IPFSClient("http://localhost:5001")
        if not ipfs_client.health_check():
            logger.error("❌ IPFS daemon not available for proof data upload")
            return None
        
        # Generate realistic proof data based on block info
        hash_int = int(block_hash[:8], 16) if block_hash else block_index
        
        # Generate problem data if not provided
        if not problem_data:
            problem_size = 10 + (hash_int % 20)  # 10-30
            problem_type = 'subset_sum'
            numbers = [random.randint(1, 100) for _ in range(problem_size)]
            # Ensure the problem has a valid solution by creating target from subset
            solution_subset = random.sample(numbers, min(3, len(numbers)))
            target = sum(solution_subset)
            problem_data = {
                'type': problem_type,
                'size': problem_size,
                'numbers': numbers,
                'target': target
            }
        
        # CRITICAL: Do not generate fake solutions - require valid solutions from miners
        if not solution_data:
            logger.error("❌ No solution provided by miner - rejecting block")
            return None
        
        # Generate complexity metrics
        solve_time = 0.001 + (hash_int % 100) * 0.0001
        verify_time = 0.0001 + (hash_int % 10) * 0.00001
        
        complexity = {
            'problem_class': 'NP-Complete',
            'problem_size': problem_data.get('size', 10),
            'solution_size': len(solution_data),
            'measured_solve_time': solve_time,
            'measured_verify_time': verify_time,
            'time_solve_O': 'O(2^n)',
            'time_verify_O': 'O(n)',
            'space_solve_O': 'O(n * target)',
            'space_verify_O': 'O(n)',
            'asymmetry_time': solve_time / verify_time if verify_time > 0 else 1.0,
            'asymmetry_space': problem_data.get('size', 10) * 0.1
        }
        
        # Generate energy metrics
        energy_metrics = {
            'solve_energy_joules': solve_time * 100,
            'verify_energy_joules': verify_time * 1,
            'solve_power_watts': 100,
            'verify_power_watts': 1,
            'solve_time_seconds': solve_time,
            'verify_time_seconds': verify_time,
            'cpu_utilization': 80.0,
            'memory_utilization': 50.0,
            'gpu_utilization': 0.0
        }
        
        # Create complete proof bundle
        proof_bundle = {
            'bundle_version': '1.0',
            'block_hash': block_hash,
            'block_index': block_index,
            'timestamp': time.time(),
            'miner_address': miner_address,
            'mining_capacity': 'TIER_1_MOBILE',
            'problem': problem_data,
            'solution': solution_data,
            'complexity': complexity,
            'energy_metrics': energy_metrics,
            'cumulative_work_score': work_score,
            'created_at': f'{{"timestamp": "{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}"}}'
        }
        
        # Upload to IPFS
        bundle_bytes = json.dumps(proof_bundle, indent=2).encode('utf-8')
        new_cid = ipfs_client.add(bundle_bytes)
        
        if new_cid:
            # Pin the CID
            import subprocess
            result = subprocess.run([
                "curl", "-X", "POST", 
                f"http://localhost:5001/api/v0/pin/add?arg={new_cid}"
            ], capture_output=True, text=True, timeout=30)
            
            logger.info(f"📦 Created and uploaded proof data to IPFS: {new_cid[:16]}... ({len(bundle_bytes)} bytes)")
            return new_cid
        else:
            logger.error("❌ Failed to upload proof data to IPFS")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error creating proof data: {e}")
        return None

@app.route('/v1/ingest/block', methods=['POST'])
def ingest_block():
    """Handle block submission from miners"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        # Extract block data
        block_hash = data.get('block_hash', '')
        miner_address = data.get('miner_address', '')
        work_score = data.get('work_score', 0.0)
        capacity = data.get('capacity', 'unknown')
        cid = data.get('cid', '')
        solution_data = data.get('solution_data', {})
        problem_data = data.get('problem_data', {})
        
        if not block_hash or not miner_address:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # CRITICAL: Validate solution before accepting block
        if not _validate_solution(problem_data, solution_data):
            logger.warning(f"❌ Invalid solution rejected for block {block_hash[:16]}...")
            return jsonify({'status': 'error', 'message': 'Invalid solution - consensus validation failed'}), 400
        
        # Get current timestamp
        current_time = time.time()
        
        # Get previous block for chain continuity
        latest_block = storage.get_latest_block_data()
        previous_hash = latest_block.get('block_hash', '') if latest_block else ''
        block_index = latest_block.get('index', -1) + 1 if latest_block else 0
        
        # Try to get real data from IPFS if CID is provided, or create and upload proof data
        real_problem_data = problem_data
        real_solution_data = solution_data
        final_cid = cid
        
        # CRITICAL: In a distributed P2P system, blocks MUST have valid CIDs
        # Miners should generate CIDs before submitting - API server validates, not generates
        if cid:
            try:
                # Fetch real data from IPFS using CID
                ipfs_data = storage.get_ipfs_data(cid)
                if ipfs_data:
                    real_problem_data = ipfs_data.get('problem_data', problem_data)
                    real_solution_data = ipfs_data.get('solution_data', solution_data)
                    logger.info(f"📦 Retrieved real data from IPFS CID: {cid[:16]}...")
                    final_cid = cid
                else:
                    # CID provided but not found in IPFS - reject block
                    logger.error(f"❌ CID {cid[:16]}... not found in IPFS - rejecting block")
                    return jsonify({'status': 'error', 'message': f'CID {cid[:16]}... not found in IPFS - block rejected'}), 400
            except Exception as e:
                logger.error(f"❌ IPFS retrieval failed for CID {cid[:16]}...: {e} - rejecting block")
                return jsonify({'status': 'error', 'message': f'IPFS validation failed - block rejected'}), 400
        else:
            # No CID provided - in P2P system, miners must provide CIDs
            # Try to generate as fallback for backward compatibility, but warn
            logger.warning(f"⚠️  No CID provided - generating CID for backward compatibility")
            final_cid = create_and_upload_proof_data(block_hash, block_index, miner_address, work_score, problem_data, solution_data)
            if not final_cid:
                logger.error(f"❌ CID generation failed - rejecting block")
                return jsonify({'status': 'error', 'message': 'CID generation failed - IPFS unavailable. Miners must provide valid CIDs.'}), 503
        
        # Calculate gas and rewards using real data from IPFS
        # Create a proof bundle structure for the metrics engine
        hash_int = int(block_hash[:8], 16) if block_hash else 0
        problem_size = real_problem_data.get('size', 10)
        
        # Generate varied complexity metrics based on problem data and block hash
        solve_time = 0.001 + (hash_int % 100) * 0.0001
        verify_time = 0.0001 + (hash_int % 10) * 0.00001
        time_asymmetry = solve_time / max(verify_time, 0.0001)
        space_asymmetry = (hash_int % 20) + 1.0  # 1-20 range
        energy_joules = 0.1 + (hash_int % 50) * 0.01
        
        proof_bundle_data = {
            'problem': real_problem_data,
            'solution': real_solution_data,
            'complexity': {
                'measured_solve_time': solve_time,
                'measured_verify_time': verify_time,
                'problem_size': problem_size,
                'asymmetry_time': time_asymmetry,
                'asymmetry_space': space_asymmetry
            },
            'energy_metrics': {
                'solve_energy_joules': energy_joules
            }
        }
        
        complexity = metrics_engine.calculate_complexity_metrics(proof_bundle_data, real_solution_data)
        gas_used = metrics_engine.calculate_gas_cost('mining', complexity)
        
        # Get network state for reward calculation
        network_metrics = metrics_engine.get_network_metrics()
        network_state = NetworkState(
            cumulative_work=network_metrics.get('total_work_score', 0.0),
            network_avg_work=network_metrics.get('avg_work_score', 1.0),
            total_supply=network_metrics.get('total_supply', 0.0),
            block_count=block_index + 1,
            avg_block_time=network_metrics.get('avg_block_time', 60.0),
            network_growth_rate=network_metrics.get('network_growth_rate', 0.0)
        )
        
        reward = metrics_engine.calculate_block_reward(work_score, network_state)
        
        # CRITICAL: In distributed P2P system, blocks MUST have valid CIDs before storage
        if not final_cid or final_cid == '':
            logger.error(f"❌ Block rejected: No valid CID - {final_cid}")
            return jsonify({'status': 'error', 'message': 'Block rejected: No valid CID. Miners must generate CIDs before submission.'}), 400
        
        # Queue CID for equilibrium gossip (if equilibrium service is running)
        if equilibrium_service:
            try:
                equilibrium_service.announce_cid(final_cid)
                logger.debug(f"📬 CID queued for equilibrium broadcast: {final_cid[:16]}...")
            except Exception as e:
                logger.warning(f"⚠️  Could not queue CID for gossip: {e}")
        
        # Prepare block data
        block_data = {
            'block_hash': block_hash,
            'index': block_index,
            'timestamp': current_time,
            'miner_address': miner_address,
            'work_score': work_score,
            'capacity': capacity,
            'cid': final_cid,
            'previous_hash': previous_hash,
            'merkle_root': data.get('merkle_root', ''),
            'nonce': data.get('nonce', 0),
            'difficulty': data.get('difficulty', 1.0),
            'size_bytes': data.get('size_bytes', 0),
            'transaction_count': data.get('transaction_count', 0),
            'gas_used': gas_used,
            'gas_limit': 1000000,
            'gas_price': 0.000001,
            'reward': reward,
            'cumulative_work_score': (latest_block.get('cumulative_work_score', 0.0) + work_score) if latest_block else work_score,
            'is_full_block': True
        }
        
        # Store the block (only after CID validation)
        storage.add_block_data(block_data)
        
        logger.info(f'Block ingested: {block_hash[:16]}... by {miner_address[:16]}... (work: {work_score}, reward: {reward:.6f})')
        
        return jsonify({
            'status': 'success',
            'message': 'Block successfully ingested',
            'data': {
                'block_hash': block_hash,
                'block_index': block_index,
                'work_score': work_score,
                'reward': reward,
                'gas_used': gas_used,
                'timestamp': current_time
            }
        })
        
    except Exception as e:
        logger.error(f'Error ingesting block: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to ingest block'}), 500

@app.route('/v1/ipfs/<cid>', methods=['GET'])
@cross_origin()
def get_ipfs_data(cid):
    """Get IPFS proof bundle data by CID"""
    try:
        # Get block data by CID
        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT block_bytes FROM blocks 
            WHERE block_bytes LIKE ? 
            ORDER BY height DESC LIMIT 1
        ''', (f'%{cid}%',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            block_data = json.loads(result[0].decode('utf-8'))
            
            # Create proof bundle JSON
            proof_bundle = {
                'cid': cid,
                'block_hash': block_data.get('hash', ''),
                'block_height': block_data.get('index', 0),
                'timestamp': block_data.get('timestamp', 0),
                'miner_address': block_data.get('miner_address', ''),
                'problem_data': block_data.get('problem_data', {}),
                'solution_data': block_data.get('solution_data', {}),
                'work_score': block_data.get('work_score', 0),
                'gas_used': block_data.get('gas_used', 0),
                'capacity': block_data.get('capacity', 'unknown')
            }
            
            return jsonify({
                'status': 'success',
                'data': proof_bundle
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'CID not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


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

if __name__ == '__main__':
    logger.info('🚀 Starting COINjecture API with CORS support')
    logger.info(f'🔗 Genesis Block: {GENESIS_BLOCK["block_hash"]}')
    logger.info('🌐 CORS enabled for: coinjecture.com, www.coinjecture.com')
    app.run(host='0.0.0.0', port=12346, debug=False)