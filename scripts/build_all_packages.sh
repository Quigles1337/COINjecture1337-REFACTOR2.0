#!/bin/bash

# COINjecture v3.13.14 - Complete Package Builder
# Builds all download packages for macOS, Windows, and Linux

set -e

echo "🚀 COINjecture v3.13.14 - Complete Package Builder"
echo "=================================================="

# Configuration
VERSION="3.13.14"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
PACKAGES_DIR="$DIST_DIR/packages"

# Create directories
mkdir -p "$DIST_DIR"
mkdir -p "$PACKAGES_DIR"

echo "📁 Created distribution directories"

# Function to build Python packages
build_python_package() {
    local platform=$1
    local package_name="COINjecture-${platform}-v${VERSION}-Python.zip"
    
    echo "🐍 Building Python package for $platform..."
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    local package_dir="$temp_dir/COINjecture-${platform}-v${VERSION}"
    
    # Copy source code
    cp -r "$PROJECT_ROOT/src" "$package_dir/"
    cp -r "$PROJECT_ROOT/config" "$package_dir/"
    cp -r "$PROJECT_ROOT/docs" "$package_dir/"
    cp "$PROJECT_ROOT/requirements.txt" "$package_dir/"
    cp "$PROJECT_ROOT/README.md" "$package_dir/"
    cp "$PROJECT_ROOT/CHANGELOG.md" "$package_dir/"
    cp "$PROJECT_ROOT/VERSION" "$package_dir/"
    
    # Create platform-specific startup scripts
    if [[ "$platform" == "macOS" ]]; then
        cat > "$package_dir/start_coinjecture.sh" << 'EOF'
#!/bin/bash
echo "🚀 Starting COINjecture CLI..."
python3 src/cli.py interactive
EOF
        chmod +x "$package_dir/start_coinjecture.sh"
    elif [[ "$platform" == "Windows" ]]; then
        cat > "$package_dir/start_coinjecture.bat" << 'EOF'
@echo off
echo 🚀 Starting COINjecture CLI...
python src/cli.py interactive
EOF
    elif [[ "$platform" == "Linux" ]]; then
        cat > "$package_dir/start_coinjecture.sh" << 'EOF'
#!/bin/bash
echo "🚀 Starting COINjecture CLI..."
python3 src/cli.py interactive
EOF
        chmod +x "$package_dir/start_coinjecture.sh"
    fi
    
    # Create installation script
    cat > "$package_dir/install.sh" << 'EOF'
#!/bin/bash
echo "🔧 Installing COINjecture dependencies..."
pip install -r requirements.txt
echo "✅ Installation complete!"
echo "🚀 Run: ./start_coinjecture.sh (Unix) or start_coinjecture.bat (Windows)"
EOF
    chmod +x "$package_dir/install.sh"
    
    # Create README for package
    cat > "$package_dir/README.md" << EOF
# COINjecture v${VERSION} - ${platform} Python Package

## Quick Start
1. Install dependencies: \`./install.sh\`
2. Start CLI: \`./start_coinjecture.sh\` (Unix) or \`start_coinjecture.bat\` (Windows)
3. Choose "Interactive Menu" for guided experience

## Features
- ✅ Dynamic Gas Calculation (38K-600K+ gas range)
- ✅ IPFS-based gas calculation
- ✅ Live mining with real-time gas costs
- ✅ Enhanced CLI with gas integration
- ✅ Complete wallet and mining system

## API Server
- **Live Server**: http://167.172.213.70:12346
- **Health Check**: http://167.172.213.70:12346/health
- **Dynamic Gas**: Real-time gas calculation based on computational complexity

## Commands
\`\`\`bash
# Generate wallet
python3 src/cli.py wallet-generate --output ./my_wallet.json

# Check balance
python3 src/cli.py wallet-balance --wallet ./my_wallet.json

# Start mining
python3 src/cli.py mine --config ./config.json

# Interactive menu
python3 src/cli.py interactive
\`\`\`

Built with ❤️ for the COINjecture community
EOF
    
    # Create zip package
    cd "$temp_dir"
    zip -r "$PACKAGES_DIR/$package_name" "COINjecture-${platform}-v${VERSION}"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    echo "✅ Built $package_name"
}

# Function to build standalone packages (placeholder for PyInstaller)
build_standalone_package() {
    local platform=$1
    local package_name="COINjecture-${platform}-v${VERSION}-Standalone.zip"
    
    echo "📦 Building standalone package for $platform..."
    echo "⚠️  Standalone packages require PyInstaller - using Python package as fallback"
    
    # For now, create a placeholder that points to Python package
    cat > "$PACKAGES_DIR/$package_name" << EOF
# COINjecture v${VERSION} - ${platform} Standalone Package
# 
# This is a placeholder for the standalone package.
# Please use the Python package for now:
# COINjecture-${platform}-v${VERSION}-Python.zip
#
# Standalone packages will be available in future releases.
EOF
    
    echo "✅ Created placeholder for $package_name"
}

# Build all packages
echo "🔨 Building all packages..."

# Python packages
build_python_package "macOS"
build_python_package "Windows" 
build_python_package "Linux"

# Standalone packages (placeholders)
build_standalone_package "macOS"
build_standalone_package "Windows"
build_standalone_package "Linux"

# Create package index
echo "📋 Creating package index..."

cat > "$PACKAGES_DIR/README.md" << EOF
# COINjecture v${VERSION} - Download Packages

## 🚀 **NEW: Dynamic Gas Calculation System**

COINjecture v${VERSION} introduces revolutionary **IPFS-based dynamic gas calculation** that scales with actual computational complexity.

### ⛽ **Gas Range Examples**
- **Simple Problems**: ~38,000-110,000 gas
- **Medium Problems**: ~200,000-400,000 gas  
- **Complex Problems**: ~500,000-600,000 gas
- **Very Complex**: 1,000,000+ gas

## 📦 **Available Packages**

### **Python Packages (Ready)**
- **macOS**: \`COINjecture-macOS-v${VERSION}-Python.zip\`
- **Windows**: \`COINjecture-Windows-v${VERSION}-Python.zip\`
- **Linux**: \`COINjecture-Linux-v${VERSION}-Python.zip\`

### **Standalone Packages (Coming Soon)**
- **macOS**: \`COINjecture-macOS-v${VERSION}-Standalone.zip\` (Placeholder)
- **Windows**: \`COINjecture-Windows-v${VERSION}-Standalone.zip\` (Placeholder)
- **Linux**: \`COINjecture-Linux-v${VERSION}-Standalone.zip\` (Placeholder)

## 🎯 **Quick Start**

1. **Download** the Python package for your platform
2. **Extract** and run \`./install.sh\`
3. **Start** with \`./start_coinjecture.sh\` (Unix) or \`start_coinjecture.bat\` (Windows)
4. **Choose** "Interactive Menu" for guided experience
5. **Start** mining with dynamic gas calculation!

## 🌐 **Live Server**

- **API Server**: http://167.172.213.70:12346
- **Health Check**: http://167.172.213.70:12346/health
- **Dynamic Gas**: Real-time gas calculation based on computational complexity

## 🔧 **CLI Commands**

\`\`\`bash
# Generate wallet
python3 src/cli.py wallet-generate --output ./my_wallet.json

# Check balance
python3 src/cli.py wallet-balance --wallet ./my_wallet.json

# Check rewards
python3 src/cli.py rewards --address BEANS...

# Start mining
python3 src/cli.py mine --config ./config.json

# Interactive menu
python3 src/cli.py interactive
\`\`\`

## 🎉 **Ready to Mine!**

Your COINjecture CLI v${VERSION} is ready with:
- ✅ **Dynamic Gas Calculation** - Real computational complexity-based gas costs
- ✅ **Enhanced CLI** - Updated commands with gas integration
- ✅ **Live Mining** - Real-time gas calculation during mining
- ✅ **Database Consistency** - All blocks updated with new gas values
- ✅ **API Integration** - Full integration with live server

**Start mining and experience the new dynamic gas calculation system!** 🚀

---

*Built with ❤️ for the COINjecture community - Version ${VERSION}*
EOF

# Create download links file
cat > "$PACKAGES_DIR/download_links.txt" << EOF
COINjecture v${VERSION} - Download Links
=====================================

Python Packages (Ready):
- macOS: COINjecture-macOS-v${VERSION}-Python.zip
- Windows: COINjecture-Windows-v${VERSION}-Python.zip  
- Linux: COINjecture-Linux-v${VERSION}-Python.zip

Standalone Packages (Coming Soon):
- macOS: COINjecture-macOS-v${VERSION}-Standalone.zip
- Windows: COINjecture-Windows-v${VERSION}-Standalone.zip
- Linux: COINjecture-Linux-v${VERSION}-Standalone.zip

Live Server: http://167.172.213.70:12346
Health Check: http://167.172.213.70:12346/health

Features:
- Dynamic Gas Calculation (38K-600K+ gas range)
- IPFS-based gas calculation
- Live mining with real-time gas costs
- Enhanced CLI with gas integration
- Complete wallet and mining system

Built with ❤️ for the COINjecture community
EOF

echo ""
echo "✅ All packages built successfully!"
echo "📁 Packages location: $PACKAGES_DIR"
echo "📋 Package index: $PACKAGES_DIR/README.md"
echo "🔗 Download links: $PACKAGES_DIR/download_links.txt"
echo ""
echo "🎯 Ready for distribution!"
echo "🚀 COINjecture v${VERSION} with Dynamic Gas Calculation is ready!"
