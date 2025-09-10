# bot/__main__.py (ORIGINAL VERSION)

import os
from flask import Flask, request, jsonify
import threading
import asyncio

# === START: NAYE IMPORTS ===
from bot import Bot
from bot.config import Config # Config ko import karna zaroori hai
from bot.plugins.scheduler import remove_expired_scheduler
from bot.plugins.subscription import process_payment_sms # Hamara naya function
# === END: NAYE IMPORTS ===

app = Flask(__name__)
bot_instance = None  # We will set this in the main async function

@app.route('/')
def home():
    return "Bot is running fine."

# === NAYA API ENDPOINT FOR IPHONE SHORTCUT ===
@app.route('/api/shortcut', methods=['POST'])
def handle_shortcut():
    # Header se secret key check karo
    provided_secret = request.headers.get('X-Shortcut-Secret')
    if provided_secret != Config.AUTOMATION_SECRET:
        return jsonify({"error": "Unauthorized"}), 403

    # SMS text ko request se nikalo
    sms_text = request.get_data(as_text=True)
    if not sms_text:
        return jsonify({"error": "No SMS text provided"}), 400

    # SMS ko process karne ke liye hamare async function ko call karo
    # asyncio.run() is a simple way to run an async function from a sync context
    if bot_instance:
        asyncio.run_coroutine_threadsafe(process_payment_sms(bot_instance, sms_text), bot_instance.loop)
    
    return jsonify({"status": "received"}), 200
# === END OF NEW API ENDPOINT ===


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Start Flask in a background thread
threading.Thread(target=run_flask, daemon=True).start()

# === ASYNC BOT LOGIC ===
async def main():
    global bot_instance
    bot = Bot()
    bot_instance = bot  # Set the global instance for Flask to use
    await bot.start()
    
    asyncio.create_task(remove_expired_scheduler())
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
