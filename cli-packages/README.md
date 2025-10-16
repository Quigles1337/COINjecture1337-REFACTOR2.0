# COINjecture CLI Packages

This directory contains all the tools and scripts needed to build standalone CLI application packages for COINjecture across all platforms.

## 📁 Directory Structure

```
cli-packages/
├── README.md                    # This file
├── shared/                      # Shared components across all platforms
│   ├── launcher/               # Application launcher and assets
│   │   ├── launcher_app.py     # Main launcher application
│   │   ├── icon.icns           # macOS icon (placeholder)
│   │   ├── icon.ico            # Windows icon (placeholder)
│   │   └── icon.png            # Linux icon (placeholder)
│   ├── specs/                  # PyInstaller specifications
│   │   └── coinjecture.spec    # Main PyInstaller spec file
│   └── docs/                   # Documentation
├── macos/                      # macOS-specific components
│   ├── builders/               # Build scripts
│   │   └── build_macos.sh      # macOS build script
│   ├── installers/             # Installer scripts
│   └── assets/                 # macOS-specific assets
├── windows/                    # Windows-specific components
│   ├── builders/               # Build scripts
│   │   └── build_windows.bat   # Windows build script
│   ├── installers/             # Installer scripts
│   └── assets/                 # Windows-specific assets
├── linux/                      # Linux-specific components
│   ├── builders/               # Build scripts
│   │   └── build_linux.sh      # Linux build script
│   ├── installers/             # Installer scripts
│   └── assets/                 # Linux-specific assets
└── build_packages.py           # Master build orchestrator
```

## 🚀 Quick Start

### Build for Current Platform

```bash
# From the project root
cd cli-packages
python3 build_packages.py
```

### Build for Specific Platform

```bash
# macOS
python3 build_packages.py --platform macOS

# Windows
python3 build_packages.py --platform Windows

# Linux
python3 build_packages.py --platform Linux
```

### Build for All Platforms

```bash
python3 build_packages.py --all
```

## 📦 Platform-Specific Builds

### macOS (.dmg)

**Requirements:**
- macOS 10.14+
- Python 3.8+
- PyInstaller
- hdiutil (built-in)

**Build:**
```bash
cd macos/builders
./build_macos.sh
```

**Output:**
- `COINjecture-3.4.0-macOS.dmg` - Drag-and-drop installer
- Native .app bundle with proper metadata
- Code signing ready (when certificates available)

### Windows (.exe + installer)

**Requirements:**
- Windows 10+
- Python 3.8+
- PyInstaller
- NSIS (optional, for installer)

**Build:**
```cmd
cd windows\builders
build_windows.bat
```

**Output:**
- `COINjecture-3.4.0-Windows.exe` - Standalone executable
- `COINjecture-3.4.0-Windows-Installer.exe` - Professional installer (if NSIS available)
- Start Menu and Desktop shortcuts
- Automatic uninstaller

### Linux (.AppImage)

**Requirements:**
- Modern Linux distribution
- Python 3.8+
- PyInstaller
- appimagetool (optional, for AppImage)

**Build:**
```bash
cd linux/builders
./build_linux.sh
```

**Output:**
- `COINjecture-3.4.0-Linux.AppImage` - Universal Linux package
- Portable executable (no installation required)
- Works on Ubuntu, Fedora, Arch, etc.

## 🎯 Application Features

### Dual Interface

The packaged applications provide two ways to use COINjecture:

1. **Interactive Menu** - Perfect for beginners
   - Guided step-by-step workflows
   - Visual menus and clear instructions
   - No command-line knowledge required

2. **Direct CLI Terminal** - For advanced users
   - Full command-line access
   - Complete control over all operations
   - Access to all COINjecture commands

### User Experience

**First Launch:**
- Beautiful COINjecture logo and branding
- Clear menu with numbered options
- Helpful descriptions for each choice
- Graceful error handling

**Features:**
- Zero Python installation required
- Automatic data directory setup
- Live network integration
- Wallet and transaction support
- Mining capabilities

## 🔧 Technical Details

### What's Bundled

