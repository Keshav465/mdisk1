import time
import math
import logging
import asyncio
from aiohttp import web
from bot.config import Config
from bot import Bot
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
    
    # We can fetch the message to get the file name
    # But for now, let's just render a simple player
    
    stream_url = f"/stream/{chat_id}/{message_id}"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mdisk Streamer</title>
        <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
        <style>
            body {{ background: #0f0f0f; color: white; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            .container {{ width: 90%; max-width: 1000px; }}
            h1 {{ font-size: 1.5rem; margin-bottom: 20px; }}
            .download-btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #0088cc; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Streaming Video</h1>
            <video id="player" playsinline controls>
                <source src="{stream_url}" type="video/mp4" />
            </video>
            <br>
            <a href="{stream_url}" class="download-btn">Fast Download</a>
        </div>
        <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
        <script>
            const player = new Plyr('#player');
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
