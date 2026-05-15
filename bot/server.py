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

    stream_url = f"/stream/{chat_id}/{message_id}"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{file_name} - Mdisk Streamer</title>
        <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #00d2ff;
                --secondary: #3a7bd5;
                --bg: #050505;
                --card-bg: #121212;
                --text: #ffffff;
                --accent: #ff007a;
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
                min-height: 100vh;
                overflow-x: hidden;
            }}
            
            .glass-header {{
                width: 100%;
                padding: 20px 0;
                background: rgba(18, 18, 18, 0.8);
                backdrop-filter: blur(10px);
                position: sticky;
                top: 0;
                z-index: 100;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                text-align: center;
            }}
            
            .logo {{
                font-size: 1.8rem;
                font-weight: 800;
                background: linear-gradient(45deg, var(--primary), var(--secondary));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: 1px;
            }}
            
            .container {{
                width: 95%;
                max-width: 1100px;
                padding: 40px 0;
                animation: fadeIn 0.8s ease-out;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .video-section {{
                background: var(--card-bg);
                border-radius: 24px;
                overflow: hidden;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 210, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.05);
                margin-bottom: 30px;
            }}
            
            .plyr--full-ui {{ --plyr-color-main: var(--primary); }}
            
            .info-card {{
                background: var(--card-bg);
                border-radius: 24px;
                padding: 30px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                margin-bottom: 30px;
            }}
            
            .meta-info {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                flex-wrap: wrap;
                gap: 15px;
            }}
            
            .title-box h1 {{
                margin: 0;
                font-size: 1.6rem;
                font-weight: 700;
                color: var(--primary);
            }}
            
            .badge {{
                background: rgba(0, 210, 255, 0.1);
                color: var(--primary);
                padding: 6px 16px;
                border-radius: 50px;
                font-size: 0.9rem;
                font-weight: 600;
                border: 1px solid rgba(0, 210, 255, 0.2);
            }}
            
            .action-buttons {{
                display: flex;
                gap: 15px;
                margin-top: 10px;
            }}
            
            .btn {{
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 14px 25px;
                border-radius: 12px;
                font-weight: 700;
                text-decoration: none;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                cursor: pointer;
                font-size: 1rem;
            }}
            
            .btn-primary {{
                background: linear-gradient(45deg, var(--primary), var(--secondary));
                color: white;
                box-shadow: 0 10px 20px rgba(0, 210, 255, 0.2);
            }}
            
            .btn-primary:hover {{
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(0, 210, 255, 0.4);
            }}
            
            .btn-secondary {{
                background: rgba(255, 255, 255, 0.05);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .btn-secondary:hover {{
                background: rgba(255, 255, 255, 0.1);
                transform: translateY(-3px);
            }}
            
            .description-section {{
                margin-top: 40px;
                line-height: 1.6;
                color: #bbb;
            }}
            
            .description-section h3 {{
                color: white;
                margin-bottom: 15px;
                font-size: 1.2rem;
            }}
            
            .disclaimer {{
                margin-top: 50px;
                padding: 20px;
                background: rgba(255, 0, 122, 0.05);
                border-left: 4px solid var(--accent);
                border-radius: 8px;
                font-size: 0.9rem;
                color: #aaa;
            }}
            
            footer {{
                margin-top: 50px;
                padding-bottom: 40px;
                text-align: center;
                color: #666;
                font-size: 0.9rem;
            }}
            
            @media (max-width: 768px) {{
                .container {{ padding: 20px 0; }}
                .meta-info {{ flex-direction: column; align-items: flex-start; }}
                .action-buttons {{ width: 100%; flex-direction: column; }}
                .title-box h1 {{ font-size: 1.3rem; }}
            }}
        </style>
    </head>
    <body>
        <header class="glass-header">
            <div class="logo">MDISK PREMIUM</div>
        </header>
        
        <div class="container">
            <div class="video-section">
                <video id="player" playsinline controls crossorigin>
                    <source src="{stream_url}" type="video/mp4" />
                </video>
            </div>
            
            <div class="info-card">
                <div class="meta-info">
                    <div class="title-box">
                        <h1>{file_name}</h1>
                    </div>
                    <div class="badge">{file_size}</div>
                </div>
                
                <div class="action-buttons">
                    <a href="{stream_url}" class="btn btn-primary">
                        <span>⚡ FAST DOWNLOAD</span>
                    </a>
                    <a href="https://t.me/{bot.username.replace('@', '')}" class="btn btn-secondary">
                        <span>💬 JOIN TELEGRAM</span>
                    </a>
                </div>
                
                <div class="description-section">
                    <h3>About this file</h3>
                    <p>Experience high-speed streaming with our premium servers. This file is optimized for seamless playback on all devices. If you face any buffering issues, try using the "Fast Download" option for offline viewing.</p>
                </div>
                
                <div class="disclaimer">
                    <strong>Disclaimer:</strong> This service is for demonstration purposes. We do not host any files on our servers. All files are streamed directly from Telegram's encrypted cloud. Please ensure you have the rights to view the content.
                </div>
            </div>
            
            <footer>
                &copy; 2026 Mdisk Streamer Pro. All Rights Reserved.
            </footer>
        </div>

        <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                const player = new Plyr('#player', {{
                    tooltips: {{ controls: true, seek: true }},
                    quality: {{ default: 576, options: [4320, 2880, 2160, 1440, 1080, 720, 576, 480, 360, 240] }}
                }});
                
                // Expose player so it can be used from the console
                window.player = player;
            }});
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

@routes.get("/stream/{chat_id}/{message_id}")
async def stream_handler(request):
    chat_id = int(request.match_info['chat_id'])
    message_id = int(request.match_info['message_id'])
    
    bot = request.app['bot']
    
    try:
        message = await bot.get_messages(chat_id, message_id)
        if not message or not (message.video or message.document):
            return web.Response(text="File not found", status=404)
        
        file = message.video or message.document
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
            if ranges[1]:
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
        logger.error(f"Stream error: {e}")
        return web.Response(text=str(e), status=500)

async def start_server(bot):
    app = web.Application()
    app['bot'] = bot
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(Config.PORT))
    await site.start()
    logger.info(f"Web server started on port {Config.PORT}")
