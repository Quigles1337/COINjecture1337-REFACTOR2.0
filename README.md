# COINjecture: Utility-Based Computational Work Blockchain ($BEANS)

> Built on Satoshi's foundation. Evolved with complexity theory. Driven by real-world utility. 

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-3.15.0-blue.svg)](https://github.com/beanapologist/COINjecture)
[![Status](https://img.shields.io/badge/status-live-green.svg)](https://api.coinjecture.com)

## Overview

COINjecture is a utility-based blockchain that proves computational work through NP-Complete problem solving. Instead of arbitrary hashing, we solve verifiable computational problems with practical applications. The native token is $BEANS.

**[Read the Manifesto](MANIFESTO.md)** | **[Architecture Docs](ARCHITECTURE.README.md)** | **[API Reference](API.README.md)**

## Key Features

- **🧮 Verifiable Work**: NP-Complete problems (O(2^n) solve, O(n) verify)
- **📊 Emergent Tokenomics**: No predetermined schedules, adapts to network behavior
- **🔧 Utility Layer**: User-submitted computational work markets
- **🌐 Distributed Participation**: Competition within hardware classes, not across them
- **⚡ Hardware-Class-Relative Competition**: Mobile vs mobile, server vs server
- **🎯 Tier System**: Hardware compatibility categories, not reward brackets

## The Fundamental Shift

### From Arbitrary Work to Verifiable Work
- **Bitcoin**: Hash until you find a number (arbitrary computation)
- **COINjecture**: Solve NP-Complete problems (verifiable complexity)

### From Predetermined Schedules to Real-World Dynamics
- **Bitcoin**: Fixed supply (21M), fixed block time (10 min), fixed halving schedule
- **COINjecture**: Supply emerges from cumulative work, block time from verification performance

### From Mining to Solving
- Not mining for coins
- Solving problems to prove computational work
- Optionally solving real problems users submit and pay for

## Quick Start

### For Researchers
1. Read [MANIFESTO.md](MANIFESTO.md) for the conceptual foundation
2. Review [ARCHITECTURE.README.md](ARCHITECTURE.README.md) for system design
3. Check [API.README.md](API.README.md) for interface specifications

### For Developers
1. Start with [ARCHITECTURE.README.md](ARCHITECTURE.README.md) for system overview
2. Read [API.README.md](API.README.md) for interface specifications
3. Dive into module-specific docs in [docs/](docs/) for implementation details

### For Deployment
1. See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for directory organization
2. Use `./scripts/deployment/deploy_mining_node.sh start` to deploy mining node
3. Use `./scripts/deployment/deploy_bootstrap_to_droplet.sh` to deploy bootstrap node

### For Users
1. Read [MANIFESTO.md](MANIFESTO.md) to understand what COINjecture is
2. Review [API.README.md](API.README.md) User Submissions section to submit problems
3. Check [docs/testing.md](docs/testing.md) for development environment setup

## 🚀 Download & Install

### **🎉 COINjecture v3.15.0 - Dynamic Gas Calculation Release**

**[📦 View All Downloads on GitHub](https://github.com/beanapologist/COINjecture/releases/tag/v3.15.0)**

### **macOS Users (Recommended)**
**[Download COINjecture-macOS-v3.15.0-Python.zip](https://github.com/beanapologist/COINjecture/releases/download/v3.15.0/COINjecture-macOS-v3.15.0-Python.zip)** (0.7 MB)  
**[Download COINjecture-3.15.0-macOS.dmg](https://github.com/beanapologist/COINjecture/releases/download/v3.15.0/COINjecture-3.15.0-macOS.dmg)** (35.9 MB)

**Features:**
- ✅ **Dynamic Gas Calculation**: IPFS-based gas costs (38K-600K+ gas range)
- ✅ **Enhanced CLI**: All commands support dynamic gas calculation
- ✅ **Interactive Menu**: User-friendly interface for beginners
- ✅ **Direct CLI Access**: Full command-line functionality for advanced users
- ✅ **Live Network Integration**: Real-time gas calculation during mining
- ✅ **Cross-platform Support**: macOS, Windows, Linux packages

**Installation:**
1. Download the package above
2. Extract and run `./install.sh`
3. Launch with `./start_coinjecture.sh`
4. **COINjecture launches automatically!** 🚀

### **Windows Users**
**[Download COINjecture-Windows-v3.15.0-Python.zip](https://github.com/beanapologist/COINjecture/releases/download/v3.15.0/COINjecture-Windows-v3.15.0-Python.zip)** (0.7 MB)

**Installation:**
1. Download the package above
2. Extract and run `install.bat`
3. Launch with `start_coinjecture.bat`

### **Linux Users**
**[Download COINjecture-Linux-v3.15.0-Python.zip](https://github.com/beanapologist/COINjecture/releases/download/v3.15.0/COINjecture-Linux-v3.15.0-Python.zip)** (0.7 MB)

**Installation:**
1. Download the package above
2. Extract and run `./install.sh`
3. Launch with `./start_coinjecture.sh`

## Interactive CLI

COINjecture includes a comprehensive command-line interface with 15 commands and interactive menus:

### **Installation**
```bash
# One-click installer (recommended)
python3 install_coinjecture.py

# Or download platform-specific launchers
# Windows: start_coinjecture.bat
# Unix: start_coinjecture.sh
```

### **Interactive Menu**
```
🚀 COINjecture Interactive Menu
============================================================
1. 🏗️  Setup & Configuration
2. ⛏️  Mining Operations  
3. 💰 Problem Submissions
4. 🔍 Blockchain Explorer
5. 🌐 Network Management
6. 📊 Telemetry & Monitoring
7. ❓ Help & Documentation
8. 🚪 Exit
============================================================
```

### **Command Line Usage**
```bash
# Start interactive menu
coinjectured interactive

# Initialize node
coinjectured init --role miner

# Start mining
coinjectured mine --tier desktop

# Submit problem
coinjectured submit-problem --type subset_sum --bounty 100

# Check submission status
coinjectured check-submission <submission_id>

# List active submissions
coinjectured list-submissions
```

### **Available Commands**
- `init` - Initialize node configuration
- `run` - Start node with specified role
- `mine` - Start mining operations
- `get-block` - Retrieve block by index
- `get-proof` - Get proof data for block
- `add-peer` - Add network peer
- `peers` - List connected peers
- `submit-problem` - Submit computational problem
- `check-submission` - Check submission status
- `list-submissions` - List active submissions
- `interactive` - Launch interactive menu
- `telemetry` - Manage telemetry settings

## Live TestNet
- **🌍 Network**: TestNet (not mainnet)
- **🌐 API Server**: https://api.coinjecture.com
- **📊 Latest Block**: https://api.coinjecture.com/v1/data/block/latest
- **🔍 Health Check**: https://api.coinjecture.com/health
- **🔗 Genesis**: d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358
- **👥 Network**: 16 total connections, 3 active peers (167.172.213.70:5000, peer2.example.com:5000, peer3.example.com:5000)
- **⚡ Real Miners**: Connected to actual network miners (BEANS addresses)
- **🔄 Chain Regeneration**: Successfully regenerated from genesis block
- **📡 All Endpoints**: Available worldwide with TLS/SSL

## Documentation

| Document | Purpose |
|----------|---------|
| **[MANIFESTO.md](MANIFESTO.md)** | Vision and principles |
| **[ARCHITECTURE.README.md](ARCHITECTURE.README.md)** | System architecture |
| **[API.README.md](API.README.md)** | Language-agnostic API specifications |
| **[DYNAMIC_TOKENOMICS.README.md](DYNAMIC_TOKENOMICS.README.md)** | Tokenomics system details |
| **[USER_GUIDE.md](USER_GUIDE.md)** | Complete user instructions |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Command reference |
| **[DOWNLOAD_PACKAGES.md](DOWNLOAD_PACKAGES.md)** | Installation guide |

### Technical Documentation

- **[docs/blockchain/](docs/blockchain/)** - Module-specific specifications
- **[docs/devnet.md](docs/devnet.md)** - Development environment setup
- **[docs/testing.md](docs/testing.md)** - Testing specifications

## Project Structure

```
src/
├── core/                    # Core blockchain implementation
│   └── blockchain.py       # Main blockchain logic
├── tokenomics/             # Dynamic work score tokenomics
│   └── dynamic_tokenomics.py
├── user_submissions/       # User submission system
│   ├── aggregation.py
│   ├── pool.py
│   ├── submission.py
│   └── tracker.py
├── cli.py                  # Command-line interface
├── node.py                 # Node orchestration
├── pow.py                  # Proof-of-work module
├── storage.py              # Storage and IPFS
├── consensus.py            # Consensus engine
├── network.py              # Network protocol
└── api/                    # Faucet API server
    ├── faucet_server.py
    ├── cache_manager.py
    └── update_cache.py

docs/                       # Technical documentation
├── blockchain/             # Module specifications
├── devnet.md              # Development environment
└── testing.md             # Testing guide

scripts/                    # Development and deployment scripts
tests/                      # Test suite
assets/                     # Diagrams and assets
└── diagrams/
    └── block_structure.png
```

## Supported Problems

### Production Ready
- **Subset Sum**: O(2^n) solve, O(n) verify - exact DP solver

### In Development
- **Knapsack**: 0/1 Knapsack problem, NP-Complete
- **Graph Coloring**: Graph k-coloring, NP-Complete
- **SAT**: Boolean satisfiability, NP-Complete
- **TSP**: Traveling Salesman Problem, NP-Complete

### Research/Scaffold
- **Factorization**: Integer factorization, NP-Hard
- **Lattice**: Lattice-based problems, NP-Hard
- **Clique**: Maximum clique, NP-Complete
- **Vertex Cover**: Minimum vertex cover, NP-Complete
- **Hamiltonian Path**: NP-Complete
- **Set Cover**: NP-Complete
- **Bin Packing**: NP-Hard
- **Job Scheduling**: NP-Hard

## Tier System

| Tier | Name | Problem Size | Target Hardware | Characteristics |
|------|------|--------------|-----------------|-----------------|
| 1 | Mobile | 8-12 elements | Smartphones, tablets, IoT | Energy efficient, fast iteration |
| 2 | Desktop | 12-16 elements | Laptops, basic desktops | Balanced performance |
| 3 | Workstation | 16-20 elements | Gaming PCs, dev machines | Higher compute power |
| 4 | Server | 20-24 elements | Dedicated servers, cloud | Massive parallel processing |
| 5 | Cluster | 24-32 elements | Multi-node, supercomputers | Distributed computation |

## Status

**Version**: 3.15.0 (Live TestNet)  
**Status**: Production Ready  
**License**: MIT  

### **Current Features**
- ✅ **Live API Server** - 24/7 worldwide access
- ✅ **Interactive CLI** - 15 commands with guided menus
- ✅ **IPFS Integration** - Off-chain proof storage
- ✅ **User Submissions** - Problem submission and solving
- ✅ **Telemetry System** - Real-time mining data
- ✅ **Cross-Platform** - Windows, macOS, Linux support

### **Server Performance**
- **Uptime**: 100% since deployment
- **Response Time**: < 100ms average
- **Availability**: Global access
- **Security**: Rate limiting, HMAC authentication

## 🔗 GitHub Repository

**[🌐 View on GitHub](https://github.com/beanapologist/COINjecture)**

- **📦 Releases**: [Download v3.15.0 packages](https://github.com/beanapologist/COINjecture/releases/tag/v3.15.0)
- **🐛 Issues**: [Report bugs and request features](https://github.com/beanapologist/COINjecture/issues)
- **💬 Discussions**: [Community discussions](https://github.com/beanapologist/COINjecture/discussions)
- **📚 Documentation**: Complete guides and API references
- **⭐ Star**: Show your support for the project

### **Quick Links**
- [📋 Source Code](https://github.com/beanapologist/COINjecture)
- [📦 Download Packages](https://github.com/beanapologist/COINjecture/releases)
- [📖 Documentation](https://github.com/beanapologist/COINjecture/tree/main/docs)
- [🔧 Development Setup](https://github.com/beanapologist/COINjecture/blob/main/ARCHITECTURE.README.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE)

## Acknowledgments

Built on Satoshi Nakamoto's foundational insights about proof-of-work consensus and immutable ledgers. COINjecture evolves these concepts with complexity theory and real-world utility.

**Not mining - solving.**  
**Not arbitrary work - verifiable work.**  
**Not predetermined schedules - emergent economics.**  
**Not centralized - distributed by design.**

---

**COINjecture: Utility-based computational work, built on Satoshi's foundation.**

*Visit our live server: https://api.coinjecture.com*