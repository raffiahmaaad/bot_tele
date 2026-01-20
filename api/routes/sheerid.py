"""
SheerID Verification API Routes

Endpoints for SheerID verification service.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

sheerid_bp = Blueprint('sheerid', __name__, url_prefix='/api/sheerid')


# Import database functions
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_cursor


# ==================== HELPER FUNCTIONS ====================

def get_user_id_from_jwt():
    """Get user_id from JWT identity (handles both int and string)"""
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return identity.get('id') or identity.get('user_id')
    try:
        return int(identity)
    except (ValueError, TypeError):
        return None


def get_sheerid_service():
    """Get SheerID service module"""
    try:
        # Direct import from the services/sheerid module
        bot_tele_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sheerid_path = os.path.join(bot_tele_path, 'services', 'sheerid')
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("sheerid_module", os.path.join(sheerid_path, '__init__.py'))
        sheerid_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sheerid_module)
        
        return sheerid_module
    except Exception as e:
        print(f"Error importing SheerID service: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==================== DATABASE OPERATIONS ====================

def get_user_settings(user_id: int) -> dict:
    """Get SheerID settings for user"""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM sheerid_settings WHERE user_id = %s
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            "proxy_enabled": False,
            "proxy_host": None,
            "proxy_port": None,
            "proxy_username": None,
            "proxy_password": None,
            "default_points_cost": 5
        }


def save_user_settings(user_id: int, settings: dict) -> bool:
    """Save SheerID settings for user"""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO sheerid_settings (user_id, proxy_enabled, proxy_host, proxy_port, proxy_username, proxy_password, default_points_cost, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                proxy_enabled = EXCLUDED.proxy_enabled,
                proxy_host = EXCLUDED.proxy_host,
                proxy_port = EXCLUDED.proxy_port,
                proxy_username = EXCLUDED.proxy_username,
                proxy_password = EXCLUDED.proxy_password,
                default_points_cost = EXCLUDED.default_points_cost,
                updated_at = NOW()
        """, (
            user_id,
            settings.get("proxy_enabled", False),
            settings.get("proxy_host"),
            settings.get("proxy_port"),
            settings.get("proxy_username"),
            settings.get("proxy_password"),
            settings.get("default_points_cost", 5)
        ))
        return True


