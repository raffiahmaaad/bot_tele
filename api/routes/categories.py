"""
Category management routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_bot_by_id

categories_bp = Blueprint('categories', __name__, url_prefix='/api')


def get_categories_by_bot(bot_id: int):
    """Get all categories for a bot."""
    from database import get_cursor
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) FROM products WHERE category_id = c.id) as products_count
            FROM categories c
            WHERE c.bot_id = %s
            ORDER BY c.sort_order, c.name
        """, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]


def create_category(bot_id: int, name: str, description: str = None):
    """Create a new category."""
    from database import get_cursor
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO categories (bot_id, name, description)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (bot_id, name, description))
        return dict(cursor.fetchone())


def update_category(category_id: int, **kwargs):
    """Update a category."""
    from database import get_cursor
    allowed = ['name', 'description', 'is_active', 'sort_order']
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    
    if not updates:
        return None
    
    with get_cursor() as cursor:
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [category_id]
        cursor.execute(f"""
            UPDATE categories SET {set_clause}
            WHERE id = %s RETURNING *
        """, values)
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_category(category_id: int):
    """Delete a category."""
    from database import get_cursor
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        return cursor.rowcount > 0


@categories_bp.route('/bots/<int:bot_id>/categories', methods=['GET'])
@jwt_required()
def list_categories(bot_id: int):
    """List all categories for a bot."""
    user_id = int(get_jwt_identity())
    
    # Verify bot ownership
    bot = get_bot_by_id(bot_id, user_id)
    if not bot:
        return jsonify({'error': 'Bot tidak ditemukan'}), 404
    
    categories = get_categories_by_bot(bot_id)
    
    return jsonify({
        'categories': [{
            'id': c['id'],
            'name': c['name'],
            'description': c['description'],
            'is_active': c['is_active'],
            'sort_order': c['sort_order'],
            'products_count': c['products_count'],
            'created_at': c['created_at'].isoformat() if c['created_at'] else None,
        } for c in categories]
    })


@categories_bp.route('/bots/<int:bot_id>/categories', methods=['POST'])
@jwt_required()
def create_new_category(bot_id: int):
    """Create a new category."""
    user_id = int(get_jwt_identity())
    
    # Verify bot ownership
    bot = get_bot_by_id(bot_id, user_id)
    if not bot:
        return jsonify({'error': 'Bot tidak ditemukan'}), 404
    
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'error': 'Nama kategori wajib diisi'}), 400
    
    try:
        category = create_category(bot_id, name, description)
        return jsonify({
            'message': 'Kategori berhasil dibuat',
            'category': {
                'id': category['id'],
                'name': category['name'],
                'description': category['description'],
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@categories_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category_route(category_id: int):
    """Update a category."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    try:
        category = update_category(
            category_id,
            name=data.get('name'),
            description=data.get('description'),
            is_active=data.get('is_active'),
            sort_order=data.get('sort_order')
        )
        if not category:
            return jsonify({'error': 'Kategori tidak ditemukan'}), 404
            
        return jsonify({
            'message': 'Kategori berhasil diupdate',
            'category': category
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@categories_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category_route(category_id: int):
    """Delete a category."""
    user_id = int(get_jwt_identity())
    
    try:
        if delete_category(category_id):
            return jsonify({'message': 'Kategori berhasil dihapus'})
        return jsonify({'error': 'Kategori tidak ditemukan'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
