import time
import math
import logging
import asyncio
from aiohttp import web
from bot.config import Config
from pyrogram import types, enums

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

routes = web.RouteTableDef()

@routes.get("/")
async def hello(request):
    return web.Response(text="Bot is running fine with Streaming Support.")

@routes.get("/watch/{chat_id}/{message_id}")
async def watch_page(request):
    chat_id = request.match_info['chat_id']
    message_id = request.match_info['message_id']
    
    bot = request.app['bot']
    file_name = "Streaming Video"
    file_size = "N/A"
    
    try:
        message = await bot.get_messages(int(chat_id), int(message_id))
        if message:
            file = message.video or message.document or message.audio
            if file:
                file_name = getattr(file, 'file_name', 'Video')
                file_size = f"{round(file.file_size / (1024 * 1024), 2)} MB"
                if file.file_size >= 1024 * 1024 * 1024:
                    file_size = f"{round(file.file_size / (1024 * 1024 * 1024), 2)} GB"
    except Exception:
        pass

    stream_url = f"{Config.BASE_URL}/stream/{chat_id}/{message_id}"
    intent_url = f"intent://{stream_url.replace('https://', '')}#Intent;package=com.nextplayer.pro;type=video/*;S.title={file_name};end"
    play_store_url = "https://play.google.com/store/apps/details?id=com.nextplayer.pro"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Redirecting to Player - Mdisk</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #00d2ff;
                --secondary: #3a7bd5;
                --bg: #050505;
                --card-bg: #121212;
                --text: #ffffff;
                --accent: #ffb400;
            }}
            
            body {{
                background: var(--bg);
                color: var(--text);
                font-family: 'Outfit', sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                text-align: center;
            }}
            
            .container {{
                width: 90%;
                max-width: 500px;
                padding: 40px;
                background: var(--card-bg);
                border-radius: 30px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.05);
                animation: fadeIn 0.5s ease-out;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: scale(0.9); }}
                to {{ opacity: 1; transform: scale(1); }}
            }}
            
            .timer-circle {{
                width: 100px;
                height: 100px;
                border-radius: 50%;
                border: 5px solid var(--primary);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2.5rem;
                font-weight: 800;
                margin: 0 auto 30px;
                color: var(--primary);
                box-shadow: 0 0 20px rgba(0, 210, 255, 0.2);
            }}
            
            h1 {{
                font-size: 1.8rem;
                margin-bottom: 15px;
                background: linear-gradient(45deg, var(--primary), var(--secondary));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            
            .instruction {{
                font-size: 1.1rem;
                color: #bbb;
                line-height: 1.6;
                margin-bottom: 30px;
            }}
            
            .hindi-text {{
                display: block;
                color: var(--accent);
                font-weight: 600;
                margin-top: 10px;
            }}
            
            .btn {{
                display: inline-block;
                width: 100%;
                padding: 16px;
                border-radius: 15px;
                font-weight: 700;
                text-decoration: none;
                transition: all 0.3s ease;
                margin-bottom: 15px;
                font-size: 1rem;
            }}
            
            .btn-primary {{
                background: linear-gradient(45deg, var(--primary), var(--secondary));
                color: white;
            }}
            
            .btn-secondary {{
                background: rgba(255, 255, 255, 0.05);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .file-info {{
                background: rgba(0, 0, 0, 0.3);
                padding: 15px;
                border-radius: 12px;
                font-size: 0.9rem;
                color: #888;
                margin-bottom: 25px;
                border: 1px dashed rgba(255, 255, 255, 0.1);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="timer-circle" id="timer">3</div>
            <h1>Preparing Stream</h1>
            <div class="file-info">
                <strong>{file_name}</strong><br>
                Size: {file_size}
            </div>
            <div class="instruction">
                For the best experience, stream this video in <b>mpvEx Player</b>.
                <span class="hindi-text">इस ऐप को डाउनलोड करके इसमें स्ट्रीम कर सकते हो।</span>
            </div>
            
            <a href="{intent_url}" class="btn btn-primary" id="streamBtn">🚀 OPEN IN MPVEX PLAYER</a>
            <a href="{play_store_url}" class="btn btn-secondary">📥 DOWNLOAD FROM PLAY STORE</a>
        </div>

        <script>
            let timeLeft = 3;
            const timerElement = document.getElementById('timer');
            const streamBtn = document.getElementById('streamBtn');
            const intentUrl = "{intent_url}";
            const playStoreUrl = "{play_store_url}";

            const countdown = setInterval(() => {{
                timeLeft--;
                timerElement.innerText = timeLeft;
                if (timeLeft <= 0) {{
                    clearInterval(countdown);
                    timerElement.innerText = "✓";
                    // Attempt to open the app
                    window.location.href = intentUrl;
                    
                    // Fallback to Play Store if the app doesn't open after 2 seconds
                    setTimeout(() => {{
                        // Check if the user is still on this page
                        if (!document.hidden) {{
                            window.location.href = playStoreUrl;
                        }}
                    }}, 2500);
                }}
            }}, 1000);
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

@routes.get("/stream/{chat_id}/{message_id}")
async def stream_handler(request):
    try:
        chat_id = int(request.match_info['chat_id'])
        message_id = int(request.match_info['message_id'])
    except ValueError:
        return web.Response(text="Invalid IDs provided", status=400)
    
    bot = request.app['bot']
    
    try:
        # Try fetching from Bot first
        message = await bot.get_messages(chat_id, message_id)
        if not message or not (message.video or message.document or message.audio):
            # If bot can't see it, try USER bot
            if bot.USER:
                message = await bot.USER.get_messages(chat_id, message_id)
            
        if not message or not (message.video or message.document or message.audio):
            logger.warning(f"File not found for {chat_id}/{message_id}")
            return web.Response(text="File not found or access denied.", status=404)
        
        file = message.video or message.document or message.audio
        file_size = file.file_size
        file_name = getattr(file, 'file_name', 'video.mp4')
        mime_type = getattr(file, 'mime_type', 'video/mp4')
        
        range_header = request.headers.get('Range')
        start = 0
        end = file_size - 1
        
        if range_header:
            # Handle Range request for seeking
            ranges = range_header.replace('bytes=', '').split('-')
            start = int(ranges[0])
            if len(ranges) > 1 and ranges[1]:
                end = int(ranges[1])
        
        content_length = end - start + 1
        
        response = web.StreamResponse(
            status=206 if range_header else 200,
            reason='Partial Content' if range_header else 'OK',
            headers={
                'Content-Type': mime_type,
                'Content-Length': str(content_length),
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Disposition': f'attachment; filename="{file_name}"'
            }
        )
        
        await response.prepare(request)
        
        # Generator for file chunks from Telegram
        async for chunk in bot.yield_file(file, start, end):
            await response.write(chunk)
            
        return response
        
    except Exception as e:
        logger.error(f"Stream error for {chat_id}/{message_id}: {e}")
        return web.Response(text=f"Server Error: {str(e)}", status=500)

async def start_server(bot):
    app = web.Application()
    app['bot'] = bot
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(Config.PORT))
    await site.start()
    logger.info(f"Web server started on port {Config.PORT}")
