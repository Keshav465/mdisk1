import os
import asyncio
import uvicorn
import logging
from bot import Bot
from bot.server import app, set_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot()
    await bot.start()
    set_client(bot)
    logger.info("Bot started. Launching web server...")

    port = int(os.environ.get("PORT", 8080))
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="warning"
    )
    server = uvicorn.Server(config)
    # Run both bot idle and web server concurrently
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
