from urllib.parse import urlparse
from collections import defaultdict
import time
import random
from typing import Dict
from reporter.config import USER_AGENTS, MIN_REQUEST_DELAY, RANDOM_DELAY_RANGE

class RateLimiter:
    def __init__(self):
        self.last_request = defaultdict(float)
        self.min_delay = MIN_REQUEST_DELAY

    def wait_if_needed(self, url: str) -> None:
        domain = urlparse(url).netloc
        elapsed = time.time() - self.last_request[domain]
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request[domain] = time.time()

def get_browser_headers(url: str) -> Dict[str, str]:
    domain = urlparse(url).netloc
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': f'https://www.google.com/search?q={domain}',
    }

rate_limiter = RateLimiter()