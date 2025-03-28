import os

# Bot configuration
BOT_PREFIX = "!"
BOT_NAME = "JoeA"
BOT_DESCRIPTION = "An automation and moderation tool for Discord servers"
BOT_OWNER = "Joseph Alekberov"

# Database configuration
DATABASE_PATH = "bot_database.db"

# AI API configuration (Using OpenRouter)
OPENROUTER_API_KEY = "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"
# OpenRouter API endpoint 
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemini-2.5-pro-exp-03-25:free"  # Google Gemini Pro 2.5 Experimental model on OpenRouter
MAX_TOKENS = 750  # Increased token limit for more detailed responses
TEMPERATURE = 0.6  # Lower temperature for more focused responses
ENABLE_CACHING = True  # Enable response caching for frequently asked questions

# Response optimization
RESPONSE_TIMEOUT = 15  # Maximum seconds to wait for API response
CONCURRENT_REQUESTS = 3  # Maximum concurrent API requests

# Discord configuration
COMMAND_GUILDS = os.getenv("COMMAND_GUILDS", "").split(",") if os.getenv("COMMAND_GUILDS") else None
