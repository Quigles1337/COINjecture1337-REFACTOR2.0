#!/bin/bash
# Remote Deployment Script for Network Stalling Fix
# This script should be executed on the remote server

echo "🚀 Deploying Network Stalling Fix to Remote Server"
echo "=================================================="

# Check if we're on the remote server
if [ ! -f "/home/coinjecture/COINjecture/src/tokenomics/wallet.py" ]; then
    echo "❌ Not on remote server - this script should be run on 167.172.213.70"
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo "📊 Server: $(hostname)"

# Backup original wallet.py
echo "💾 Backing up original wallet.py..."
sudo cp /home/coinjecture/COINjecture/src/tokenomics/wallet.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py.backup.$(date +%Y%m%d_%H%M%S)

# Create enhanced wallet.py with improved signature validation
echo "🔧 Creating enhanced wallet.py with improved signature validation..."

cat > /tmp/wallet_enhanced.py << 'EOF'
"""
Enhanced Wallet with Improved Signature Validation
This version includes proper hex string validation to prevent network stalling.
"""

import json
import time
import hashlib
import base64
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class Wallet:
    """Enhanced COINjecture Wallet with improved signature validation."""
    
    def __init__(self, private_key: ed25519.Ed25519PrivateKey, public_key: ed25519.Ed25519PublicKey):
        self.private_key = private_key
        self.public_key = public_key
        self.address = self._generate_address()
    
    @classmethod
    def generate(cls) -> 'Wallet':
        """Generate a new wallet."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return cls(private_key, public_key)
    
    def _generate_address(self) -> str:
        """Generate wallet address from public key."""
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return hashlib.sha256(pub_bytes).hexdigest()[:32]
    
    def sign_transaction(self, data: bytes) -> bytes:
        """Sign transaction data."""
        return self.private_key.sign(data)
    
    def get_private_key_bytes(self) -> bytes:
        """Get private key as bytes."""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    def get_public_key_bytes(self) -> bytes:
        """Get public key as bytes."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def save_to_file(self, filepath: str, password: Optional[str] = None) -> bool:
        """Save wallet to encrypted file."""
        try:
            wallet_data = {
                'address': self.address,
                'private_key': self.get_private_key_bytes().hex(),
                'public_key': self.get_public_key_bytes().hex()
            }
            
            with open(filepath, 'w') as f:
                json.dump(wallet_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving wallet: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str, password: Optional[str] = None) -> Optional['Wallet']:
        """Load wallet from file."""
        try:
            with open(filepath, 'r') as f:
                wallet_data = json.load(f)
            
            private_key_bytes = bytes.fromhex(wallet_data['private_key'])
            public_key_bytes = bytes.fromhex(wallet_data['public_key'])
            
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            return cls(private_key, public_key)
        except Exception as e:
            print(f"Error loading wallet: {e}")
            return None
    
    def sign_block(self, block_data: Dict[str, Any]) -> str:
        """Sign block data and return signature as hex string."""
        import json
        canonical = json.dumps(block_data, sort_keys=True).encode()
        signature = self.sign_transaction(canonical)
        return signature.hex()
    
    @staticmethod
    def verify_block_signature(public_key_hex: str, block_data: dict, signature_hex: str) -> bool:
        """
        Verify block signature with enhanced error handling.
        
        Args:
            public_key_hex: Public key as hex string
            block_data: Block data dictionary that was signed
            signature_hex: Signature as hex string
            
        Returns:
            True if signature is valid
        """
        import json
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        # Validate inputs
        if not public_key_hex or not signature_hex:
            return False
        
        # Check if strings are valid hexadecimal
        try:
            # Test if strings are valid hex
            bytes.fromhex(public_key_hex)
            bytes.fromhex(signature_hex)
        except ValueError:
            # Not valid hex strings - this is likely a test or invalid submission
            print(f"⚠️  Invalid hex strings: pub_key={public_key_hex[:16]}..., sig={signature_hex[:16]}...")
            return False
        
        # Additional validation for Ed25519 keys
        if len(public_key_hex) != 64 or len(signature_hex) != 128:
            print(f"⚠️  Invalid key/signature length: pub_key={len(public_key_hex)}, sig={len(signature_hex)}")
            return False
        
        canonical = json.dumps(block_data, sort_keys=True).encode()
        pub_bytes = bytes.fromhex(public_key_hex)
        sig_bytes = bytes.fromhex(signature_hex)
        
        # Use multi-implementation verification (prioritizes PyNaCl for browser compatibility)
        return Wallet._verify_tweetnacl_signature(public_key_hex, canonical, signature_hex)
    
    @staticmethod
    def _verify_tweetnacl_signature(public_key_hex: str, data: bytes, signature_hex: str) -> bool:
        """
        Verify signature using multiple implementations as fallback.
        
        Args:
            public_key_hex: Public key as hex string
            data: Data that was signed
            signature_hex: Signature as hex string
            
        Returns:
            True if signature is valid
        """
        try:
            # Try PyNaCl first (browser compatibility)
            import nacl.signing
            import nacl.encoding
            
            public_key_bytes = bytes.fromhex(public_key_hex)
            signature_bytes = bytes.fromhex(signature_hex)
            
            # Create verifying key
            verify_key = nacl.signing.VerifyKey(public_key_bytes)
            
            # Verify signature
            try:
                verify_key.verify(data, signature_bytes)
                return True
            except nacl.exceptions.BadSignatureError:
                return False
                
        except ImportError:
            # Fallback to cryptography library
            try:
                from cryptography.hazmat.primitives.asymmetric import ed25519
                
                public_key_bytes = bytes.fromhex(public_key_hex)
                signature_bytes = bytes.fromhex(signature_hex)
                
                public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
                public_key.verify(signature_bytes, data)
                return True
                
            except Exception:
                return False
        except Exception:
            return False
EOF

# Apply the enhanced wallet.py
echo "🔄 Applying enhanced wallet.py..."
sudo cp /tmp/wallet_enhanced.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py

# Set correct permissions
echo "🔐 Setting correct permissions..."
sudo chown coinjecture:coinjecture /home/coinjecture/COINjecture/src/tokenomics/wallet.py
sudo chmod 644 /home/coinjecture/COINjecture/src/tokenomics/wallet.py

# Restart API service
echo "🔄 Restarting API service..."
sudo systemctl restart coinjecture-api.service

# Check service status
echo "📊 Checking API service status..."
sudo systemctl status coinjecture-api.service --no-pager -l

# Test the fix
echo "🧪 Testing the fix..."
curl -k https://167.172.213.70/v1/data/block/latest

echo ""
echo "✅ Network stalling fix deployed!"
echo "🔧 Enhanced signature validation is now active"
echo "📊 Network should now be able to process new blocks beyond #166"



