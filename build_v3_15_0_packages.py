#!/usr/bin/env python3
"""
Build COINjecture v3.15.0 Release Packages
Creates distribution packages for all platforms with proper versioning.
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

def create_package_structure():
    """Create the basic package structure for v3.15.0"""
    print("📦 Creating COINjecture v3.15.0 package structure...")
    
    # Create directories
    packages_dir = Path("dist/packages")
    packages_dir.mkdir(parents=True, exist_ok=True)
    
    # Create platform-specific directories
    platforms = ["macOS", "Windows", "Linux"]
    for platform in platforms:
        platform_dir = packages_dir / f"COINjecture-{platform}-v3.15.0"
        platform_dir.mkdir(exist_ok=True)
        
        # Create basic structure
        (platform_dir / "src").mkdir(exist_ok=True)
        (platform_dir / "config").mkdir(exist_ok=True)
        (platform_dir / "scripts").mkdir(exist_ok=True)
        (platform_dir / "docs").mkdir(exist_ok=True)
    
    return packages_dir

def copy_source_files(packages_dir):
    """Copy source files to all platform packages"""
    print("📋 Copying source files to packages...")
    
    # Files to copy
    source_files = [
        "src/",
        "config/",
        "scripts/",
        "docs/",
        "requirements.txt",
        "VERSION",
        "README.md",
        "LICENSE"
    ]
    
    platforms = ["macOS", "Windows", "Linux"]
    
    for platform in platforms:
        platform_dir = packages_dir / f"COINjecture-{platform}-v3.15.0"
        
        for source in source_files:
            source_path = Path(source)
            if source_path.exists():
                if source_path.is_dir():
                    dest_path = platform_dir / source_path.name
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, platform_dir)
                print(f"  ✅ Copied {source} to {platform} package")

def create_install_scripts(packages_dir):
    """Create platform-specific install scripts"""
    print("🔧 Creating install scripts...")
    
    # macOS install script
    macos_script = """#!/bin/bash
echo "🚀 Installing COINjecture v3.15.0 for macOS..."
echo "📦 Setting up Python environment..."

# Check Python version
python3 --version || { echo "❌ Python 3.8+ required"; exit 1; }

# Install dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x scripts/*.sh

echo "✅ Installation complete!"
echo "🚀 Run: ./start_coinjecture.sh"
"""
    
    # Windows install script
    windows_script = """@echo off
echo 🚀 Installing COINjecture v3.15.0 for Windows...
echo 📦 Setting up Python environment...

REM Check Python version
python --version || (echo ❌ Python 3.8+ required && exit /b 1)

REM Install dependencies
pip install -r requirements.txt

echo ✅ Installation complete!
echo 🚀 Run: start_coinjecture.bat
"""
    
    # Linux install script
    linux_script = """#!/bin/bash
echo "🚀 Installing COINjecture v3.15.0 for Linux..."
echo "📦 Setting up Python environment..."

# Check Python version
python3 --version || { echo "❌ Python 3.8+ required"; exit 1; }

# Install dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x scripts/*.sh

echo "✅ Installation complete!"
echo "🚀 Run: ./start_coinjecture.sh"
"""
    
    # Write install scripts
    platforms = [
        ("macOS", "install.sh", macos_script),
        ("Windows", "install.bat", windows_script),
        ("Linux", "install.sh", linux_script)
    ]
    
    for platform, filename, content in platforms:
        platform_dir = packages_dir / f"COINjecture-{platform}-v3.15.0"
        script_path = platform_dir / filename
        with open(script_path, 'w') as f:
            f.write(content)
        
        # Make executable on Unix systems
        if platform != "Windows":
            os.chmod(script_path, 0o755)
        
        print(f"  ✅ Created {filename} for {platform}")

def create_launcher_scripts(packages_dir):
    """Create platform-specific launcher scripts"""
    print("🚀 Creating launcher scripts...")
    
    # macOS launcher
    macos_launcher = """#!/bin/bash
echo "🚀 Starting COINjecture v3.15.0..."
echo "🌐 Connecting to network..."

cd "$(dirname "$0")"
python3 src/cli.py interactive
"""
    
    # Windows launcher
    windows_launcher = """@echo off
echo 🚀 Starting COINjecture v3.15.0...
echo 🌐 Connecting to network...

cd /d "%~dp0"
python src/cli.py interactive
pause
"""
    
    # Linux launcher
    linux_launcher = """#!/bin/bash
echo "🚀 Starting COINjecture v3.15.0..."
echo "🌐 Connecting to network..."

