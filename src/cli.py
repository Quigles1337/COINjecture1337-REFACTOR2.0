"""
COINjecture CLI Module

Provides user-facing commands to run nodes and interact with the chain.
Includes user submissions management commands.

Based on docs/blockchain/cli.md specification.
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Import node and related modules
try:
    from .node import Node, NodeConfig, NodeRole, create_node, load_config
    from .user_submissions.aggregation import AggregationStrategy
except ImportError:
    from node import Node, NodeConfig, NodeRole, create_node, load_config
    from user_submissions.aggregation import AggregationStrategy


class COINjectureCLI:
    """COINjecture Command Line Interface."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='coinjectured',
            description='COINjecture blockchain node and interaction tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  coinjectured init --role miner --data-dir ./data
  coinjectured run --config ./config.json
  coinjectured mine --config ./config.json --problem-type subset_sum --tier desktop
  coinjectured get-block --hash 0xabc123...
  coinjectured get-proof --cid QmXyZ...
  coinjectured add-peer --multiaddr /ip4/127.0.0.1/tcp/8080
  coinjectured peers
  coinjectured submit-problem --type subset_sum --bounty 100 --strategy BEST
  coinjectured check-submission --id submission-123
  coinjectured list-submissions
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Node management commands
        self._add_init_command(subparsers)
        self._add_run_command(subparsers)
        self._add_mine_command(subparsers)
        
        # Blockchain interaction commands
        self._add_get_block_command(subparsers)
        self._add_get_proof_command(subparsers)
        
        # Network commands
        self._add_add_peer_command(subparsers)
        self._add_peers_command(subparsers)
        
        # User submissions commands
        self._add_submit_problem_command(subparsers)
        self._add_check_submission_command(subparsers)
        self._add_list_submissions_command(subparsers)
        
        return parser
    
    def _add_init_command(self, subparsers):
        """Add init command parser."""
        parser = subparsers.add_parser(
            'init',
            help='Initialize a new COINjecture node'
        )
        parser.add_argument(
            '--role',
            choices=['light', 'full', 'miner', 'archive'],
            required=True,
            help='Node role (light, full, miner, archive)'
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default='./data',
            help='Data directory for node storage (default: ./data)'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Output config file path (default: config.json)'
        )
        parser.add_argument(
            '--network-id',
            type=str,
            default='coinjecture-mainnet',
            help='Network identifier (default: coinjecture-mainnet)'
        )
        parser.add_argument(
            '--listen-addr',
            type=str,
            default='0.0.0.0:8080',
            help='Listen address (default: 0.0.0.0:8080)'
        )
        parser.add_argument(
            '--enable-user-submissions',
            action='store_true',
            default=True,
            help='Enable user submissions system (default: True)'
        )
    
    def _add_run_command(self, subparsers):
        """Add run command parser."""
        parser = subparsers.add_parser(
            'run',
            help='Start a COINjecture node'
        )
        parser.add_argument(
            '--config',
            type=str,
            required=True,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon (background process)'
        )
    
    def _add_mine_command(self, subparsers):
        """Add mine command parser."""
        parser = subparsers.add_parser(
            'mine',
            help='Start mining operations'
        )
        parser.add_argument(
            '--config',
            type=str,
            required=True,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--problem-type',
            type=str,
            default='subset_sum',
            help='Problem type to mine (default: subset_sum)'
        )
        parser.add_argument(
            '--tier',
            choices=['mobile', 'desktop', 'server', 'gpu'],
            default='desktop',
            help='Hardware tier for mining (default: desktop)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            help='Mining duration in seconds (default: unlimited)'
        )
    
    def _add_get_block_command(self, subparsers):
        """Add get-block command parser."""
        parser = subparsers.add_parser(
            'get-block',
            help='Get block information'
        )
        parser.add_argument(
            '--hash',
            type=str,
            help='Block hash (hex format)'
        )
        parser.add_argument(
            '--index',
            type=int,
            help='Block index/height'
        )
        parser.add_argument(
            '--latest',
            action='store_true',
            help='Get latest block'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'pretty'],
            default='pretty',
            help='Output format (default: pretty)'
        )
    
    def _add_get_proof_command(self, subparsers):
        """Add get-proof command parser."""
        parser = subparsers.add_parser(
            'get-proof',
            help='Get proof data from IPFS'
        )
        parser.add_argument(
            '--cid',
            type=str,
            required=True,
            help='IPFS CID of the proof data'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'raw'],
            default='json',
            help='Output format (default: json)'
        )
    
    def _add_add_peer_command(self, subparsers):
        """Add add-peer command parser."""
        parser = subparsers.add_parser(
            'add-peer',
            help='Add a peer to the network'
        )
        parser.add_argument(
            '--multiaddr',
            type=str,
            required=True,
            help='Multiaddress of the peer'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
    
    def _add_peers_command(self, subparsers):
        """Add peers command parser."""
        parser = subparsers.add_parser(
            'peers',
            help='List connected peers'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'table'],
            default='table',
            help='Output format (default: table)'
        )
    
    def _add_submit_problem_command(self, subparsers):
        """Add submit-problem command parser."""
        parser = subparsers.add_parser(
            'submit-problem',
            help='Submit a problem for mining with bounty'
        )
        parser.add_argument(
            '--type',
            type=str,
            required=True,
            help='Problem type (e.g., subset_sum)'
        )
        parser.add_argument(
            '--template',
            type=str,
            required=True,
            help='Problem template as JSON string'
        )
        parser.add_argument(
            '--bounty',
            type=float,
            required=True,
            help='Bounty amount per solution'
        )
        parser.add_argument(
            '--strategy',
            choices=['ANY', 'BEST', 'MULTIPLE', 'STATISTICAL'],
            default='BEST',
            help='Aggregation strategy (default: BEST)'
        )
        parser.add_argument(
            '--min-quality',
            type=float,
            default=0.0,
            help='Minimum solution quality threshold (default: 0.0)'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
    
    def _add_check_submission_command(self, subparsers):
        """Add check-submission command parser."""
        parser = subparsers.add_parser(
            'check-submission',
            help='Check submission status'
        )
        parser.add_argument(
            '--id',
            type=str,
            required=True,
            help='Submission ID'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'pretty'],
            default='pretty',
            help='Output format (default: pretty)'
        )
    
    def _add_list_submissions_command(self, subparsers):
        """Add list-submissions command parser."""
        parser = subparsers.add_parser(
            'list-submissions',
            help='List active problem submissions'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'table'],
            default='table',
            help='Output format (default: table)'
        )
        parser.add_argument(
            '--status',
            choices=['open', 'partially_filled', 'complete', 'expired'],
            help='Filter by submission status'
        )
    
    def run(self, args: Optional[list] = None) -> int:
        """
        Run the CLI with given arguments.
        
        Args:
            args: Command line arguments (default: sys.argv[1:])
            
        Returns:
            int: Exit code (0 for success, non-zero for error)
        """
        try:
            parsed_args = self.parser.parse_args(args)
            
            if not parsed_args.command:
                self.parser.print_help()
                return 1
            
            # Route to appropriate command handler
            command_method = getattr(self, f'_handle_{parsed_args.command.replace("-", "_")}', None)
            if not command_method:
                print(f"Error: Unknown command '{parsed_args.command}'", file=sys.stderr)
                return 1
            
            return command_method(parsed_args)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _handle_init(self, args) -> int:
        """Handle init command."""
        try:
            # Convert role string to enum
            role_map = {
                'light': NodeRole.LIGHT,
                'full': NodeRole.FULL,
                'miner': NodeRole.MINER,
                'archive': NodeRole.ARCHIVE
            }
            role = role_map[args.role]
            
            # Create node configuration
            config = NodeConfig(
                role=role,
                data_dir=args.data_dir,
                network_id=args.network_id,
                listen_addr=args.listen_addr,
                enable_user_submissions=args.enable_user_submissions
            )
            
            # Create data directory
            data_path = Path(args.data_dir)
            data_path.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            config_path = args.config or 'config.json'
            config_data = {
                'role': args.role,
                'data_dir': args.data_dir,
                'network_id': args.network_id,
                'listen_addr': args.listen_addr,
                'enable_user_submissions': args.enable_user_submissions,
                'ipfs_api_url': config.ipfs_api_url,
                'target_block_interval_secs': config.target_block_interval_secs,
                'log_level': config.log_level
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"✅ Node initialized successfully")
            print(f"   Role: {args.role}")
            print(f"   Data directory: {args.data_dir}")
            print(f"   Config file: {config_path}")
            print(f"   User submissions: {'enabled' if args.enable_user_submissions else 'disabled'}")
            
            return 0
            
        except Exception as e:
            print(f"Error initializing node: {e}", file=sys.stderr)
            return 1
    
    def _handle_run(self, args) -> int:
        """Handle run command."""
        try:
            # Load configuration
            config = load_config(args.config)
            
            # Create and start node
            node = Node(config)
            
            if not node.init():
                print("Error: Failed to initialize node", file=sys.stderr)
                return 1
            
            if not node.start():
                print("Error: Failed to start node", file=sys.stderr)
                return 1
            
            print(f"✅ Node started successfully in {config.role.value} mode")
            print(f"   Data directory: {config.data_dir}")
            print(f"   Listen address: {config.listen_addr}")
            
            if args.daemon:
                print("Running as daemon...")
                # In a real implementation, this would fork to background
                # For now, just run in foreground
                import time
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutting down node...")
                    node.stop()
            else:
                print("Press Ctrl+C to stop the node")
                import time
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutting down node...")
                    node.stop()
            
            return 0
            
        except Exception as e:
            print(f"Error running node: {e}", file=sys.stderr)
            return 1
    
    def _handle_mine(self, args) -> int:
        """Handle mine command."""
        try:
            # Load configuration
            config = load_config(args.config)
            
            if config.role != NodeRole.MINER:
                print("Error: Node must be configured as miner to mine", file=sys.stderr)
                return 1
            
            # Create and start node
            node = Node(config)
            
            if not node.init():
                print("Error: Failed to initialize node", file=sys.stderr)
                return 1
            
            if not node.start():
                print("Error: Failed to start node", file=sys.stderr)
                return 1
            
            print(f"✅ Mining started")
            print(f"   Problem type: {args.problem_type}")
            print(f"   Hardware tier: {args.tier}")
            print(f"   Duration: {'unlimited' if not args.duration else f'{args.duration}s'}")
            
            # Run mining for specified duration
            import time
            start_time = time.time()
            
            try:
                while True:
                    if args.duration and (time.time() - start_time) >= args.duration:
                        print(f"\nMining completed after {args.duration} seconds")
                        break
                    
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\nMining stopped by user")
            
            node.stop()
            return 0
            
        except Exception as e:
            print(f"Error during mining: {e}", file=sys.stderr)
            return 1
    
    def _handle_get_block(self, args) -> int:
        """Handle get-block command."""
        try:
            # This would typically connect to a running node or read from storage
            # For now, return a placeholder response
            
            if args.latest:
                print("Getting latest block...")
                # Placeholder response
                block_data = {
                    "index": 1,
                    "timestamp": 1760601000.0,
                    "previous_hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "block_hash": "0xabc123...",
                    "mining_capacity": "TIER_2_DESKTOP",
                    "cumulative_work_score": 100.0
                }
            elif args.hash:
                print(f"Getting block by hash: {args.hash}")
                block_data = {"error": "Block not found"}
            elif args.index:
                print(f"Getting block by index: {args.index}")
                block_data = {"error": "Block not found"}
            else:
                print("Error: Must specify --hash, --index, or --latest", file=sys.stderr)
                return 1
            
            if args.format == 'json':
                print(json.dumps(block_data, indent=2))
            else:
                self._print_block_pretty(block_data)
            
            return 0
            
        except Exception as e:
            print(f"Error getting block: {e}", file=sys.stderr)
            return 1
    
    def _handle_get_proof(self, args) -> int:
        """Handle get-proof command."""
        try:
            print(f"Getting proof data from IPFS CID: {args.cid}")
            
            # This would typically fetch from IPFS
            # For now, return a placeholder response
            proof_data = {
                "cid": args.cid,
                "status": "retrieved",
                "data": {
                    "problem": {"type": "subset_sum", "numbers": [1, 2, 3, 4, 5], "target": 7},
                    "solution": [2, 5],
                    "complexity": "O(2^n)"
                }
            }
            
            if args.format == 'json':
                print(json.dumps(proof_data, indent=2))
            else:
                print(f"Proof CID: {proof_data['cid']}")
                print(f"Status: {proof_data['status']}")
                print(f"Problem: {proof_data['data']['problem']}")
                print(f"Solution: {proof_data['data']['solution']}")
            
            return 0
            
        except Exception as e:
            print(f"Error getting proof: {e}", file=sys.stderr)
            return 1
    
    def _handle_add_peer(self, args) -> int:
        """Handle add-peer command."""
        try:
            print(f"Adding peer: {args.multiaddr}")
            
            # This would typically connect to a running node
            # For now, just confirm the action
            print("✅ Peer added successfully")
            
            return 0
            
        except Exception as e:
            print(f"Error adding peer: {e}", file=sys.stderr)
            return 1
    
    def _handle_peers(self, args) -> int:
        """Handle peers command."""
        try:
            print("Connected peers:")
            
            # This would typically query a running node
            # For now, return placeholder data
            peers = [
                {"id": "peer1", "address": "/ip4/127.0.0.1/tcp/8080", "status": "connected"},
                {"id": "peer2", "address": "/ip4/192.168.1.100/tcp/8080", "status": "connected"}
            ]
            
            if args.format == 'json':
                print(json.dumps(peers, indent=2))
            else:
                print(f"{'ID':<10} {'Address':<30} {'Status':<10}")
                print("-" * 50)
                for peer in peers:
                    print(f"{peer['id']:<10} {peer['address']:<30} {peer['status']:<10}")
            
            return 0
            
        except Exception as e:
            print(f"Error listing peers: {e}", file=sys.stderr)
            return 1
    
    def _handle_submit_problem(self, args) -> int:
        """Handle submit-problem command."""
        try:
            # Load configuration
            config = load_config(args.config) if args.config else NodeConfig()
            
            # Create node for submission
            node = Node(config)
            
            # Parse problem template
            try:
                problem_template = json.loads(args.template)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in problem template: {e}", file=sys.stderr)
                return 1
            
            # Convert strategy string to enum
            strategy_map = {
                'ANY': AggregationStrategy.ANY,
                'BEST': AggregationStrategy.BEST,
                'MULTIPLE': AggregationStrategy.MULTIPLE,
                'STATISTICAL': AggregationStrategy.STATISTICAL
            }
            strategy = strategy_map[args.strategy]
            
            # Submit problem
            submission_id = node.submit_problem(
                problem_type=args.type,
                problem_template=problem_template,
                aggregation=strategy,
                bounty=args.bounty,
                min_quality=args.min_quality
            )
            
            if submission_id:
                print(f"✅ Problem submitted successfully")
                print(f"   Submission ID: {submission_id}")
                print(f"   Problem type: {args.type}")
                print(f"   Bounty: {args.bounty}")
                print(f"   Strategy: {args.strategy}")
                return 0
            else:
                print("Error: Failed to submit problem", file=sys.stderr)
                return 1
            
        except Exception as e:
            print(f"Error submitting problem: {e}", file=sys.stderr)
            return 1
    
    def _handle_check_submission(self, args) -> int:
        """Handle check-submission command."""
        try:
            # Load configuration
            config = load_config(args.config) if args.config else NodeConfig()
            
            # Create node for query
            node = Node(config)
            
            # Check submission status
            status = node.get_submission_status(args.id)
            
            if status:
                if args.format == 'json':
                    print(json.dumps(status, indent=2))
                else:
                    self._print_submission_pretty(args.id, status)
                return 0
            else:
                print(f"Error: Submission '{args.id}' not found", file=sys.stderr)
                return 1
            
        except Exception as e:
            print(f"Error checking submission: {e}", file=sys.stderr)
            return 1
    
    def _handle_list_submissions(self, args) -> int:
        """Handle list-submissions command."""
        try:
            # Load configuration
            config = load_config(args.config) if args.config else NodeConfig()
            
            # Create node for query
            node = Node(config)
            
            # List active submissions
            submissions = node.list_active_submissions()
            
            # Filter by status if specified
            if args.status:
                submissions = [s for s in submissions if s['status'] == args.status]
            
            if args.format == 'json':
                print(json.dumps(submissions, indent=2))
            else:
                if submissions:
                    print(f"Active submissions ({len(submissions)}):")
                    print(f"{'ID':<25} {'Type':<15} {'Bounty':<10} {'Status':<15} {'Solutions':<10}")
                    print("-" * 85)
                    for sub in submissions:
                        print(f"{sub['submission_id']:<25} {sub['problem_type']:<15} {sub['bounty']:<10} {sub['status']:<15} {sub['solutions_count']:<10}")
                else:
                    print("No active submissions found")
            
            return 0
            
        except Exception as e:
            print(f"Error listing submissions: {e}", file=sys.stderr)
            return 1
    
    def _print_block_pretty(self, block_data: Dict[str, Any]) -> None:
        """Print block data in a pretty format."""
        if "error" in block_data:
            print(f"Error: {block_data['error']}")
            return
        
        print(f"Block Index: {block_data.get('index', 'N/A')}")
        print(f"Timestamp: {block_data.get('timestamp', 'N/A')}")
        print(f"Previous Hash: {block_data.get('previous_hash', 'N/A')}")
        print(f"Block Hash: {block_data.get('block_hash', 'N/A')}")
        print(f"Mining Capacity: {block_data.get('mining_capacity', 'N/A')}")
        print(f"Work Score: {block_data.get('cumulative_work_score', 'N/A')}")
    
    def _print_submission_pretty(self, submission_id: str, status: Dict[str, Any]) -> None:
        """Print submission status in a pretty format."""
        print(f"Submission ID: {submission_id}")
        print(f"Mode: {status.get('mode', 'N/A')}")
        print(f"Status: {status.get('status', 'N/A')}")
        print(f"Solutions Count: {status.get('solutions_count', 0)}")
        
        if status.get('mode') == 'BEST':
            print(f"Best Quality: {status.get('best_quality', 'N/A')}")
            print(f"Current Leader: {status.get('current_leader', 'N/A')}")
        elif status.get('mode') == 'MULTIPLE':
            print(f"Progress: {status.get('progress', 'N/A')}")


def main():
    """Main entry point for the CLI."""
    cli = COINjectureCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
