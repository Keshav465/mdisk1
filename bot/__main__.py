# bot/__main__.py

import os
from flask import Flask, request, jsonify, redirect, render_template_string
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

# === YEH POORA ENDPOINT BADAL GAYA HAI (FINAL GPLINKS LOOP FIX) ===
@app.route('/get/<payload>')
def handle_get_redirect(payload):
    """
    Yeh GPlinks ke loop ko todne ke liye final solution hai.
    Yeh seedha redirect karne ke bajaye ek HTML page bhejega jo JavaScript se redirect karega.
    """
    if bot_instance and bot_instance.username:
        bot_username = bot_instance.username.replace("@", "")
        telegram_url = f"https://telegram.dog/{bot_username}?start={payload}"

        # HTML template jo user ke browser mein redirect karega
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Please Wait...</title>
            <meta http-equiv="refresh" content="1; url={url}" />
            <script type="text/javascript">
                setTimeout(function() {{
                    window.location.href = "{url}";
                }}, 500);
            </script>
            <style>
                body {{ font-family: sans-serif; background-color: #121212; color: #ffffff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .container {{ text-align: center; }}
                .loader {{ border: 4px solid #f3f3f3; border-radius: 50%; border-top: 4px solid #3498db; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 0 auto 20px; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="loader"></div>
                <h2>Redirecting you to Telegram...</h2>
                <p>If you are not redirected automatically, <a href="{url}">click here</a>.</p>
            </div>
        </body>
        </html>
        """
        return render_template_string(html_template, url=telegram_url)
    else:
        return "Bot is initializing, please try again in a moment.", 503
# =================================================================


# === API ENDPOINT FOR IPHONE SHORTCUT ===
@app.route('/api/shortcut', methods=['POST'])
def handle_shortcut():
    provided_secret = request.headers.get('X-Shortcut-Secret')
    if provided_secret != Config.AUTOMATION_SECRET:
        return jsonify({"error": "Unauthorized"}), 403

    sms_text = request.get_data(as_text=True)
    if not sms_text:
        return jsonify({"error": "No SMS text provided"}), 400

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
    bot_instance = bot
    await bot.start()
    
    asyncio.create_task(remove_expired_scheduler())
    
    await asyncio.sleep(5)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
