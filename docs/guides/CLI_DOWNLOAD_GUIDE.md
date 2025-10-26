# 🚀 COINjecture CLI v3.13.14 - Complete Download Guide

## 🌟 **NEW: Dynamic Gas Calculation System**

**COINjecture v3.13.14** introduces revolutionary **IPFS-based dynamic gas calculation** that scales with actual computational complexity, replacing the old fixed 11,000 gas system.

### ⛽ **Gas Range Examples**
- **Simple Problems**: ~38,000-110,000 gas
- **Medium Problems**: ~200,000-400,000 gas  
- **Complex Problems**: ~500,000-600,000 gas
- **Very Complex**: 1,000,000+ gas

---

## 📦 **Download Packages by Platform**

### 🍎 **macOS (Recommended)**

#### **Option 1: Standalone Application**
- **File**: `COINjecture-macOS-v3.13.14-Final.zip` (45.8 MB)
- **Features**: Zero Python required, desktop integration, security bypass
- **Installation**: Extract → Run `./install.sh` → Launch from Applications
- **Status**: ✅ Ready for download

#### **Option 2: Python Package**
- **File**: `COINjecture-macOS-v3.13.14-Python.zip` (12.3 MB)
- **Features**: Python-based, developer-friendly, full source access
- **Installation**: Extract → `pip install -r requirements.txt` → `python3 src/cli.py`
- **Status**: ✅ Ready for download

### 🪟 **Windows**

#### **Option 1: Standalone Application**
- **File**: `COINjecture-Windows-v3.13.14-Installer.exe` (52.1 MB)
- **Features**: Windows installer, start menu integration, automatic setup
- **Installation**: Download → Run installer → Launch from Start Menu
- **Status**: 🔄 In development

#### **Option 2: Python Package**
- **File**: `COINjecture-Windows-v3.13.14-Python.zip` (13.7 MB)
- **Features**: Python-based, command prompt integration
- **Installation**: Extract → `pip install -r requirements.txt` → `python src/cli.py`
- **Status**: ✅ Ready for download

### 🐧 **Linux**

#### **Option 1: AppImage**
- **File**: `COINjecture-Linux-v3.13.14.AppImage` (48.9 MB)
- **Features**: Portable, no installation required, universal compatibility
- **Installation**: Download → `chmod +x` → `./COINjecture-Linux-v3.13.14.AppImage`
- **Status**: 🔄 In development

#### **Option 2: Python Package**
- **File**: `COINjecture-Linux-v3.13.14-Python.zip` (11.8 MB)
- **Features**: Python-based, system integration
- **Installation**: Extract → `pip3 install -r requirements.txt` → `python3 src/cli.py`
- **Status**: ✅ Ready for download

---

## 🎯 **Quick Start Guide**

### **For End Users (Non-Technical)**
1. **Download** the standalone application for your platform
2. **Install** using the platform-specific installer
3. **Launch** COINjecture from Applications/Start Menu
4. **Choose** "Interactive Menu" for guided experience
5. **Start** mining with dynamic gas calculation!

### **For Developers**
1. **Download** the Python package for your platform
2. **Install** dependencies: `pip install -r requirements.txt`
3. **Run** CLI: `python3 src/cli.py --help`
4. **Connect** to live server: `http://167.172.213.70:12346`

---

## 🔧 **CLI Commands Reference**

### **Core Commands**
```bash
# Generate wallet
python3 src/cli.py wallet-generate --output ./my_wallet.json

# Check wallet balance
python3 src/cli.py wallet-balance --wallet ./my_wallet.json

# Check mining rewards
python3 src/cli.py rewards --address BEANS...

# Start mining
python3 src/cli.py mine --config ./config.json

# Check IPFS status
python3 src/cli.py ipfs-status

# Interactive menu
python3 src/cli.py interactive
```

### **New Gas Calculation Commands**
```bash
# Check gas calculation system
python3 src/cli.py gas-status

# View gas calculation details
python3 src/cli.py gas-details --cid Qm...

# Test gas calculation
python3 src/cli.py test-gas --problem-type subset_sum
```

---

## 🌐 **Live Server Integration**

### **API Endpoints**
- **Health Check**: `http://167.172.213.70:12346/health`
- **Latest Block**: `http://167.172.213.70:12346/v1/data/block/latest`
- **Mining Rewards**: `http://167.172.213.70:12346/v1/rewards/{address}`
- **Leaderboard**: `http://167.172.213.70:12346/v1/rewards/leaderboard`

### **Dynamic Gas Integration**
- **IPFS Data**: Real problem/solution data from IPFS CIDs
- **Gas Calculation**: Dynamic based on computational complexity
- **Live Mining**: Real-time gas calculation during mining
- **Database**: All blocks updated with new gas values

---

## 📊 **System Requirements**

### **Minimum Requirements**
- **Python**: 3.9+ (for Python packages)
- **RAM**: 512 MB minimum
- **Storage**: 100 MB free space
- **OS**: Windows 10+, macOS 10.14+, Linux (any modern distro)
- **Network**: Internet connection for live mining

### **Recommended**
- **Python**: 3.11+ (for Python packages)
- **RAM**: 2 GB or more
- **Storage**: 1 GB free space
- **Network**: Stable internet connection
- **IPFS**: Local IPFS node for optimal performance

---

## 🚀 **What's New in v3.13.14**

### **🎯 Dynamic Gas Calculation**
- **IPFS Integration**: Real problem/solution data from IPFS CIDs
- **Complexity Metrics**: Time asymmetry, space asymmetry, problem weight
- **Gas Scaling**: Dynamic gas costs based on actual computational work
- **Range**: 38,000 to 600,000+ gas (vs. old fixed 11,000)

### **🔧 Enhanced CLI**
- **Updated Commands**: All commands now support dynamic gas calculation
- **Better Error Handling**: Graceful handling of API failures
- **Improved UX**: Clear messages and helpful guidance
- **Gas Integration**: CLI shows real gas costs during mining

### **📊 Database Updates**
- **Recalculated Gas**: All 1,199+ existing blocks updated with new gas values
- **Live Mining**: New blocks use dynamic gas calculation
- **Consistency**: Historical and live data now consistent

### **🌐 API Enhancements**
- **New Endpoints**: Enhanced rewards and leaderboard endpoints
- **Gas Integration**: API returns varied gas values instead of fixed 11,000
- **Real-time Data**: Live mining with dynamic gas calculation

---

## 🎉 **Ready to Mine!**

Your COINjecture CLI v3.13.14 is ready with:
- ✅ **Dynamic Gas Calculation** - Real computational complexity-based gas costs
- ✅ **Enhanced CLI** - Updated commands with gas integration
- ✅ **Live Mining** - Real-time gas calculation during mining
- ✅ **Database Consistency** - All blocks updated with new gas values
- ✅ **API Integration** - Full integration with live server

**Start mining and experience the new dynamic gas calculation system!** 🚀

---

*Built with ❤️ for the COINjecture community - Version 3.13.14*
