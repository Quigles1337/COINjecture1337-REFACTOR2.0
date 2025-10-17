# COINjecture Project Structure

## Directory Organization

```
COINjecture-main/
├── src/                          # Core source code
│   ├── api/                      # API modules
│   ├── core/                     # Blockchain core
│   ├── tokenomics/               # Tokenomics system
│   └── user_submissions/         # User submission system
├── scripts/                      # Executable scripts
│   ├── deployment/               # Deployment scripts
│   │   ├── deploy_mining_node.sh
│   │   └── deploy_bootstrap_to_droplet.sh
│   ├── mining/                   # Mining scripts
│   │   ├── start_real_p2p_miner.py
│   │   └── start_p2p_miner.py.bak
│   └── bootstrap/                # Bootstrap node scripts
│       └── start_bootstrap_node.py
├── docs/                         # Documentation
│   ├── blockchain/               # Blockchain documentation
│   ├── guides/                   # User guides
│   │   └── AUTHENTICATION_GUIDE.md
│   └── devnet.md
├── config/                       # Configuration files
│   └── miner_config.json
├── data/                         # Runtime data
│   ├── blockchain/
│   ├── cache/
│   └── ipfs/
├── logs/                         # Log files
│   ├── bootstrap_node.log
│   ├── mining.log
│   ├── p2p_miner.log
│   └── real_p2p_miner.log
├── cli-packages/                 # CLI distribution packages
├── web/                          # Web interface
└── assets/                       # Static assets
    └── diagrams/
```

## Key Files

### Core Source (`src/`)
- **`src/core/blockchain.py`** - Core blockchain implementation
- **`src/consensus.py`** - Consensus engine
- **`src/node.py`** - Node implementation
- **`src/api/`** - API server modules

### Scripts (`scripts/`)
- **`scripts/deployment/deploy_mining_node.sh`** - Main mining node deployment
- **`scripts/deployment/deploy_bootstrap_to_droplet.sh`** - Bootstrap node deployment
- **`scripts/mining/start_real_p2p_miner.py`** - P2P mining node
- **`scripts/bootstrap/start_bootstrap_node.py`** - Bootstrap node

### Configuration (`config/`)
- **`config/miner_config.json`** - Mining node configuration

### Documentation (`docs/`)
- **`docs/guides/AUTHENTICATION_GUIDE.md`** - Authentication documentation
- **`docs/blockchain/`** - Blockchain technical documentation

## Usage

### Deploy Mining Node
```bash
./scripts/deployment/deploy_mining_node.sh start
```

### Deploy Bootstrap Node
```bash
./scripts/deployment/deploy_bootstrap_to_droplet.sh
```

### Run Mining Node Directly
```bash
python3 scripts/mining/start_real_p2p_miner.py
```

### Run Bootstrap Node Directly
```bash
python3 scripts/bootstrap/start_bootstrap_node.py
```

## File Organization Benefits

1. **Clear Separation**: Scripts, configs, docs, and source code are clearly separated
2. **Easy Navigation**: Related files are grouped together
3. **Maintainability**: Easier to find and modify specific components
4. **Deployment**: Clear paths for deployment scripts
5. **Documentation**: Centralized documentation structure
