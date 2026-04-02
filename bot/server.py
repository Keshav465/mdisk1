from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bot.config import Config
from bot import Bot
import os
import math
import mimetypes
from pyrogram import Client
import logging

logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="bot/templates")

# I'll need to create the bot/templates directory
os.makedirs("bot/templates", exist_ok=True)

class MediaStreamer:
    def __init__(self, client: Client):
        self.client = client

    async def get_stream(self, chat_id: int, message_id: int, request: Request):
        try:
            message = await self.client.get_messages(chat_id, message_id)
            if not message or not (message.video or message.document):
                raise HTTPException(status_code=404, detail="File not found")

            file = message.video or message.document
            file_size = file.file_size
            mime_type = file.mime_type or mimetypes.guess_type(file.file_name)[0] or "application/octet-stream"

            range_header = request.headers.get("Range")
            start = 0
            end = file_size - 1

            if range_header:
                # Basic range header parsing: "bytes=0-100"
                parts = range_header.replace("bytes=", "").split("-")
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

            content_length = end - start + 1

            async def generate():
                async for chunk in self.client.stream_media(message, offset=start, limit=content_length):
                    yield chunk

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": mime_type,
                "Content-Disposition": f'attachment; filename="{file.file_name}"' if "download" in request.query_params else "inline"
            }

            return StreamingResponse(generate(), status_code=206, headers=headers)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

streamer = None

def set_client(client: Client):
    global streamer
    streamer = MediaStreamer(client)

@app.get("/", response_class=HTMLResponse)
async def home():
    return "<h3>Bot is running fine.</h3><p>Dashboard is coming soon.</p>"

@app.get("/watch/{slug}", response_class=HTMLResponse)
async def watch_page(request: Request, slug: str):
    try:
        file_id_str, chat_id_str = slug.split("_")
        file_id = int(file_id_str)
        chat_id = int(chat_id_str)
        
        # Get metadata for the page
        message = await streamer.client.get_messages(chat_id, file_id)
        file = message.video or message.document
        title = file.file_name
        size = f"{round(file.file_size / (1024 * 1024), 1)} MB"
        
        stream_url = f"{Config.URL}/stream/{slug}"
        download_url = f"{stream_url}?download=1"
        
        # External Player Links
        vlc_url = f"vlc://{stream_url.replace('http://', '').replace('https://', '')}"
        mx_url = f"intent:{stream_url}#Intent;package=com.mxtech.videoplayer.ad;S.title={title};end"
        
        return templates.TemplateResponse("watch.html", {
            "request": request,
            "title": title,
            "size": size,
            "stream_url": stream_url,
            "download_url": download_url,
            "vlc_url": vlc_url,
            "mx_url": mx_url
        })
    except Exception as e:
        return f"Error: {e}"

@app.get("/stream/{slug}")
async def stream_file(request: Request, slug: str):
    file_id_str, chat_id_str = slug.split("_")
    return await streamer.get_stream(int(chat_id_str), int(file_id_str), request)

# API for Admin Dashboard
@app.get("/api/stats")
async def get_stats(request: Request):
    # Check simple auth
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {Config.ADMIN_PASSWORD}":
         raise HTTPException(status_code=401)
    
    from bot.database import user_db, group_db
    users_count = await user_db.total_users_count()
    groups_count = await group_db.total_groups_count()
    
    return {
        "users": users_count,
        "groups": groups_count,
        "status": "online"
    }
