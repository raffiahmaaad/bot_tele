"""
Webhook server for receiving Pakasir payment notifications.
Note: Currently not used - bot uses polling mode.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import threading


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
        status = data.get("status")
        
        print(f"📥 Webhook received: order_id={order_id}, status={status}")
        
        # Import from database_pg for bot runner context
        from database_pg import get_order_by_order_id, update_order_status
        
        # Get order from database
        order = get_order_by_order_id(order_id)
        
        if not order:
            print(f"⚠️ Order not found: {order_id}")
            return jsonify({"error": "Order not found"}), 404
        
        # Check if already processed
        if order.get('status') == "paid":
            print(f"ℹ️ Order already paid: {order_id}")
            return jsonify({"status": "already_processed"}), 200
        
        # Process completed payment
        if status == "completed":
            # Update order status
            update_order_status(order_id, "paid", datetime.now())
            print(f"✅ Order {order_id} marked as paid")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


def run_webhook_server(port: int = 5001):
    """Run the webhook server in a separate thread."""
    def run():
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print(f"🌐 Webhook server started on port {port}")
    return thread
