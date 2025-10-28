#!/usr/bin/env python3
"""
COINjecture v3.15.0 Package Verification Script
Verifies that all packages are properly created and contain expected files.
"""

import os
import zipfile
from pathlib import Path

def verify_zip_package(zip_path, platform):
    """Verify a ZIP package contains expected files"""
    print(f"🔍 Verifying {zip_path.name}...")
    
    if not zip_path.exists():
        print(f"  ❌ Package not found: {zip_path}")
        return False
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            files = zipf.namelist()
            
            # Expected files/directories
            expected = [
                'src/',
                'config/',
                'scripts/',
                'docs/',
                'requirements.txt',
                'VERSION',
                'README.md',
                'LICENSE'
            ]
            
            # Platform-specific files
            if platform == "Windows":
                expected.extend(['install.bat', 'start_coinjecture.bat'])
            else:
                expected.extend(['install.sh', 'start_coinjecture.sh'])
            
            missing = []
            for item in expected:
                if not any(f.startswith(item) for f in files):
                    missing.append(item)
            
            if missing:
                print(f"  ❌ Missing files: {missing}")
                return False
            
            print(f"  ✅ Package verified successfully ({len(files)} files)")
            return True
            
    except Exception as e:
        print(f"  ❌ Error reading package: {e}")
        return False

def verify_version_consistency():
    """Verify version consistency across files"""
    print("🔍 Verifying version consistency...")
    
    # Check VERSION file
    version_file = Path("VERSION")
    if version_file.exists():
        with open(version_file, 'r') as f:
            version = f.read().strip()
        print(f"  📋 VERSION file: {version}")
    else:
        print("  ❌ VERSION file not found")
        return False
    
    # Check CLI version
    cli_file = Path("src/cli.py")
    if cli_file.exists():
        with open(cli_file, 'r') as f:
            content = f.read()
            if f'VERSION = "3.15.0"' in content:
                print("  ✅ CLI version: 3.15.0")
            else:
                print("  ❌ CLI version mismatch")
                return False
    else:
        print("  ❌ CLI file not found")
        return False
    
    return True

def main():
    """Main verification function"""
    print("🚀 COINjecture v3.15.0 Package Verification")
    print("=" * 50)
    
    # Verify version consistency
    if not verify_version_consistency():
        print("\n❌ Version consistency check failed")
        return False
    
    # Verify packages
    packages_dir = Path("dist/packages")
    if not packages_dir.exists():
        print("\n❌ Packages directory not found")
        return False
    
    platforms = ["macOS", "Windows", "Linux"]
    all_good = True
    
    for platform in platforms:
        zip_path = packages_dir / f"COINjecture-{platform}-v3.15.0-Python.zip"
        if not verify_zip_package(zip_path, platform):
            all_good = False
    
    # Check for additional packages
    additional_packages = [
        "COINjecture-3.15.0-macOS.dmg",
        "COINjecture-3.15.0-macOS.app"
    ]
    
    for package in additional_packages:
        package_path = packages_dir / package
        if package_path.exists():
            size_mb = package_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {package} ({size_mb:.1f} MB)")
        else:
            print(f"  ⚠️  {package} not found (optional)")
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All packages verified successfully!")
        print("✅ Ready for distribution")
    else:
        print("❌ Some packages failed verification")
        print("🔧 Please check and fix issues")
    
    return all_good

if __name__ == "__main__":
    main()
