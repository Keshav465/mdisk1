from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from bot.config import Config
import os
import mimetypes
from pyrogram import Client
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="SDWB2 Movie Bot API")
os.makedirs("bot/templates", exist_ok=True)
templates = Jinja2Templates(directory="bot/templates")


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
            mime_type = file.mime_type or mimetypes.guess_type(getattr(file, 'file_name', 'file'))[0] or "application/octet-stream"

            range_header = request.headers.get("Range")
            start, end = 0, file_size - 1

            if range_header:
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
                "Content-Disposition": f'attachment; filename="{getattr(file, "file_name", "file")}"'
                if "download" in request.query_params else "inline"
            }
            return StreamingResponse(generate(), status_code=206, headers=headers)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


streamer: MediaStreamer = None


def set_client(client: Client):
    global streamer
    streamer = MediaStreamer(client)


@app.get("/", response_class=HTMLResponse)
async def home():
    return """<html><body style='font-family:sans-serif;text-align:center;padding:50px;background:#0f172a;color:white'>
    <h1>🎬 SDWB2 Movie Bot</h1><p>Bot is running fine.</p>
    <a href='/dashboard' style='color:#6366f1'>Go to Admin Dashboard →</a>
    </body></html>"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/watch/{slug}", response_class=HTMLResponse)
async def watch_page(request: Request, slug: str):
    try:
        parts = slug.split("_")
        file_id = int(parts[0])
        chat_id = int(parts[1])

        message = await streamer.client.get_messages(chat_id, file_id)
        file = message.video or message.document
        file_name = getattr(file, 'file_name', 'Movie')
        size_mb = round(file.file_size / (1024 * 1024), 1)
        size = f"{size_mb} MB" if size_mb < 1024 else f"{round(size_mb/1024, 1)} GB"

        stream_url = f"{Config.URL}/stream/{slug}"
        download_url = f"{stream_url}?download=1"
        vlc_url = f"vlc://{stream_url.replace('https://', '').replace('http://', '')}"
        mx_url = f"intent:{stream_url}#Intent;package=com.mxtech.videoplayer.ad;S.title={file_name};end"

        # Try to fetch TMDb metadata
        from bot.utils import fetch_tmdb_metadata
        meta = await fetch_tmdb_metadata(file_name)

        return templates.TemplateResponse("watch.html", {
            "request": request,
            "title": meta.get("title", file_name),
            "size": size,
            "stream_url": stream_url,
            "download_url": download_url,
            "vlc_url": vlc_url,
            "mx_url": mx_url,
            "poster": meta.get("poster", ""),
            "rating": meta.get("rating", ""),
            "overview": meta.get("overview", ""),
            "year": meta.get("year", ""),
        })
    except Exception as e:
        return HTMLResponse(f"<h3>Error: {e}</h3>", status_code=500)


@app.get("/stream/{slug}")
async def stream_file(request: Request, slug: str):
    parts = slug.split("_")
    return await streamer.get_stream(int(parts[1]), int(parts[0]), request)


# ── Admin API ─────────────────────────────────────────────────────────────────

def _check_auth(request: Request):
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {Config.ADMIN_PASSWORD}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/api/stats")
async def get_stats(request: Request):
    _check_auth(request)
    from bot.database import user_db, group_db
    return {
        "users": await user_db.total_users_count(),
        "groups": await group_db.total_groups_count(),
        "status": "online"
    }


@app.post("/api/broadcast")
async def broadcast(request: Request):
    _check_auth(request)
    body = await request.json()
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    from bot.database import user_db
    import asyncio
    users = await user_db.get_all_users()
    sent, failed = 0, 0
    async for user in users:
        try:
            await streamer.client.send_message(user["user_id"], text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    return {"sent": sent, "failed": failed}
