import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_MODEL = "llama-3.1-sonar-large-128k-chat"

# HTTP Configuration
MAX_CONNECTIONS = 30
MAX_RETRIES = 3
MIN_REQUEST_DELAY = 1
RANDOM_DELAY_RANGE = (1, 2)  # seconds

# Content Processing
MIN_WORD_COUNT = 50
MIN_TEXT_BLOCK_SIZE = 100

# Type definitions
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Discord Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_IDS = [int(id.strip()) for id in os.getenv('DISCORD_CHANNEL_IDS', '').split(',') if id.strip()]
DISCORD_MESSAGE_LIMIT = 2000  # Discord's max message length
DISCORD_BOT_ID = 1304943002862751764