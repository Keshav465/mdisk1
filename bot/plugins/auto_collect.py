import re
import os
import logging
import asyncio
import aiohttp
from pyrogram import Client, filters, types
from bot.config import Config
from bot.database import movie_db
from bot.utils import create_telegraph_post, edit_telegraph_post, remove_link, remove_mention
from tmdbv3api import TMDb, Movie, TV

# Initialize TMDb
tmdb = TMDb()
tmdb.api_key = Config.TMDB_API_KEY
tmdb_movie = Movie()
tmdb_tv = TV()

logger = logging.getLogger(__name__)

# Dictionary to store locks for each movie to prevent concurrent telegraph edits
movie_locks = {}

async def get_movie_info(query):
    # Try TMDb first
    try:
        search = await asyncio.to_thread(tmdb_movie.search, query)
        if search:
            return {
                "title": search[0].title,
                "overview": getattr(search[0], 'overview', ''),
                "poster": f"https://image.tmdb.org/t/p/w500{search[0].poster_path}" if getattr(search[0], 'poster_path', None) else None,
                "id": f"movie_{search[0].id}"
            }
        search_tv = await asyncio.to_thread(tmdb_tv.search, query)
        if search_tv:
            return {
                "title": search_tv[0].name,
                "overview": getattr(search_tv[0], 'overview', ''),
                "poster": f"https://image.tmdb.org/t/p/w500{search_tv[0].poster_path}" if getattr(search_tv[0], 'poster_path', None) else None,
                "id": f"tv_{search_tv[0].id}"
            }
    except Exception as e:
        logger.error(f"TMDb error: {e}")

    # Fallback to IMDb Worker API
    if Config.IMDB_API_URL:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{Config.IMDB_API_URL}?q={query}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Assuming common IMDb worker response format
                        if data and isinstance(data, list) and len(data) > 0:
                            item = data[0]
                            return {
                                "title": item.get("title") or item.get("name") or query,
                                "overview": item.get("description") or item.get("plot") or "",
                                "poster": item.get("image") or item.get("poster") or None,
                                "id": f"imdb_{item.get('id', query.lower().replace(' ', '_'))}"
                            }
                        elif isinstance(data, dict) and data.get("results"):
                             item = data["results"][0]
                             return {
                                "title": item.get("title") or query,
                                "overview": item.get("description") or "",
                                "poster": item.get("image") or None,
                                "id": f"imdb_{item.get('id', query.lower().replace(' ', '_'))}"
                            }
        except Exception as e:
            logger.error(f"IMDb API error: {e}")

    return {
        "title": query,
        "overview": "",
        "poster": None,
        "id": f"manual_{query.lower().replace(' ', '_')}"
    }

def clean_title(title):
    # Remove common tags, resolutions, and years
    title = re.sub(r'\(.*?\)|\[.*?\]', '', title)
    title = re.sub(r'\b(480p|720p|1080p|2160p|4k|hdr|bluray|web-dl|hdtv|x264|x265|hevc)\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\b(S\d{1,2}E\d{1,2}|Season \d{1,2}|E\d{1,2})\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\b\d{4}\b.*', '', title)
    title = title.replace('.', ' ').replace('_', ' ').replace('-', ' ').strip()
    return title

@Client.on_message(filters.chat(Config.DATABASE_CHANNEL) & (filters.video | filters.document))
async def auto_collect_handler(c: Client, m: types.Message):
    file = m.video or m.document
    if not file:
        return

    # Add a small random delay to handle batch uploads and avoid race conditions
    await asyncio.sleep(2)

    raw_title = m.caption or getattr(file, 'file_name', 'Unknown')
    title = clean_title(raw_title)
    
    info = await get_movie_info(title)
    movie_id = info["id"]
    movie_name = info["title"]
    poster = info["poster"]
    overview = info["overview"]
    
    # Use a lock for this movie_id to prevent concurrent edits
    if movie_id not in movie_locks:
        movie_locks[movie_id] = asyncio.Lock()
        
    async with movie_locks[movie_id]:
        file_data = {
            "file_id": m.id,
            "chat_id": m.chat.id,
            "file_name": getattr(file, 'file_name', 'video.mp4'),
            "file_size": file.file_size
        }

        # Add file to database
        await movie_db.add_file_to_movie(movie_id, file_data)
        
        # Get all files for this movie
        movie_data = await movie_db.get_movie(movie_id)
        files = movie_data.get("files", [])
        existing_telegraph_url = movie_data.get("telegraph_url")
        
        # Prepare Telegraph Content
        telegraph_content = f"<h3>🎬 {movie_name}</h3>"
        if poster:
            telegraph_content += f'<img src="{poster}" style="width:100%; max-width:300px; display:block; margin:auto;"><br>'
            
        if overview:
            telegraph_content += f"<p><i>{overview}</i></p>"
        
        telegraph_content += "<hr><h4>🚀 Fast Download & Stream Links:</h4><ul>"
        
        bot_username = (await c.get_me()).username
        for f in files:
            size = f"{round(f['file_size'] / (1024 * 1024), 1)} MB"
            if f['file_size'] >= 1024 * 1024 * 1024:
                size = f"{round(f['file_size'] / (1024 * 1024 * 1024), 1)} GB"
                
            link = f"https://t.me/{bot_username}?start=file_{f['file_id']}_{f['chat_id']}"
            telegraph_content += f"<li>📂 <b>{f['file_name']}</b> ({size})<br>👉 <a href='{link}'>Click Here To Watch / Download</a></li><br>"
        
        telegraph_content += "</ul><p><b>Made With ❤️ By @sdmoviespointes</b></p>"
        
        # Create/Update Telegraph Post
        if existing_telegraph_url:
            try:
                path = existing_telegraph_url.split('/')[-1]
                telegraph_url = await edit_telegraph_post(path, movie_name, telegraph_content)
            except Exception as e:
                logger.error(f"Failed to edit telegraph post: {e}")
                telegraph_url = await create_telegraph_post(movie_name, telegraph_content)
        else:
            telegraph_url = await create_telegraph_post(movie_name, telegraph_content)
        
        # Update movie with telegraph URL
        await movie_db.update_movie(movie_id, {"telegraph_url": telegraph_url, "name": movie_name})
        
        # Notify Update Channel
        if Config.UPDATE_CHANNEL:
            notification_text = (
                f"<b>🎬 New Quality Added: {movie_name}</b>\n\n"
                f"✨ <b>Total Versions:</b> {len(files)}\n"
                f"📦 <b>Latest:</b> <code>{file_data['file_name']}</code>\n\n"
                f"🔗 <b>Watch & Download Here:</b>\n{telegraph_url}"
            )
            try:
                await c.send_message(Config.UPDATE_CHANNEL, notification_text, disable_web_page_preview=False)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
