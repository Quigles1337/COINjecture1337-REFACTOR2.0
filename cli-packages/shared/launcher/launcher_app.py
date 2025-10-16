#!/usr/bin/env python3
"""
COINjecture Application Launcher

Main entry point for packaged COINjecture applications.
Provides a user-friendly interface for non-developers to access
both the interactive menu and direct CLI functionality.
"""

import os
import sys
import subprocess
import platform
import time
from pathlib import Path

# Add src directory to path for imports
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def show_logo():
    """Display the COINjecture logo with enhanced styling."""
    logo = """
    ╔════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                            ║
    ║   ██████╗ ██████╗ ██╗███╗   ██╗     ██╗███████╗ ██████╗████████╗██╗   ██╗██████╗ ███████╗  ║
    ║  ██╔════╝██╔═══██╗██║████╗  ██║     ██║██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝  ║
    ║  ██║     ██║   ██║██║██╔██╗ ██║     ██║█████╗  ██║        ██║   ██║   ██║██████╔╝█████╗    ║
    ║  ██║     ██║   ██║██║██║╚██╗██║██   ██║██╔══╝  ██║        ██║   ██║   ██║██╔══██╗██╔══╝    ║
    ║  ╚██████╗╚██████╔╝██║██║ ╚████║╚█████╔╝███████╗╚██████╗   ██║   ╚██████╔╝██║  ██╗███████╗  ║
    ║   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝  ║
    ║                                                                                            ║
    ║         🔬 Mathematical Proof-of-Work Mining                                               ║
    ║         🌟 Transform blockchain mining into meaningful discovery                           ║
    ║         💎 Every proof counts. Every discovery pays.                                       ║
    ║                                                                                            ║
    ╚════════════════════════════════════════════════════════════════════════════════════════════╝
    """
    print(logo)

def show_welcome():
    """Display welcome message and version info."""
    print("\n" + "="*80)
    print("🚀 COINjecture v3.4.0 - Proof-of-Work Blockchain")
    print("="*80)
    print("Welcome to COINjecture! Choose how you'd like to get started:")
    print()

def show_menu():
    """Display the main launcher menu."""
    print("📋 Available Options:")
    print()
    print("  [1] 🎯 Interactive Menu")
    print("      • Guided interface for all operations")
    print("      • Perfect for beginners")
    print("      • Step-by-step workflows")
    print()
    print("  [2] 💻 Direct CLI Terminal")
    print("      • Full command-line access")
    print("      • For advanced users")
    print("      • Run any coinjecture command")
    print()
    print("  [3] 📚 Quick Start Guides")
    print("      • Mining tutorial")
    print("      • Wallet setup")
    print("      • Problem submission")
    print()
    print("  [4] 🔧 Setup & Configuration")
    print("      • Initialize node")
    print("      • Configure settings")
    print("      • Check system requirements")
    print()
    print("  [5] ❓ Help & Documentation")
    print("      • User guide")
    print("      • Command reference")
    print("      • Troubleshooting")
    print()
    print("  [6] 🚪 Exit")
    print()

