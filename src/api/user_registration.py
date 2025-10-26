"""
User registration and authentication API endpoints.
"""

from flask import Blueprint, request, jsonify
from api.user_auth import auth_manager, AuthMethod
import os

# Create blueprint for user management
user_bp = Blueprint('user', __name__, url_prefix='/v1/user')


@user_bp.route('/register', methods=['POST'])
def register_user():
    """Register a new mining user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "No JSON data provided"
            }), 400
        
        user_id = data.get('user_id')
        auth_method = data.get('auth_method', 'hmac_personal')
        tier = data.get('tier', 'TIER_2_DESKTOP')
        
        if not user_id:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "user_id is required"
            }), 400
        
        # Validate auth method
        try:
            auth_enum = AuthMethod(auth_method)
        except ValueError:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": f"Invalid auth_method. Must be one of: {[m.value for m in AuthMethod]}"
            }), 400
        
        # Register user
        credentials = auth_manager.register_user(user_id, auth_enum, tier)
        
        response_data = {
            "status": "success",
            "user_id": credentials[0],
            "auth_method": auth_method,
            "tier": tier
        }
        
        if auth_enum == AuthMethod.HMAC_PERSONAL:
            response_data["api_key"] = credentials[1]
            response_data["instructions"] = {
                "authentication": "Include X-User-ID and X-Signature headers",
                "signature": "HMAC-SHA256 of canonical JSON body using your API key",
                "timestamp": "Include X-Timestamp header with current Unix timestamp"
            }
        else:
            response_data["shared_secret"] = credentials[1]
            response_data["instructions"] = {
                "authentication": "Include X-Signature header",
                "signature": "HMAC-SHA256 of canonical JSON body using shared secret",
                "timestamp": "Include X-Timestamp header with current Unix timestamp"
            }
        
        return jsonify(response_data), 201
        
    except ValueError as e:
        return jsonify({
            "status": "error",
            "error": "INVALID",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500


@user_bp.route('/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile information."""
    try:
        profile = auth_manager.get_user_profile(user_id)
        if not profile:
            return jsonify({
                "status": "error",
                "error": "NOT_FOUND",
                "message": f"User {user_id} not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "profile": {
                "user_id": profile.user_id,
                "auth_method": profile.auth_method.value,
                "tier": profile.tier,
                "rate_limit": profile.rate_limit,
                "is_active": profile.is_active
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500


@user_bp.route('/update-tier', methods=['POST'])
def update_user_tier():
    """Update user's mining tier."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "No JSON data provided"
            }), 400
        
        user_id = data.get('user_id')
        tier = data.get('tier')
        
        if not user_id or not tier:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "user_id and tier are required"
            }), 400
        
        success = auth_manager.update_user_tier(user_id, tier)
        if not success:
            return jsonify({
                "status": "error",
                "error": "NOT_FOUND",
                "message": f"User {user_id} not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "message": f"User {user_id} tier updated to {tier}"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500


@user_bp.route('/auth-test', methods=['POST'])
def test_authentication():
    """Test authentication for a user."""
    try:
        # This endpoint requires authentication to test
        headers = request.headers
        body = request.get_json() or {}
        
        user_id = auth_manager.authenticate_request(body, headers)
        if not user_id:
            return jsonify({
                "status": "error",
                "error": "UNAUTHORIZED",
                "message": "Authentication failed"
            }), 401
        
        profile = auth_manager.get_user_profile(user_id)
        return jsonify({
            "status": "success",
            "message": "Authentication successful",
            "user_id": user_id,
            "tier": profile.tier if profile else "unknown"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500
