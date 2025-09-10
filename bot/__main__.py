# bot/__main__.py

import os
from flask import Flask, request, jsonify, redirect
import threading
import asyncio

# === START: NAYE IMPORTS ===
from bot import Bot
from bot.config import Config
from bot.plugins.scheduler import remove_expired_scheduler
from bot.plugins.subscription import process_payment_sms
# === END: NAYE IMPORTS ===

app = Flask(__name__)
bot_instance = None  # We will set this in the main async function

@app.route('/')
def home():
    return "Bot is running fine."

# === YEH NAYA ENDPOINT ADD KIYA GAYA HAI (GPLINKS LOOP FIX) ===
@app.route('/get/<payload>')
def handle_get_redirect(payload):
    """
    Yeh GPlinks ke loop ko todne ke liye hai.
    Yeh seedha telegram deep link par redirect karega.
    """
    if bot_instance and bot_instance.username:
        # bot_instance.username @ ke saath aata hai, isliye @ hata dein
        bot_username = bot_instance.username.replace("@", "")
        telegram_url = f"https://telegram.dog/{bot_username}?start={payload}"
        return redirect(telegram_url, code=302)
    else:
        # Agar bot abhi tak start nahi hua hai
        return "Bot is initializing, please try again in a moment.", 503
# === END OF GPLINKS LOOP FIX ===


# === API ENDPOINT FOR IPHONE SHORTCUT ===
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
    if bot_instance:
        asyncio.run_coroutine_threadsafe(process_payment_sms(bot_instance, sms_text), bot_instance.loop)
    
    return jsonify({"status": "received"}), 200
# === END OF API ENDPOINT ===


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
    
    # Bot start hone ke baad 5 second wait karein taaki username load ho jaye
    await asyncio.sleep(5)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
