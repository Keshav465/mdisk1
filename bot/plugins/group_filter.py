from pyrogram import Client, filters, types as t
from .search_logic import perform_search

# === YAHAN BADLAV KIYA GAYA HAI ===
# Ab yeh function sirf un messages par chalega jo forward nahi kiye gaye hain.
@Client.on_message(filters.text & filters.group & ~filters.forwarded, group=3)
async def group_search_handler(c: Client, m: t.Message):
    """
    Handles search queries in group chats.
    This will ALWAYS post the Telegraph results to act as a teaser.
    """
    if m.text.startswith('/'):
        return
        
    query = m.text
    
    # Group mein hamesha direct search hoga, bina shortener ke (Telegraph page ke liye)
    await perform_search(c, m, query)
