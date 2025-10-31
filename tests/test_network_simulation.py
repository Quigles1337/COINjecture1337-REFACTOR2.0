"""
Local Network Simulation Test
Simulates multi-node network to verify equilibrium is maintained
"""

import pytest
import asyncio
import time
import sys
import os
from typing import List
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None

from network import NetworkProtocol


class SimulatedNode:
    """Simulated network node for testing."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        # Create network protocol with mocked dependencies
        self.network = NetworkProtocol(Mock(), Mock(), Mock())
        self.received_cids = []
        self.broadcast_times = []
        self.lambda_history = []
        self.eta_history = []
        self.cids_announced = []
    
    def mine_block(self, block_id: int):
        """Simulate mining a block."""
        cid = f"Qm{self.node_id}-{block_id}"
        self.network.announce_proof(cid)
        self.cids_announced.append(cid)
    
    def record_metrics(self):
        """Record current equilibrium state."""
        self.lambda_history.append(self.network.lambda_state)
        self.eta_history.append(self.network.eta_state)


class NetworkSimulation:
    """Simulate multi-node network."""
    
    def __init__(self, num_nodes: int = 10):
        self.nodes: List[SimulatedNode] = [
            SimulatedNode(f"node{i}") for i in range(num_nodes)
        ]
        self.start_time = time.time()
        self.metrics_recorded = []
    
    async def run_simulation(self, duration: int = 60):
        """
        Run network simulation for given duration (seconds).
        
        Tests:
        1. Nodes mine at random intervals
        2. Network maintains equilibrium
        3. CIDs propagate successfully (simulated)
        """
        print(f"\n🧪 Starting {duration}s simulation with {len(self.nodes)} nodes...")
        
        # Start equilibrium loops on all nodes
        for node in self.nodes:
            node.network.start_equilibrium_loops()
        
        # Mining simulation - nodes mine at random intervals
        mining_tasks = []
        for node in self.nodes:
            async def mine_loop(n):
                block_id = 0
                start_time = time.time()
                while time.time() - start_time < duration:
                    # Random mining interval between 1-10 seconds
                    if not HAS_NUMPY:
                        import random
                        interval = random.uniform(1, 10)
                    else:
                        interval = np.random.uniform(1, 10)
                    
                    n.mine_block(block_id)
                    block_id += 1
                    await asyncio.sleep(interval)
            
            mining_tasks.append(mine_loop(node))
        
        # Metric recording loop
        async def record_loop():
            start_time = time.time()
            while time.time() - start_time < duration + 2:  # Record slightly longer
                for node in self.nodes:
                    node.record_metrics()
                await asyncio.sleep(1)
        
        # Run simulation
        recording_task = asyncio.create_task(record_loop())
        
        try:
            await asyncio.gather(*mining_tasks, return_exceptions=True)
            await asyncio.sleep(2)  # Wait for final recordings
            recording_task.cancel()
        except Exception as e:
            print(f"⚠️  Simulation error: {e}")
        finally:
            # Stop all loops
            for node in self.nodes:
                node.network.stop_equilibrium_loops()
        
        print(f"✅ Simulation complete")
        return self.analyze_results()
    
    def analyze_results(self):
        """Analyze simulation results."""
        print("\n📊 Simulation Results:")
        
        # Calculate average equilibrium across all nodes
        all_lambda = []
        all_eta = []
        all_cids = 0
        
        for node in self.nodes:
            if node.lambda_history:
                all_lambda.extend(node.lambda_history)
            if node.eta_history:
                all_eta.extend(node.eta_history)
            all_cids += len(node.cids_announced)
        
        if not all_lambda or not all_eta:
            return {"error": "No metrics recorded"}
        
        if HAS_NUMPY:
            avg_lambda = np.mean(all_lambda)
            avg_eta = np.mean(all_eta)
            std_lambda = np.std(all_lambda)
            std_eta = np.std(all_eta)
        else:
            avg_lambda = sum(all_lambda) / len(all_lambda)
            avg_eta = sum(all_eta) / len(all_eta)
            variance_lambda = sum((x - avg_lambda) ** 2 for x in all_lambda) / len(all_lambda)
            variance_eta = sum((x - avg_eta) ** 2 for x in all_eta) / len(all_eta)
            std_lambda = variance_lambda ** 0.5
            std_eta = variance_eta ** 0.5
        
        ratio = avg_lambda / avg_eta if avg_eta > 0 else 1.0
        
        print(f"   λ (Coupling):  {avg_lambda:.4f} ± {std_lambda:.4f}")
        print(f"   η (Damping):   {avg_eta:.4f} ± {std_eta:.4f}")
        print(f"   Ratio λ/η:     {ratio:.4f}")
        print(f"   CIDs announced: {all_cids}")
        
        # Check equilibrium
        target = 0.7071
        lambda_deviation = abs(avg_lambda - target)
        eta_deviation = abs(avg_eta - target)
        ratio_deviation = abs(ratio - 1.0)
        
        print(f"\n⚖️  Equilibrium Check:")
        lambda_ok = lambda_deviation < 0.05
        eta_ok = eta_deviation < 0.05
        ratio_ok = ratio_deviation < 0.1
        
        print(f"   λ deviation:   {lambda_deviation:.4f} {'✅' if lambda_ok else '❌'}")
        print(f"   η deviation:   {eta_deviation:.4f} {'✅' if eta_ok else '❌'}")
        print(f"   Ratio balance: {ratio_deviation:.4f} {'✅' if ratio_ok else '❌'}")
        
        results = {
            "avg_lambda": avg_lambda,
            "avg_eta": avg_eta,
            "ratio": ratio,
            "lambda_deviation": lambda_deviation,
            "eta_deviation": eta_deviation,
            "ratio_deviation": ratio_deviation,
            "lambda_ok": lambda_ok,
            "eta_ok": eta_ok,
            "ratio_ok": ratio_ok,
            "total_cids": all_cids
        }
        
        # Plot results if matplotlib available
        if HAS_MATPLOTLIB and HAS_NUMPY:
            self.plot_equilibrium()
        
        return results
    
    def plot_equilibrium(self):
        """Plot equilibrium over time."""
        if not (HAS_MATPLOTLIB and HAS_NUMPY):
            return
        
        try:
            fig, axes = plt.subplots(2, 1, figsize=(12, 8))
            
            # Plot λ and η for each node
            for node in self.nodes:
                if node.lambda_history:
                    axes[0].plot(node.lambda_history, alpha=0.3, label=f'{node.node_id}')
                if node.eta_history:
                    axes[1].plot(node.eta_history, alpha=0.3)
            
            # Target lines
            axes[0].axhline(y=0.7071, color='r', linestyle='--', label='Target λ')
            axes[1].axhline(y=0.7071, color='r', linestyle='--', label='Target η')
            
            axes[0].set_title('λ (Coupling) Over Time')
            axes[0].set_ylabel('λ value')
            axes[0].legend(loc='upper right', fontsize=6)
            axes[0].grid(True, alpha=0.3)
            
            axes[1].set_title('η (Damping) Over Time')
            axes[1].set_ylabel('η value')
            axes[1].set_xlabel('Time (seconds)')
            axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            output_path = os.path.join(os.path.dirname(__file__), '..', 'equilibrium_simulation.png')
            plt.savefig(output_path, dpi=150)
            print(f"\n📈 Plot saved to {output_path}")
            plt.close()
        except Exception as e:
            print(f"⚠️  Could not generate plot: {e}")


@pytest.mark.simulation
@pytest.mark.slow
class TestNetworkSimulation:
    """Test network equilibrium through simulation."""
    
    @pytest.mark.asyncio
    async def test_small_network_simulation(self):
        """Test equilibrium with small network (5 nodes, 30 seconds)."""
        sim = NetworkSimulation(num_nodes=5)
        results = await sim.run_simulation(duration=30)
        
        assert "error" not in results, "Simulation should complete without error"
        assert results["lambda_ok"], f"λ should stay near target, deviation: {results['lambda_deviation']:.4f}"
        assert results["eta_ok"], f"η should stay near target, deviation: {results['eta_deviation']:.4f}"
        assert results["ratio_ok"], f"Ratio should stay near 1.0, deviation: {results['ratio_deviation']:.4f}"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_NUMPY, reason="NumPy required for longer simulations")
    async def test_medium_network_simulation(self):
        """Test equilibrium with medium network (10 nodes, 60 seconds)."""
        sim = NetworkSimulation(num_nodes=10)
        results = await sim.run_simulation(duration=60)
        
        assert "error" not in results, "Simulation should complete without error"
        assert results["lambda_ok"], f"λ should stay near target"
        assert results["eta_ok"], f"η should stay near target"
        assert results["ratio_ok"], f"Ratio should stay near 1.0"


if __name__ == "__main__":
    # Run simulation directly
    sim = NetworkSimulation(num_nodes=10)
    results = asyncio.run(sim.run_simulation(duration=60))
    print(f"\n✅ Simulation complete: {results}")

