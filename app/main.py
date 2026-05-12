"""
Main application entry point.
Flask server with Telegram webhook for Cloud Run deployment.
"""
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application
from app.config import TELEGRAM_TOKEN, PORT
from app.bot_handler import register_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Flask app
flask_app = Flask(__name__)

# Telegram application (initialized lazily)
_telegram_app = None


def get_telegram_app() -> Application:
    """Get or create the Telegram application."""
    global _telegram_app
    if _telegram_app is None:
        _telegram_app = (
            Application.builder()
            .token(TELEGRAM_TOKEN)
            .build()
        )
        register_handlers(_telegram_app)
    return _telegram_app


@flask_app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Cloud Run."""
    return jsonify({"status": "healthy", "service": "roger-bot"}), 200


@flask_app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming Telegram webhook updates."""
    try:
        data = request.get_json(force=True)
        logger.info(f"Received webhook update: {data.get('update_id', 'N/A')}")

        app = get_telegram_app()
        update = Update.de_json(data, app.bot)

        # Process update asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(app.initialize())
            loop.run_until_complete(app.process_update(update))
        finally:
            loop.run_until_complete(app.shutdown())
            loop.close()

        return jsonify({"ok": True}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500


@flask_app.route("/set-webhook", methods=["GET"])
def set_webhook():
    """Utility endpoint to set the Telegram webhook URL."""
    webhook_url = request.args.get("url")
    if not webhook_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        result = loop.run_until_complete(
            bot.set_webhook(url=f"{webhook_url}/webhook")
        )
        return jsonify({"ok": result, "webhook_url": f"{webhook_url}/webhook"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()


@flask_app.route("/", methods=["GET"])
def index():
    """Root endpoint."""
    return jsonify({
        "service": "Roger - IDEAM Enterprise Architecture Bot",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook (POST)",
            "set_webhook": "/set-webhook?url=<base_url>",
        },
    }), 200


def main():
    """Run the Flask application."""
    logger.info(f"Starting Roger bot server on port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    main()
