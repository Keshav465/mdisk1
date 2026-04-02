# FastAPI server for Streaming & Dashboard
import os
import uvicorn
import asyncio
from bot.server import app, set_client
from bot import Bot

def run_server():
    port = int(os.environ.get("PORT", 8080))
    # We use uvicorn to run the FastAPI app
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    return server.serve()

async def main():
    # Initialize the bot
    bot = Bot()
    await bot.start()
    
    # Set the bot client for the streamer
    set_client(bot)
    
    # Run the web server and the bot's idle loop together
    await asyncio.gather(
        run_server(),
        bot.loop.create_future() # Keep the bot running
    )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
