import os
import uvicorn
import logging
from bot.server import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting web server on port {port}...")
    uvicorn.run(
        "bot.server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        import sys
        sys.exit(1)