cd "$(dirname "$0")"
python3 src/cli.py interactive
"""
    
    # Write launcher scripts
    platforms = [
        ("macOS", "start_coinjecture.sh", macos_launcher),
        ("Windows", "start_coinjecture.bat", windows_launcher),
        ("Linux", "start_coinjecture.sh", linux_launcher)
    ]
    
    for platform, filename, content in platforms:
        platform_dir = packages_dir / f"COINjecture-{platform}-v3.15.0"
        script_path = platform_dir / filename
        with open(script_path, 'w') as f:
            f.write(content)
        
        # Make executable on Unix systems
        if platform != "Windows":
            os.chmod(script_path, 0o755)
        
        print(f"  ✅ Created {filename} for {platform}")

def create_readme_files(packages_dir):
    """Create README files for each platform"""
    print("📚 Creating README files...")
    
    readme_content = """# COINjecture v3.15.0

## 🚀 Dynamic Gas Calculation System

COINjecture is a revolutionary proof-of-work blockchain that uses computational complexity and dynamic gas calculation to secure the network.

### ✨ What's New in v3.15.0

- **Dynamic Gas Calculation**: IPFS-based gas costs scaling with computational complexity (38K-600K+ gas range)
- **Enhanced CLI**: All commands now support dynamic gas calculation with improved error handling
- **Live Integration**: Real-time gas calculation during mining with live server connectivity
- **Complete Packages**: Ready-to-use packages for all platforms with automated installation

### 🚀 Quick Start

1. **Install**: Run the install script for your platform
2. **Launch**: Run the start script
3. **Mine**: Choose "Interactive Menu" and start mining!

### 📋 System Requirements

- Python 3.8+ (included in package)
- 4GB RAM minimum
- 2GB free disk space
- Internet connection for mining

### 🔧 Installation

**macOS/Linux:**
```bash
./install.sh
./start_coinjecture.sh
```

**Windows:**
```cmd
install.bat
start_coinjecture.bat
```

### 🌐 Network

- **API URL**: http://167.172.213.70:12346
- **P2P Port**: 12345
- **IPFS**: http://localhost:5001

### 📚 Documentation

- Interactive CLI with built-in help
- Web interface: https://coinjecture.com
- API docs: https://coinjecture.com/api-docs

### 🆘 Support

- GitHub Issues: https://github.com/beanapologist/COINjecture/issues
- Community: https://github.com/beanapologist/COINjecture/discussions

---

**COINjecture v3.15.0** - Utility-Based Computational Work Blockchain
"""
    
    platforms = ["macOS", "Windows", "Linux"]
    for platform in platforms:
        platform_dir = packages_dir / f"COINjecture-{platform}-v3.15.0"
        readme_path = platform_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        print(f"  ✅ Created README.md for {platform}")

def create_zip_packages(packages_dir):
    """Create ZIP packages for distribution"""
    print("📦 Creating ZIP packages...")
    
    platforms = ["macOS", "Windows", "Linux"]
    
    for platform in platforms:
        platform_dir = packages_dir / f"COINjecture-{platform}-v3.15.0"
        zip_path = packages_dir / f"COINjecture-{platform}-v3.15.0-Python.zip"
        
        print(f"  📦 Creating {zip_path.name}...")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(platform_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(platform_dir)
                    zipf.write(file_path, arcname)
        
        # Get file size
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"    ✅ Created {zip_path.name} ({size_mb:.1f} MB)")

def main():
    """Main function to build all packages"""
    print("🚀 Building COINjecture v3.15.0 Release Packages")
    print("=" * 60)
    
    # Create package structure
    packages_dir = create_package_structure()
    
    # Copy source files
    copy_source_files(packages_dir)
    
    # Create install scripts
    create_install_scripts(packages_dir)
    
    # Create launcher scripts
    create_launcher_scripts(packages_dir)
    
    # Create README files
    create_readme_files(packages_dir)
    
    # Create ZIP packages
    create_zip_packages(packages_dir)
    
    print("\n" + "=" * 60)
    print("🎉 COINjecture v3.15.0 packages created successfully!")
    print("=" * 60)
    
    # Show package summary
    print("\n📦 Created packages:")
    for zip_file in packages_dir.glob("*.zip"):
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"  • {zip_file.name} ({size_mb:.1f} MB)")
    
    print(f"\n📁 Packages location: {packages_dir.absolute()}")
    print("\n🚀 Next steps:")
    print("1. Test packages on target platforms")
    print("2. Upload to GitHub Releases")
    print("3. Update download links in web interface")
    print("4. Share with users!")

if __name__ == "__main__":
    main()