def get_user_verifications(user_id: int, limit: int = 50) -> list:
    """Get user's verification history"""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM sheerid_verifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def create_verification_record(user_id: int, verify_type: str, verify_url: str, verify_id: str, points_cost: int) -> dict:
    """Create a new verification record"""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO sheerid_verifications (user_id, verify_type, verify_url, verify_id, points_cost, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            RETURNING *
        """, (user_id, verify_type, verify_url, verify_id, points_cost))
        return dict(cursor.fetchone())


def update_verification_result(verification_id: int, result: dict) -> bool:
    """Update verification with result"""
    with get_cursor() as cursor:
        status = "success" if result.get("success") else "failed"
        cursor.execute("""
            UPDATE sheerid_verifications SET
                status = %s,
                result_message = %s,
                student_name = %s,
                student_email = %s,
                school_name = %s,
                redirect_url = %s,
                error_details = %s,
                processed_at = NOW(),
                points_paid = true
            WHERE id = %s
        """, (
            status,
            result.get("message"),
            result.get("student_name"),
            result.get("student_email"),
            result.get("school_name"),
            result.get("redirect_url"),
            result.get("error") if not result.get("success") else None,
            verification_id
        ))
        return cursor.rowcount > 0


# ==================== API ROUTES ====================

@sheerid_bp.route('/types', methods=['GET'])
@jwt_required()
def get_types():
    """Get available verification types"""
    sheerid = get_sheerid_service()
    if not sheerid:
        return jsonify({"error": "SheerID service not available"}), 500
    
    types = sheerid.get_verify_types()
    return jsonify({
        "types": [
            {
                "id": key,
                "name": val["name"],
                "cost": val["cost"],
                "icon": val["icon"]
            }
            for key, val in types.items()
        ]
    })


@sheerid_bp.route('/check-link', methods=['POST'])
@jwt_required()
def check_link():
    """Check if a SheerID link is valid"""
    sheerid = get_sheerid_service()
    if not sheerid:
        return jsonify({"error": "SheerID service not available"}), 500
    
    data = request.get_json()
    url = data.get("url", "")
    verify_type = data.get("type", "youtube")
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    if "sheerid.com" not in url:
        return jsonify({"error": "Invalid URL - must be a SheerID URL"}), 400
    
    result = sheerid.check_sheerid_link(url, verify_type)
    return jsonify(result)


@sheerid_bp.route('/verify', methods=['POST'])
@jwt_required()
def submit_verification():
    """Submit a verification request"""
    sheerid = get_sheerid_service()
    if not sheerid:
        return jsonify({"error": "SheerID service not available"}), 500
    
    user_id = get_user_id_from_jwt()
    if not user_id:
        return jsonify({"error": "Invalid user"}), 401
    
    data = request.get_json()
    url = data.get("url", "")
    verify_type = data.get("type", "youtube")
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    if "sheerid.com" not in url:
        return jsonify({"error": "Invalid URL - must be a SheerID URL"}), 400
    
    # Get verification type config
    types = sheerid.get_verify_types()
    type_config = types.get(verify_type)
    if not type_config:
        return jsonify({"error": f"Invalid verification type: {verify_type}"}), 400
    
    points_cost = type_config["cost"]
    
    # Check link validity first
    check_result = sheerid.check_sheerid_link(url, verify_type)
    if not check_result.get("valid"):
        return jsonify({"error": check_result.get("error", "Invalid link")}), 400
    
    # Get user's proxy settings
    settings = get_user_settings(user_id)
    proxy = None
    if settings.get("proxy_enabled") and settings.get("proxy_host"):
        proxy_host = settings["proxy_host"]
        proxy_port = settings.get("proxy_port", 80)
        if settings.get("proxy_username"):
            proxy = f"http://{settings['proxy_username']}:{settings.get('proxy_password', '')}@{proxy_host}:{proxy_port}"
        else:
            proxy = f"http://{proxy_host}:{proxy_port}"
    
    # Extract verification ID
    import re
    vid_match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
    if not vid_match:
        vid_match = re.search(r"/verification/([a-f0-9]+)", url, re.IGNORECASE)
    verify_id = vid_match.group(1) if vid_match else None
    
    # Create verification record
    record = create_verification_record(user_id, verify_type, url, verify_id, points_cost)
    
    # Run verification
    result = sheerid.run_verification(url, verify_type, proxy)
    
    # Update record with result
    update_verification_result(record["id"], result)
    
    if result.get("success"):
        return jsonify({
            "success": True,
            "message": result.get("message"),
            "verification_id": record["id"],
            "student_name": result.get("student_name"),
            "student_email": result.get("student_email"),
            "school_name": result.get("school_name"),
            "redirect_url": result.get("redirect_url"),
            "points_cost": points_cost
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error"),
            "verification_id": record["id"]
        }), 400


@sheerid_bp.route('/verifications', methods=['GET'])
@jwt_required()
def list_verifications():
    """Get user's verification history"""
    user_id = get_user_id_from_jwt()
    if not user_id:
        return jsonify({"error": "Invalid user"}), 401
    
    verifications = get_user_verifications(user_id)
    return jsonify({"verifications": verifications})


@sheerid_bp.route('/verifications/<int:verification_id>', methods=['GET'])
@jwt_required()
def get_verification(verification_id):
    """Get verification details"""
    user_id = get_user_id_from_jwt()
    if not user_id:
        return jsonify({"error": "Invalid user"}), 401
    
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM sheerid_verifications
            WHERE id = %s AND user_id = %s
        """, (verification_id, user_id))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({"error": "Verification not found"}), 404
        
        return jsonify({"verification": dict(row)})


@sheerid_bp.route('/verifications/<int:verification_id>/status', methods=['GET'])
@jwt_required()
def check_verification_status(verification_id):
    """Check real-time verification status from SheerID API"""
    sheerid = get_sheerid_service()
    if not sheerid:
        return jsonify({"error": "SheerID service not available"}), 500
    
    user_id = get_user_id_from_jwt()
    if not user_id:
        return jsonify({"error": "Invalid user"}), 401
    
    # Get verification record
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, verify_id, verify_type, status FROM sheerid_verifications
            WHERE id = %s AND user_id = %s
        """, (verification_id, user_id))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({"error": "Verification not found"}), 404
        
        sheerid_id = row["verify_id"]
        verify_type = row["verify_type"]
    
    if not sheerid_id:
        return jsonify({"error": "No SheerID verification ID"}), 400
    
    # Get user's proxy settings
    settings = get_user_settings(user_id)
    proxy = None
    if settings.get("proxy_enabled") and settings.get("proxy_host"):
        proxy_host = settings["proxy_host"]
        proxy_port = settings.get("proxy_port", 80)
        if settings.get("proxy_username"):
            proxy = f"http://{settings['proxy_username']}:{settings.get('proxy_password', '')}@{proxy_host}:{proxy_port}"
        else:
            proxy = f"http://{proxy_host}:{proxy_port}"
    
    # Check real-time status
    status_result = sheerid.get_verification_status(sheerid_id, proxy)
    
    if not status_result.get("success"):
        return jsonify(status_result), 400
    
    # Get claim URL
    claim_url = sheerid.get_claim_url(verify_type)
    
    # Update database if status changed
    if status_result.get("approved"):
        new_status = "success"
    elif status_result.get("status") in ["pending", "fraud_review", "error", "doc_upload"]:
        new_status = status_result.get("status")
    else:
        new_status = row["status"]
    
    if new_status != row["status"]:
        with get_cursor() as cursor:
            cursor.execute("""
                UPDATE sheerid_verifications
                SET status = %s
                WHERE id = %s
            """, (new_status, verification_id))
    
    return jsonify({
        **status_result,
        "claim_url": claim_url if status_result.get("approved") else None,
        "verify_type": verify_type,
        "verification_id": verification_id
    })