def get_user_choice():
    """Get user's menu choice with validation."""
    while True:
        try:
            choice = input("Enter your choice (1-6): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6']:
                return int(choice)
            else:
                print("❌ Please enter a number between 1 and 6.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
        except:
            print("❌ Please enter a valid number.")

def launch_interactive_menu():
    """Launch the COINjecture interactive menu."""
    print("🎯 Launching Interactive Menu...")
    print("="*50)
    
    try:
        from cli import COINjectureCLI
        cli = COINjectureCLI()
        result = cli.run(['interactive'])
        if result != 0:
            print(f"❌ Interactive menu exited with code {result}")
            input("Press Enter to continue...")
    except Exception as e:
        print(f"❌ Error launching interactive menu: {e}")
        input("Press Enter to continue...")

def launch_cli_terminal():
    """Launch a terminal with COINjecture CLI ready to use."""
    print("💻 Opening CLI Terminal...")
    print("="*50)
    
    # Get the current script directory
    script_dir = Path(__file__).parent.parent
    
    # Create a temporary script to launch CLI
    if platform.system() == "Windows":
        temp_script = script_dir / "temp_cli_launcher.bat"
        script_content = f"""@echo off
cd /d "{script_dir}"
echo Starting COINjecture CLI...
echo.
echo Available commands:
echo   coinjecture --help          - Show all commands
echo   coinjecture wallet-create   - Create a new wallet
echo   coinjecture mine            - Start mining
echo   coinjecture interactive     - Launch interactive menu
echo.
python -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
echo.
echo Type 'exit' to close this terminal.
cmd /k
"""
    else:
        temp_script = script_dir / "temp_cli_launcher.sh"
        script_content = f"""#!/bin/bash
cd "{script_dir}"
echo "Starting COINjecture CLI..."
echo ""
echo "Available commands:"
echo "  python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])\""
echo "  python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['wallet-create', 'my_wallet'])\""
echo "  python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['mine'])\""
echo ""
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
echo ""
echo "Type 'exit' to close this terminal."
exec $SHELL
"""
    
    try:
        # Write temporary script
        with open(temp_script, 'w') as f:
            f.write(script_content)
        
        # Make executable on Unix systems
        if platform.system() != "Windows":
            os.chmod(temp_script, 0o755)
        
        # Launch terminal
        if platform.system() == "Windows":
            subprocess.Popen([str(temp_script)], shell=True)
        else:
            # Try different terminal emulators
            terminals = ['gnome-terminal', 'xterm', 'konsole', 'xfce4-terminal', 'mate-terminal']
            launched = False
            
            for terminal in terminals:
                try:
                    if terminal == 'gnome-terminal':
                        subprocess.Popen([terminal, '--', 'bash', str(temp_script)])
                    elif terminal == 'xterm':
                        subprocess.Popen([terminal, '-e', 'bash', str(temp_script)])
                    else:
                        subprocess.Popen([terminal, '-e', str(temp_script)])
                    launched = True
                    break
                except FileNotFoundError:
                    continue
            
            if not launched:
                print("❌ Could not find a suitable terminal emulator.")
                print("Please run the following command in your terminal:")
                print(f"bash {temp_script}")
                input("Press Enter to continue...")
        
        print("✅ Terminal launched successfully!")
        print("The CLI is ready to use in the new terminal window.")
        
    except Exception as e:
        print(f"❌ Error launching terminal: {e}")
        input("Press Enter to continue...")
    finally:
        # Clean up temporary script after a delay
        def cleanup():
            time.sleep(5)
            try:
                if temp_script.exists():
                    temp_script.unlink()
            except:
                pass
        
        import threading
        threading.Thread(target=cleanup, daemon=True).start()

def show_quick_start_guides():
    """Display quick start guides."""
    print("📚 Quick Start Guides")
    print("="*50)
    print()
    print("🔨 Mining Tutorial:")
    print("   1. Create a wallet: wallet-create my_miner")
    print("   2. Start mining: mine")
    print("   3. Check balance: wallet-balance <your_address>")
    print()
    print("💰 Wallet Setup:")
    print("   1. Create wallet: wallet-create my_wallet")
    print("   2. List wallets: wallet-list")
    print("   3. Check balance: wallet-balance <address>")
    print()
    print("📝 Problem Submission:")
    print("   1. Submit problem: submit-problem --type subset_sum --bounty 100")
    print("   2. Check status: check-submission <submission_id>")
    print("   3. List submissions: list-submissions")
    print()
    print("🌐 Connect to Live Network:")
    print("   • Live API: http://167.172.213.70:5000")
    print("   • Health check: http://167.172.213.70:5000/health")
    print("   • Latest block: http://167.172.213.70:5000/v1/data/block/latest")
    print()
    input("Press Enter to continue...")

def show_setup_configuration():
    """Show setup and configuration options."""
    print("🔧 Setup & Configuration")
    print("="*50)
    print()
    print("Available setup options:")
    print()
    print("  [1] Initialize new node")
    print("  [2] Check system requirements")
    print("  [3] Configure network settings")
    print("  [4] Test installation")
    print("  [5] Back to main menu")
    print()
    
    while True:
        try:
            choice = input("Choose setup option (1-5): ").strip()
            if choice == '1':
                print("🏗️ Initializing new node...")
                try:
                    from cli import COINjectureCLI
                    cli = COINjectureCLI()
                    cli.run(['init', '--role', 'miner'])
                except Exception as e:
                    print(f"❌ Error: {e}")
                break
            elif choice == '2':
                print("🔍 Checking system requirements...")
                print(f"✅ Python version: {sys.version}")
                print(f"✅ Platform: {platform.system()} {platform.release()}")
                print(f"✅ Architecture: {platform.machine()}")
                break
            elif choice == '3':
                print("🌐 Network configuration...")
                print("Default settings:")
                print("  • Network ID: coinjecture-mainnet")
                print("  • Listen address: 0.0.0.0:8080")
                print("  • Live API: http://167.172.213.70:5000")
                break
            elif choice == '4':
                print("🧪 Testing installation...")
                try:
                    from cli import COINjectureCLI
                    cli = COINjectureCLI()
                    result = cli.run(['--help'])
                    if result == 0:
                        print("✅ Installation test passed!")
                    else:
                        print("❌ Installation test failed!")
                except Exception as e:
                    print(f"❌ Test error: {e}")
                break
            elif choice == '5':
                break
            else:
                print("❌ Please enter 1-5.")
        except KeyboardInterrupt:
            break
    
    input("Press Enter to continue...")

def show_help_documentation():
    """Show help and documentation."""
    print("❓ Help & Documentation")
    print("="*50)
    print()
    print("📖 Documentation Files:")
    print("  • README.md - Project overview")
    print("  • USER_GUIDE.md - Detailed user instructions")
    print("  • QUICK_REFERENCE.md - Copy-paste commands")
    print("  • DOWNLOAD_PACKAGES.md - Installation options")
    print()
    print("🔗 Online Resources:")
    print("  • GitHub: https://github.com/beanapologist/COINjecture")
    print("  • Live API: http://167.172.213.70:5000")
    print("  • Health Check: http://167.172.213.70:5000/health")
    print()
    print("🆘 Getting Help:")
    print("  • Run '--help' for command reference")
    print("  • Use interactive menu for guided workflows")
    print("  • Check logs in the 'logs/' directory")
    print()
    print("🐛 Troubleshooting:")
    print("  • Ensure Python 3.8+ is installed")
    print("  • Check internet connection for live API")
    print("  • Verify file permissions on data directory")
    print()
    input("Press Enter to continue...")

def main():
    """Main launcher application."""
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Show logo and welcome
    show_logo()
    show_welcome()
    
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == 1:
            launch_interactive_menu()
        elif choice == 2:
            launch_cli_terminal()
        elif choice == 3:
            show_quick_start_guides()
        elif choice == 4:
            show_setup_configuration()
        elif choice == 5:
            show_help_documentation()
        elif choice == 6:
            print("👋 Thank you for using COINjecture!")
            print("Happy mining! ⛏️")
            break
        
        # Clear screen for next iteration
        os.system('cls' if os.name == 'nt' else 'clear')
        show_logo()
        show_welcome()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
