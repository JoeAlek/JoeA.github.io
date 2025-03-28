import os
import logging
from bot import DiscordBot

# Import Flask app for the web interface
from app import app  # This is needed for the gunicorn server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get the bot token from environment variables
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        logger.error(
            "DISCORD_BOT_TOKEN environment variable not set! Please set it and try again."
        )
        exit(1)

    # Initialize and run the bot
    bot = DiscordBot()
    logger.info("Starting Discord bot...")
    bot.run(token)