Each package includes:
- **Python Runtime**: Complete Python 3.9+ interpreter
- **Dependencies**: Flask, cryptography, requests, etc.
- **Source Code**: Full COINjecture codebase
- **Documentation**: README, user guides, quick reference
- **Assets**: Icons, metadata, configuration files

### Data Storage

Applications automatically create data directories:
- **macOS**: `~/Library/Application Support/COINjecture/`
- **Windows**: `%APPDATA%\COINjecture\`
- **Linux**: `~/.coinjecture/`

### Network Integration

All packages connect to the live COINjecture network:
- **API Server**: http://167.172.213.70:5000
- **Health Check**: http://167.172.213.70:5000/health
- **Latest Block**: http://167.172.213.70:5000/v1/data/block/latest

## 📋 Build Process

### Prerequisites

1. **Install PyInstaller:**
   ```bash
   pip3 install pyinstaller
   ```

2. **Install Platform-Specific Tools:**
   - **macOS**: No additional tools needed
   - **Windows**: NSIS (optional, for installer)
   - **Linux**: appimagetool (optional, for AppImage)

### Build Steps

1. **Check Dependencies** - Verify Python and PyInstaller
2. **Create Assets** - Generate icons and metadata
3. **Build Executable** - Run PyInstaller with spec file
4. **Create Package** - Platform-specific packaging
5. **Test Package** - Verify functionality

### Output

Built packages are placed in:
```
dist/packages/
├── COINjecture-3.4.0-macOS.dmg
├── COINjecture-3.4.0-Windows.exe
├── COINjecture-3.4.0-Windows-Installer.exe
└── COINjecture-3.4.0-Linux.AppImage
```

## 🧪 Testing

### Local Testing

1. **Build Package** for your platform
2. **Test Installation** on clean system
3. **Verify Launch** - Double-click should work
4. **Test Features** - Wallet creation, mining, transactions
5. **Check Network** - Live API connectivity

### Cross-Platform Testing

1. **Build on Each Platform** - macOS, Windows, Linux
2. **Test on Clean VMs** - No Python installed
3. **Verify Functionality** - All features work
4. **Check File Permissions** - Proper access rights
5. **Test Uninstall** - Clean removal

## 📚 Documentation

### User Documentation

- **DISTRIBUTION.md** - Complete distribution guide
- **DOWNLOAD_PACKAGES.md** - Download and installation instructions
- **USER_GUIDE.md** - Detailed user instructions
- **QUICK_REFERENCE.md** - Copy-paste commands

### Developer Documentation

- **Build Scripts** - Platform-specific build instructions
- **PyInstaller Spec** - Bundling configuration
- **Launcher Code** - Application entry point
- **Asset Creation** - Icons and metadata

## 🚀 Distribution

### GitHub Releases

1. **Build Packages** for all platforms
2. **Test Packages** thoroughly
3. **Create Release** on GitHub
4. **Upload Artifacts** (DMG, EXE, AppImage)
5. **Update Documentation** with download links

### Release Automation

GitHub Actions workflow (`.github/workflows/build-packages.yml`):
- Automatically builds on release
- Tests on all platforms
- Uploads artifacts
- Creates release notes

## 🆘 Troubleshooting

### Common Issues

**Build Failures:**
- Check Python version (3.8+ required)
- Verify PyInstaller installation
- Ensure sufficient disk space
- Check file permissions

**Package Issues:**
- Test on clean system
- Verify all dependencies bundled
- Check network connectivity
- Review log files

**User Issues:**
- Provide clear installation instructions
- Include troubleshooting guide
- Offer multiple download options
- Maintain support documentation

## 🔄 Maintenance

### Updates

- **Version Bumping** - Update version numbers
- **Dependency Updates** - Keep packages current
- **Security Patches** - Apply security updates
- **Feature Additions** - Add new functionality

### Monitoring

- **Download Statistics** - Track package usage
- **User Feedback** - Collect user reports
- **Performance Metrics** - Monitor app performance
- **Error Tracking** - Log and fix issues

---

**Ready to distribute COINjecture to the world!** 🌍

The CLI packages provide a seamless experience for non-developers while maintaining full functionality for advanced users. Users can start mining, creating wallets, and participating in the COINjecture network with just a few clicks.
