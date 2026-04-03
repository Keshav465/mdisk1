from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from bot.config import Config
import os
import mimetypes
from pyrogram import Client
import logging
import asyncio
from bot.utils import decode_movie_token
from contextlib import asynccontextmanager
from bot.bot_client import Bot

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    global bot, streamer
    bot = Bot()
    
    # 🔥 Start Bot in background so the web server binds instantly
    asyncio.create_task(bot.start())
    
    streamer = MediaStreamer(bot)
    
    # 📝 Start Reminder Loop
    from bot.plugins.user_reminders import reminder_loop
    asyncio.create_task(reminder_loop(bot))
    
    logger.info("Web server successfully bound to port! ✅")
    yield
    # ── Shutdown ──
    await bot.stop()

app = FastAPI(title="SDWB2 Movie Bot API", lifespan=lifespan)
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
            file_name = getattr(file, 'file_name', 'movie.mp4') or 'movie.mp4'
            mime_type = getattr(file, 'mime_type', None) or \
                        mimetypes.guess_type(file_name)[0] or \
                        "application/octet-stream"

            range_header = request.headers.get("Range")
            start, end = 0, file_size - 1

            if range_header:
                try:
                    parts = range_header.replace("bytes=", "").split("-")
                    start = int(parts[0]) if parts[0] else 0
                    end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
                except Exception:
                    pass

            content_length = end - start + 1

            async def generate():
                async for chunk in self.client.USER.stream_media(message, offset=start, limit=content_length):
                    yield chunk

            is_download = "download" in request.query_params
            disposition = f'attachment; filename="{file_name}"' if is_download else "inline"

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": mime_type,
                "Content-Disposition": disposition,
            }
            return StreamingResponse(generate(), status_code=206, headers=headers)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


bot: Bot = None
streamer: MediaStreamer = None


# ── Pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home():
    return """<!DOCTYPE html><html><head><title>SDWB2 Movie Bot</title>
    <style>body{font-family:sans-serif;text-align:center;padding:60px;background:#0f172a;color:#e2e8f0}
    h1{font-size:2.5rem;margin-bottom:10px}a{color:#818cf8;text-decoration:none}
    a:hover{color:#6366f1}</style></head><body>
    <h1>🎬 SDWB2 Movie Bot</h1>
    <p>Bot is running fine ✅</p><br>
    <a href="/dashboard">→ Admin Dashboard</a>
    </body></html>"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return HTMLResponse(f"<h3>Dashboard Error: {e}</h3>")


@app.get("/w/{token}", response_class=HTMLResponse)
async def watch_page(request: Request, token: str):
    try:
        # Decode the secure token
        file_id, chat_id = decode_movie_token(token)
        if not file_id or not chat_id:
            return HTMLResponse("<h3>❌ Invalid or Expired Link</h3>", status_code=403)

        message = await streamer.client.get_messages(chat_id, file_id)
        if not message or not (message.video or message.document):
            return HTMLResponse("<h3>File not found</h3>", status_code=404)

        file = message.video or message.document
        file_name = str(getattr(file, 'file_name', 'Movie') or 'Movie')
        file_size = file.file_size or 0

        if file_size >= 1024 * 1024 * 1024:
            size = f"{round(file_size / (1024 * 1024 * 1024), 2)} GB"
        elif file_size >= 1024 * 1024:
            size = f"{round(file_size / (1024 * 1024), 1)} MB"
        else:
            size = f"{file_size} B"

        stream_url = f"{Config.URL}/s/{token}"
        download_url = f"{stream_url}?download=1"
        vlc_url = f"vlc://{stream_url.replace('https://', '').replace('http://', '')}"
        mx_url = f"intent:{stream_url}#Intent;package=com.mxtech.videoplayer.ad;S.title={file_name};end"
        next_url = f"intent://{stream_url.replace('https://', '').replace('http://', '')}#Intent;scheme=https;package=dev.anilbeesetti.nextplayer;S.title={file_name};end"

        # Try TMDb metadata (optional — won't crash if fails)
        poster = rating = overview = year = ""
        try:
            from bot.utils import fetch_tmdb_metadata
            meta = await fetch_tmdb_metadata(file_name)
            if isinstance(meta, dict):
                poster   = str(meta.get("poster", "") or "")
                rating   = str(meta.get("rating", "") or "")
                overview = str(meta.get("overview", "") or "")
                year     = str(meta.get("year", "") or "")
                if meta.get("title"):
                    file_name = str(meta["title"])
        except Exception as tmdb_err:
            logger.warning(f"TMDb fetch failed (non-fatal): {tmdb_err}")

        html = _build_watch_html(
            title=file_name, size=size, poster=poster, rating=rating,
            overview=overview, year=year, stream_url=stream_url,
            download_url=download_url, vlc_url=vlc_url, mx_url=mx_url, next_url=next_url
        )
        return HTMLResponse(html)

    except Exception as e:
        logger.error(f"Watch page error: {e}")
        return HTMLResponse(f"<html><body style='font-family:sans-serif;padding:40px;background:#0f172a;color:#e2e8f0'>"
                            f"<h2>⚠️ Error loading watch page</h2><p>{e}</p></body></html>", status_code=500)


def _build_watch_html(title, size, poster, rating, overview, year,
                      stream_url, download_url, vlc_url, mx_url, next_url):
    poster_html = f'<img class="poster" src="{poster}" alt="{title}"/>' if poster else '<div class="poster-ph">🎬</div>'
    rating_html = f'<span class="tag tag-y">⭐ {rating}/10</span>' if rating else ''
    year_html   = f'<span class="tag tag-b">🗓 {year}</span>' if year else ''
    overview_html = f'<p class="overview">{overview}</p>' if overview else ''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{title} — Watch &amp; Download</title>
  <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css"/>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet"/>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Outfit',sans-serif;background:#0a0f1e;color:#e2e8f0;min-height:100vh;
          display:flex;align-items:center;justify-content:center;padding:16px;
          background-image:radial-gradient(ellipse at top right,#1e1b4b,transparent 60%),
                           radial-gradient(ellipse at bottom left,#1e1b4b,transparent 60%)}}
    .card{{width:100%;max-width:820px;background:rgba(30,41,59,.55);backdrop-filter:blur(24px);
           border:1px solid rgba(255,255,255,.08);border-radius:24px;overflow:hidden;
           box-shadow:0 30px 60px rgba(0,0,0,.5)}}
    .top{{display:flex;gap:18px;padding:22px;align-items:flex-start}}
    .poster{{width:100px;min-width:100px;height:150px;border-radius:12px;object-fit:cover;box-shadow:0 8px 20px rgba(0,0,0,.5)}}
    .poster-ph{{width:100px;min-width:100px;height:150px;border-radius:12px;background:rgba(255,255,255,.05);
                display:flex;align-items:center;justify-content:center;font-size:2.4rem}}
    .info h1{{font-size:1.25rem;font-weight:700;margin-bottom:10px;line-height:1.3}}
    .tags{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px}}
    .tag{{padding:3px 12px;border-radius:999px;font-size:.75rem;font-weight:600}}
    .tag-y{{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid rgba(245,158,11,.3)}}
    .tag-b{{background:rgba(99,102,241,.15);color:#818cf8;border:1px solid rgba(99,102,241,.3)}}
    .tag-g{{background:rgba(255,255,255,.06);color:#94a3b8;border:1px solid rgba(255,255,255,.1)}}
    .overview{{font-size:.83rem;color:#94a3b8;line-height:1.6;max-height:72px;overflow:hidden}}
    .pw{{padding:0 22px}}
    .plyr{{border-radius:14px;overflow:hidden;box-shadow:0 12px 30px rgba(0,0,0,.4)}}
    .actions{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;padding:18px 22px 22px}}
    .btn{{padding:13px;border-radius:14px;text-decoration:none;font-weight:600;font-size:.87rem;
          display:flex;align-items:center;justify-content:center;gap:7px;transition:all .25s;border:none;cursor:pointer}}
    .btn-p{{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white}}
    .btn-p:hover{{transform:translateY(-2px);box-shadow:0 10px 25px rgba(99,102,241,.4)}}
    .btn-o{{background:rgba(255,255,255,.05);color:#e2e8f0;border:1px solid rgba(255,255,255,.12)}}
    .btn-o:hover{{background:rgba(255,255,255,.1);transform:translateY(-2px)}}
    footer{{text-align:center;padding:0 22px 18px;font-size:.72rem;color:rgba(255,255,255,.2)}}
    .plyr--full-ui.plyr--video .plyr__control--overlaid{{background:linear-gradient(135deg,#6366f1,#8b5cf6)}}
    .plyr--video .plyr__controls{{background:linear-gradient(transparent,rgba(0,0,0,.7))}}
    @media(max-width:480px){{.top{{flex-direction:column}}.poster,.poster-ph{{width:100%;height:160px;min-width:auto}}}}
  </style>
</head>
<body>
<div class="card">
  <div class="top">
    {poster_html}
    <div class="info">
      <h1>{title}</h1>
      <div class="tags">
        {rating_html}{year_html}
        <span class="tag tag-g">📦 {size}</span>
      </div>
      {overview_html}
    </div>
  </div>
  <div class="pw">
    <video id="player" playsinline controls>
      <source src="{stream_url}" type="video/mp4"/>
    </video>
  </div>
  <div class="actions">
    <a href="{download_url}" class="btn btn-p" download>📥 Download</a>
    <a href="{vlc_url}" class="btn btn-o" target="_blank">🧡 VLC</a>
    <a href="{mx_url}" class="btn btn-o" target="_blank">💚 MX Player</a>
    <a href="{next_url}" class="btn btn-o" target="_blank">💙 Next Player</a>
  </div>
  <footer>Powered by SDWB2 · High-Speed Telegram Streaming</footer>
</div>
<script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
<script>new Plyr('#player',{{displayDuration:true,keyboard:{{focused:true,global:true}},tooltips:{{controls:true,seek:true}}}});</script>
</body></html>"""


@app.get("/s/{token}")
async def stream_file(request: Request, token: str):
    try:
        file_id, chat_id = decode_movie_token(token)
        if not file_id or not chat_id:
            raise HTTPException(status_code=403, detail="Invalid token")
        return await streamer.get_stream(chat_id, file_id, request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Streaming error: {e}")


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
async def broadcast_api(request: Request):
    _check_auth(request)
    body = await request.json()
    text = body.get("text", "").strip()
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
