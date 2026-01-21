"""
Bot management routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests as http_requests

from database import (
    create_bot, get_bots_by_user, get_bot_by_id, 
    update_bot, delete_bot, get_bot_stats
)

bots_bp = Blueprint('bots', __name__, url_prefix='/api/bots')


def verify_bot_token(token: str) -> dict | None:
    """Verify Telegram bot token and get bot info."""
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = http_requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                return data.get('result')
        return None
    except Exception as e:
        print(f"Bot verification error: {e}")
        return None


@bots_bp.route('', methods=['GET'])
@jwt_required()
def list_bots():
    """List all bots for current user."""
    user_id = int(get_jwt_identity())
    bots = get_bots_by_user(user_id)
    
    return jsonify({
        'bots': [{
            'id': bot['id'],
            'bot_username': bot['bot_username'],
            'bot_name': bot['bot_name'],
            'bot_type': bot.get('bot_type', 'store'),
            'is_active': bot['is_active'],
            'products_count': bot['products_count'],
            'users_count': bot['users_count'],
            'transactions_count': bot['transactions_count'],
            'created_at': bot['created_at'].isoformat() if bot['created_at'] else None,
        } for bot in bots]
    })


@bots_bp.route('', methods=['POST'])
@jwt_required()
def create_new_bot():
    """Create a new bot."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    telegram_token = data.get('telegram_token', '').strip()
    bot_type = data.get('bot_type', 'store')
    pakasir_slug = data.get('pakasir_slug', '').strip() or None
    pakasir_api_key = data.get('pakasir_api_key', '').strip() or None
    
    if not telegram_token:
        return jsonify({'error': 'Bot token wajib diisi'}), 400
    
    if bot_type not in ['store', 'sheerid', 'custom']:
        return jsonify({'error': 'Tipe bot tidak valid'}), 400
    
    # Verify token with Telegram
    bot_info = verify_bot_token(telegram_token)
    
    if not bot_info:
        return jsonify({'error': 'Token bot tidak valid'}), 400
    
    bot_username = f"@{bot_info.get('username', '')}"
    bot_name = bot_info.get('first_name', 'Unnamed Bot')
    
    try:
        bot = create_bot(
            user_id, 
            telegram_token, 
            bot_username, 
            bot_name,
            bot_type=bot_type,
            pakasir_slug=pakasir_slug,
            pakasir_api_key=pakasir_api_key
        )
        
        return jsonify({
            'message': 'Bot berhasil ditambahkan',
            'bot': {
                'id': bot['id'],
                'bot_username': bot['bot_username'],
                'bot_name': bot['bot_name'],
                'bot_type': bot['bot_type'],
                'is_active': bot['is_active'],
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bots_bp.route('/<int:bot_id>', methods=['GET'])
@jwt_required()
def get_single_bot(bot_id: int):
    """Get bot details with stats."""
    user_id = int(get_jwt_identity())
    
    bot = get_bot_by_id(bot_id, user_id)
    if not bot:
        return jsonify({'error': 'Bot tidak ditemukan'}), 404
    
    stats = get_bot_stats(bot_id)
    
    return jsonify({
        'bot': {
            'id': bot['id'],
            'bot_username': bot['bot_username'],
            'bot_name': bot['bot_name'],
            'bot_type': bot.get('bot_type', 'store'),
            'pakasir_slug': bot.get('pakasir_slug'),
            'pakasir_api_key': '••••••••' if bot.get('pakasir_api_key') else None,
            'is_active': bot['is_active'],
            'created_at': bot['created_at'].isoformat() if bot['created_at'] else None,
        },
        'stats': stats
    })


@bots_bp.route('/<int:bot_id>', methods=['PUT'])
@jwt_required()
def update_single_bot(bot_id: int):
    """Update bot settings."""
    user_id = int(get_jwt_identity())
    
    bot = get_bot_by_id(bot_id, user_id)
    if not bot:
        return jsonify({'error': 'Bot tidak ditemukan'}), 404
    
    data = request.get_json()
    
    updated_bot = update_bot(
        bot_id,
        bot_name=data.get('bot_name'),
        bot_type=data.get('bot_type'),
        pakasir_slug=data.get('pakasir_slug'),
        pakasir_api_key=data.get('pakasir_api_key'),
        is_active=data.get('is_active'),
    )
    
    return jsonify({
        'message': 'Bot berhasil diupdate',
        'bot': {
            'id': updated_bot['id'],
            'bot_username': updated_bot['bot_username'],
            'bot_name': updated_bot['bot_name'],
            'bot_type': updated_bot.get('bot_type', 'store'),
            'is_active': updated_bot['is_active'],
        }
    })


@bots_bp.route('/<int:bot_id>', methods=['DELETE'])
@jwt_required()
def delete_single_bot(bot_id: int):
    """Delete a bot."""
    user_id = int(get_jwt_identity())
    
    bot = get_bot_by_id(bot_id, user_id)
    if not bot:
        return jsonify({'error': 'Bot tidak ditemukan'}), 404
    
    delete_bot(bot_id)
    
    return jsonify({'message': 'Bot berhasil dihapus'})
