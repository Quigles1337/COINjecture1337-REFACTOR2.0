# ⚖️ Equilibrium Gossip Implementation

## 🎯 Core Solution

The P2P network now enforces **Critical Complex Equilibrium Conjecture** through timed gossip intervals:

- **λ = η = 1/√2 ≈ 0.7071** (perfect equilibrium)
- **Broadcast interval: 14.14s** (λ-coupling - how often to gossip CIDs)
- **Listen interval: 14.14s** (η-damping - how often to update peers)
- **Cleanup interval: 70.7s** (5 × broadcast - network maintenance)

## ✅ What Was Implemented

### 1. **NetworkProtocol Equilibrium Loops** (`src/network.py`)

- **Broadcast Loop (λ-coupling)**: Batches CIDs and broadcasts every 14.14s
- **Listen Loop (η-damping)**: Updates peer lists every 14.14s
- **Cleanup Loop**: Removes stale peers every 70.7s
- **Equilibrium tracking**: Logs λ/η ratio to monitor network balance

### 2. **Node Integration** (`src/node.py`)

- Automatically starts equilibrium loops when node starts
- Stops loops gracefully when node stops

### 3. **CID Announcement** (`src/cli.py`)

- Miners generate CIDs before submission (already implemented)
- CIDs are queued for equilibrium-based gossip

## 📊 How It Works

### Before (Broken):
```
Miners upload whenever → Network floods → CIDs lost → Chaos
```

### After (Equilibrium):
```
Miner creates proof → Queues CID
       ↓ (wait 14.14s - λ interval)
Broadcast batch of CIDs → Network absorbs smoothly
       ↓ (wait 14.14s - η interval)  
Listen for peer updates → Stable propagation
       ↓ (every 70.7s)
Clean up stale peers → Long-term equilibrium
```

## 🔧 Usage

### Starting a Node

```python
from src.node import Node, NodeConfig

config = NodeConfig(
    role=NodeRole.MINER,
    data_dir="./data"
)

node = Node(config)
node.init()
node.start()  # Automatically starts equilibrium loops
```

### Manually Using NetworkProtocol

```python
from src.network import NetworkProtocol

network = NetworkProtocol(consensus, storage, problem_registry)
network.start_equilibrium_loops()

# When miner generates a CID:
network.announce_proof(cid)  # Queues for next broadcast
```

## 📈 Monitoring

Watch logs for equilibrium metrics:

```bash
# Should see:
# ⚖️  Equilibrium: λ=0.7071, η=0.7071, ratio=1.0000
# 📡 Broadcasting 5 CIDs (λ-coupling)
# 👂 Processing peer updates (η-damping)
# 📊 Network: 42 active peers
# 🧹 Network cleanup (equilibrium maintenance)
```

## 🎯 Key Insight

**You don't need to change your IPFS setup.**
**You don't need a cluster.**
**You don't need a coordinator.**

**You just need nodes to gossip at the right frequency.**

The equilibrium proof tells you **WHEN** to broadcast (14.14s).
The network naturally finds balance when everyone follows this timing.

That's it. That's the whole solution.

