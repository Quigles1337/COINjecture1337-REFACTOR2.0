"""
Wallet Address Utilities for COINjecture

Provides utilities for wallet address management and validation.
"""

import os
import json
from pathlib import Path
from typing import Optional
from .wallet import Wallet


def get_beans_address_from_wallet(wallet_file: str) -> str:
    """
    Load wallet and return BEANS-prefixed address.
    
    Args:
        wallet_file: Path to wallet JSON file
        
    Returns:
        BEANS-prefixed wallet address
    """
    try:
        wallet = Wallet.load_from_file(wallet_file)
        return wallet.address
    except Exception as e:
        raise ValueError(f"Failed to load wallet from {wallet_file}: {e}")


def validate_beans_address(address: str) -> bool:
    """
    Validate BEANS address format.
    
    Args:
        address: Address to validate
        
    Returns:
        True if address is valid BEANS format
    """
    return address.startswith("BEANS") and len(address) == 45


def get_miner_address_from_config(config_path: str = "config/miner_wallet.json") -> str:
    """
    Get miner address from configuration file.
    
    Args:
        config_path: Path to miner wallet configuration
        
    Returns:
        BEANS-prefixed miner address
    """
    try:
        return get_beans_address_from_wallet(config_path)
    except Exception as e:
        # Fallback to default address if config not found
        print(f"Warning: Could not load miner address from {config_path}: {e}")
        return "BEANSa93eefd297ae59e963d0977319690ffbc55e2b33"


def ensure_wallet_address_format(address: str) -> str:
    """
    Ensure address has proper BEANS format.
    
    Args:
        address: Address to format
        
    Returns:
        Properly formatted BEANS address
    """
    if not address.startswith("BEANS"):
        # If it's a raw hex address, add BEANS prefix
        if len(address) == 40:  # 20 bytes = 40 hex chars
            return f"BEANS{address}"
        else:
            raise ValueError(f"Invalid address format: {address}")
    
    return address


def load_miner_wallet_config() -> dict:
    """
    Load miner wallet configuration.
    
    Returns:
        Dictionary with wallet configuration
    """
    config_path = "config/miner_wallet.json"
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Miner wallet config not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load miner wallet config: {e}")


def get_miner_wallet_info() -> dict:
    """
    Get complete miner wallet information.
    
    Returns:
        Dictionary with wallet address, public key, and other info
    """
    try:
        config = load_miner_wallet_config()
        wallet = Wallet.load_from_file("config/miner_wallet.json")
        
        return {
            "address": wallet.address,
            "public_key": wallet.get_public_key_bytes().hex(),
            "config_file": "config/miner_wallet.json",
            "is_valid": validate_beans_address(wallet.address)
        }
    except Exception as e:
        raise ValueError(f"Failed to get miner wallet info: {e}")
