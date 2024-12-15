import os
from dotenv import load_dotenv
from fake_useragent import UserAgent

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

USER_AGENTS = ua()

# Discord Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_IDS = [int(id.strip()) for id in os.getenv('DISCORD_CHANNEL_IDS', '').split(',') if id.strip()]
DISCORD_MESSAGE_LIMIT = 2000  # Discord's max message length
DISCORD_BOT_ID = 1304943002862751764