@sheerid_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get user's SheerID settings"""
    user_id = get_user_id_from_jwt()
    if not user_id:
        return jsonify({"error": "Invalid user"}), 401
    
    settings = get_user_settings(user_id)
    # Don't expose password in response
    if settings.get("proxy_password"):
        settings["proxy_password"] = "********"
    
    return jsonify({"settings": settings})


@sheerid_bp.route('/settings', methods=['POST'])
@jwt_required()
def update_settings():
    """Update user's SheerID settings"""
    user_id = get_user_id_from_jwt()
    if not user_id:
        return jsonify({"error": "Invalid user"}), 401
    
    data = request.get_json()
    
    # Get current settings to preserve password if not provided
    current = get_user_settings(user_id)
    
    settings = {
        "proxy_enabled": data.get("proxy_enabled", current.get("proxy_enabled", False)),
        "proxy_host": data.get("proxy_host", current.get("proxy_host")),
        "proxy_port": data.get("proxy_port", current.get("proxy_port")),
        "proxy_username": data.get("proxy_username", current.get("proxy_username")),
        "default_points_cost": data.get("default_points_cost", current.get("default_points_cost", 5))
    }
    
    # Only update password if provided and not placeholder
    if data.get("proxy_password") and data.get("proxy_password") != "********":
        settings["proxy_password"] = data["proxy_password"]
    else:
        settings["proxy_password"] = current.get("proxy_password")
    
    save_user_settings(user_id, settings)
    
    return jsonify({"message": "Settings saved", "settings": settings})


# ==================== IP LOOKUP & PROXY CHECK ====================

@sheerid_bp.route('/ip-lookup', methods=['GET'])
@jwt_required()
def ip_lookup():
    """Get current IP address info (without proxy)"""
    try:
        import httpx
        
        # Get IP info from multiple sources
        ip_info = {}
        
        # Try ipapi.co first
        try:
            resp = httpx.get("https://ipapi.co/json/", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                ip_info = {
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code"),
                    "isp": data.get("org"),
                    "timezone": data.get("timezone"),
                    "source": "ipapi.co"
                }
        except Exception:
            pass
        
        # Fallback to ipinfo.io
        if not ip_info.get("ip"):
            try:
                resp = httpx.get("https://ipinfo.io/json", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    ip_info = {
                        "ip": data.get("ip"),
                        "city": data.get("city"),
                        "region": data.get("region"),
                        "country": data.get("country"),
                        "isp": data.get("org"),
                        "timezone": data.get("timezone"),
                        "source": "ipinfo.io"
                    }
            except Exception:
                pass
        
        # Last fallback to simple IP check
        if not ip_info.get("ip"):
            try:
                resp = httpx.get("https://api.ipify.org?format=json", timeout=10)
                if resp.status_code == 200:
                    ip_info = {
                        "ip": resp.json().get("ip"),
                        "source": "ipify.org"
                    }
            except Exception:
                pass
        
        if ip_info.get("ip"):
            return jsonify({"success": True, **ip_info})
        else:
            return jsonify({"success": False, "error": "Could not get IP info"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@sheerid_bp.route('/proxy-check', methods=['POST'])
@jwt_required()
def proxy_check():
    """Check if proxy is valid and get IP info through proxy"""
    data = request.get_json()
    
    proxy_host = data.get("host")
    proxy_port = data.get("port")
    proxy_username = data.get("username")
    proxy_password = data.get("password")
    
    if not proxy_host or not proxy_port:
        return jsonify({"success": False, "error": "Host and port are required"}), 400
    
    try:
        import httpx
        
        # Build proxy URL
        if proxy_username:
            proxy_url = f"http://{proxy_username}:{proxy_password or ''}@{proxy_host}:{proxy_port}"
        else:
            proxy_url = f"http://{proxy_host}:{proxy_port}"
        
        # Test proxy with IP lookup
        try:
            client = httpx.Client(proxy=proxy_url, timeout=15)
            
            # Get IP through proxy
            resp = client.get("https://ipapi.co/json/")
            
            if resp.status_code == 200:
                data = resp.json()
                return jsonify({
                    "success": True,
                    "valid": True,
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code"),
                    "isp": data.get("org"),
                    "timezone": data.get("timezone"),
                    "message": "Proxy is working!"
                })
            else:
                return jsonify({
                    "success": False,
                    "valid": False,
                    "error": f"Proxy returned status {resp.status_code}"
                })
                
        except httpx.ProxyError as e:
            return jsonify({
                "success": False,
                "valid": False,
                "error": f"Proxy connection failed: {str(e)}"
            })
        except httpx.ConnectTimeout:
            return jsonify({
                "success": False,
                "valid": False,
                "error": "Proxy connection timeout"
            })
        except httpx.ConnectError as e:
            return jsonify({
                "success": False,
                "valid": False,
                "error": f"Cannot connect to proxy: {str(e)}"
            })
        finally:
            try:
                client.close()
            except:
                pass
                
    except Exception as e:
        return jsonify({"success": False, "valid": False, "error": str(e)}), 500

