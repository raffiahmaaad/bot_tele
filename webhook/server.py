"""
Webhook server for receiving Pakasir payment notifications.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import threading

from config import config
from database import (
    get_order_by_order_id,
    update_order_status,
    decrease_stock,
    get_product_by_id,
    get_user_by_telegram_id
)


# Flask app for webhook
app = Flask(__name__)

# Global reference to bot for sending messages
_bot = None
_loop = None


def set_bot_reference(bot, loop):
    """Set the bot reference for sending messages from webhook."""
    global _bot, _loop
    _bot = bot
    _loop = loop


@app.route("/webhook/pakasir", methods=["POST"])
def pakasir_webhook():
    """
    Handle Pakasir payment webhook.
    
    Expected payload:
    {
        "amount": 22000,
        "order_id": "240910HDE7C9",
        "project": "your_project",
        "status": "completed",
        "payment_method": "qris",
        "completed_at": "2024-09-10T08:07:02.819+07:00"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        order_id = data.get("order_id")
        amount = data.get("amount")
        status = data.get("status")
        project = data.get("project")
        
        print(f"📥 Webhook received: order_id={order_id}, status={status}")
        
        # Verify project matches
        if project != config.PAKASIR_PROJECT_SLUG:
            print(f"⚠️ Project mismatch: {project} != {config.PAKASIR_PROJECT_SLUG}")
            return jsonify({"error": "Invalid project"}), 400
        
        # Get order from database
        order = get_order_by_order_id(order_id)
        
        if not order:
            print(f"⚠️ Order not found: {order_id}")
            return jsonify({"error": "Order not found"}), 404
        
        # Verify amount matches
        if order.amount != amount:
            print(f"⚠️ Amount mismatch: {order.amount} != {amount}")
            return jsonify({"error": "Amount mismatch"}), 400
        
        # Check if already processed
        if order.status == "paid":
            print(f"ℹ️ Order already paid: {order_id}")
            return jsonify({"status": "already_processed"}), 200
        
        # Process completed payment
        if status == "completed":
            # Update order status
            update_order_status(order_id, "paid", datetime.now())
            
            # Decrease product stock
            decrease_stock(order.product_id)
            
            print(f"✅ Order {order_id} marked as paid")
            
            # Trigger product delivery
            if _bot and _loop:
                _loop.call_soon_threadsafe(
                    lambda: _schedule_delivery(order)
                )
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


def _schedule_delivery(order):
    """Schedule product delivery in the event loop."""
    import asyncio
    asyncio.create_task(_deliver_product_async(order))


async def _deliver_product_async(order):
    """Deliver product to user after payment."""
    try:
        from services.delivery import deliver_product
        from database import get_product_by_id
        
        product = get_product_by_id(order.product_id)
        
        if not product:
            print(f"❌ Product not found for order {order.order_id}")
            return
        
        # Get user's telegram_id from user_id
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE id = ?", (order.user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            telegram_id = row["telegram_id"]
            await deliver_product(_bot, telegram_id, product, order.order_id)
            print(f"✅ Product delivered for order {order.order_id}")
    except Exception as e:
        print(f"❌ Delivery error: {e}")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


def run_webhook_server(port: int = None):
    """Run the webhook server in a separate thread."""
    port = port or config.WEBHOOK_PORT
    
    def run():
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print(f"🌐 Webhook server started on port {port}")
    return thread
