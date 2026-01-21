"""
Bot Commands API routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database import get_cursor, get_bot_by_id

commands_bp = Blueprint('commands', __name__)


@commands_bp.route('/bots/<int:bot_id>/commands', methods=['GET'])
@jwt_required()
def get_bot_commands(bot_id: int):
    """Get all commands for a bot."""
    user_id = int(get_jwt_identity())
    
    # Verify bot ownership
    bot = get_bot_by_id(bot_id, user_id)
    if not bot:
        return jsonify({'error': 'Bot tidak ditemukan'}), 404
    
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, bot_id, command_name, response_text, is_enabled, created_at
            FROM bot_commands
            WHERE bot_id = %s
            ORDER BY command_name
        """, (bot_id,))
        commands = cursor.fetchall()
    
    return jsonify({
        'commands': [
            {
                'id': cmd['id'],
                'bot_id': cmd['bot_id'],
                'command_name': cmd['command_name'],
                'response_text': cmd['response_text'],
                'is_enabled': cmd['is_enabled'],
                'created_at': cmd['created_at'].isoformat() if cmd['created_at'] else None
            }
            for cmd in commands
        ]
    })


@commands_bp.route('/bots/<int:bot_id>/commands', methods=['POST'])
@jwt_required()
def save_bot_command(bot_id: int):
    """Create or update a bot command."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Verify bot ownership
    bot = get_bot_by_id(bot_id, user_id)
    if not bot:
        return jsonify({'error': 'Bot tidak ditemukan'}), 404
    
    command_name = data.get('command_name', '').strip()
    response_text = data.get('response_text', '').strip()
    is_enabled = data.get('is_enabled', True)
    
    if not command_name:
        return jsonify({'error': 'Command name wajib diisi'}), 400
    
    with get_cursor() as cursor:
        # Check if command exists
        cursor.execute("""
            SELECT id FROM bot_commands
            WHERE bot_id = %s AND command_name = %s
        """, (bot_id, command_name))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute("""
                UPDATE bot_commands
                SET response_text = %s, is_enabled = %s
                WHERE id = %s
                RETURNING id, bot_id, command_name, response_text, is_enabled, created_at
            """, (response_text, is_enabled, existing['id']))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO bot_commands (bot_id, command_name, response_text, is_enabled)
                VALUES (%s, %s, %s, %s)
                RETURNING id, bot_id, command_name, response_text, is_enabled, created_at
            """, (bot_id, command_name, response_text, is_enabled))
        
        command = cursor.fetchone()
    
    return jsonify({
        'message': 'Command berhasil disimpan',
        'command': {
            'id': command['id'],
            'bot_id': command['bot_id'],
            'command_name': command['command_name'],
            'response_text': command['response_text'],
            'is_enabled': command['is_enabled'],
            'created_at': command['created_at'].isoformat() if command['created_at'] else None
        }
    })


@commands_bp.route('/bots/<int:bot_id>/users', methods=['GET'])
@jwt_required()
def get_bot_users(bot_id: int):
    """Get all users for a bot."""
    user_id = int(get_jwt_identity())
    
    # Verify bot ownership
    bot = get_bot_by_id(bot_id, user_id)
    if not bot:
        return jsonify({'error': 'Bot tidak ditemukan'}), 404
    
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, telegram_id, username, first_name, last_name, is_blocked, created_at
            FROM bot_users
            WHERE bot_id = %s
            ORDER BY created_at DESC
        """, (bot_id,))
        users = cursor.fetchall()
    
    return jsonify({
        'users': [
            {
                'id': u['id'],
                'telegram_id': str(u['telegram_id']),
                'username': u['username'],
                'first_name': u['first_name'],
                'last_name': u['last_name'],
                'is_blocked': u['is_blocked'],
                'created_at': u['created_at'].isoformat() if u['created_at'] else None
            }
            for u in users
        ]
    })
