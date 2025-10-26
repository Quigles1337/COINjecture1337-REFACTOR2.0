"""
Enhanced user authentication system for COINjecture mining network.
Supports multiple authentication methods for different user types.
"""

from __future__ import annotations

import hashlib
import hmac
import time
import secrets
import json
import os
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class AuthMethod(Enum):
    """Authentication methods supported."""
    HMAC_SHARED = "hmac_shared"      # Shared secret (current)
    HMAC_PERSONAL = "hmac_personal"  # Personal API key
    JWT_TOKEN = "jwt_token"         # JWT tokens
    WALLET_SIGNATURE = "wallet_sig" # Wallet signature


@dataclass
class UserProfile:
    """User profile for authentication."""
    user_id: str
    auth_method: AuthMethod
    api_key: Optional[str] = None
    public_key: Optional[str] = None
    tier: str = "TIER_2_DESKTOP"
    rate_limit: int = 100  # requests per minute
    is_active: bool = True


class UserAuthManager:
    """Enhanced authentication manager supporting multiple methods."""
    
    def __init__(self, master_secret: str):
        self.master_secret = master_secret.encode("utf-8")
        self.users: Dict[str, UserProfile] = {}
        self.shared_secret = os.environ.get("FAUCET_HMAC_SECRET", "dev-secret")
        self.max_drift_sec = 300
        
        # Initialize with default development user
        self._create_default_user()
    
    def _create_default_user(self):
        """Create default development user."""
        dev_user = UserProfile(
            user_id="dev_miner",
            auth_method=AuthMethod.HMAC_SHARED,
            tier="TIER_2_DESKTOP",
            rate_limit=1000
        )
        self.users["dev_miner"] = dev_user
    
    def register_user(self, user_id: str, auth_method: AuthMethod, 
                     tier: str = "TIER_2_DESKTOP") -> Tuple[str, str]:
        """Register a new user and return credentials."""
        if user_id in self.users:
            raise ValueError(f"User {user_id} already exists")
        
        if auth_method == AuthMethod.HMAC_PERSONAL:
            # Generate personal API key
            api_key = self._generate_api_key(user_id)
            user = UserProfile(
                user_id=user_id,
                auth_method=auth_method,
                api_key=api_key,
                tier=tier
            )
        elif auth_method == AuthMethod.WALLET_SIGNATURE:
            # For wallet-based auth, user provides public key
            user = UserProfile(
                user_id=user_id,
                auth_method=auth_method,
                tier=tier
            )
        else:
            # Shared secret method
            user = UserProfile(
                user_id=user_id,
                auth_method=auth_method,
                tier=tier
            )
        
        self.users[user_id] = user
        
        if auth_method == AuthMethod.HMAC_PERSONAL:
            return user_id, api_key
        else:
            return user_id, self.shared_secret
    
    def _generate_api_key(self, user_id: str) -> str:
        """Generate a personal API key for the user."""
        timestamp = str(int(time.time()))
        data = f"{user_id}:{timestamp}:{secrets.token_hex(16)}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def authenticate_request(self, body: Dict, headers: Dict) -> Optional[str]:
        """Authenticate a request and return user_id if valid."""
        signature = headers.get("X-Signature", "")
        timestamp = headers.get("X-Timestamp", "")
        user_id = headers.get("X-User-ID", "")
        
        if not signature or not timestamp:
            return None
        
        # Check timestamp drift
        try:
            ts = float(timestamp)
            if abs(time.time() - ts) > self.max_drift_sec:
                return None
        except ValueError:
            return None
        
        # Try different authentication methods
        if user_id and user_id in self.users:
            user = self.users[user_id]
            
            if user.auth_method == AuthMethod.HMAC_PERSONAL and user.api_key:
                # Personal API key authentication
                if self._verify_personal_hmac(body, signature, user.api_key):
                    return user_id
            elif user.auth_method == AuthMethod.HMAC_SHARED:
                # Shared secret authentication
                if self._verify_shared_hmac(body, signature):
                    return user_id
            elif user.auth_method == AuthMethod.WALLET_SIGNATURE:
                # Wallet signature authentication (placeholder)
                if self._verify_wallet_signature(body, signature, user.public_key):
                    return user_id
        
        # Fallback to shared secret for backward compatibility
        if self._verify_shared_hmac(body, signature):
            return "anonymous"
        
        return None
    
    def _verify_shared_hmac(self, body: Dict, signature: str) -> bool:
        """Verify HMAC with shared secret."""
        canonical_body = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected = hmac.new(
            self.shared_secret.encode("utf-8"), 
            canonical_body, 
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    def _verify_personal_hmac(self, body: Dict, signature: str, api_key: str) -> bool:
        """Verify HMAC with personal API key."""
        canonical_body = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected = hmac.new(
            api_key.encode("utf-8"), 
            canonical_body, 
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    def _verify_wallet_signature(self, body: Dict, signature: str, public_key: str) -> bool:
        """Verify wallet signature (placeholder for crypto signature verification)."""
        # TODO: Implement actual cryptographic signature verification
        # This would verify that the signature was created by the private key
        # corresponding to the public key
        return True  # Placeholder
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user_id."""
        return self.users.get(user_id)
    
    def update_user_tier(self, user_id: str, tier: str) -> bool:
        """Update user's mining tier."""
        if user_id in self.users:
            self.users[user_id].tier = tier
            return True
        return False
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user."""
        if user_id in self.users:
            self.users[user_id].is_active = False
            return True
        return False


# Global auth manager instance
auth_manager = UserAuthManager("production-secret-key")
