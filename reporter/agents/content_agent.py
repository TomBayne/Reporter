import aiohttp
from bs4 import BeautifulSoup
from typing import List
import re
from reporter.utils.http import get_browser_headers, rate_limiter
from reporter.utils.text import clean_text
from reporter.config import MIN_WORD_COUNT, MIN_TEXT_BLOCK_SIZE
import asyncio
from tqdm import tqdm
from http import HTTPStatus
from aiohttp import ClientTimeout, ClientError
from asyncio.exceptions import TimeoutError
from urllib.parse import urlparse
from itertools import groupby
from operator import itemgetter

async def fetch_article_content(url: str, session: aiohttp.ClientSession) -> str:
    """Fetch and extract content from a single article URL."""
    try:
        headers = get_browser_headers(url)
        rate_limiter.wait_if_needed(url)
        
        async with session.get(url, headers=headers, timeout=5) as response:
            if response.status != HTTPStatus.OK:
                print(f"\nHTTP {response.status} error for {url}: {response.reason}")
                return ""
                
            html = await response.text()
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove unwanted elements
            for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'nav', 
                                    'header', 'footer', 'aside', 'form']):
                tag.decompose()
            
            for tag in soup.find_all(class_=re.compile(r'(ads?|banner|social|share|comment|newsletter|subscription)')):
                tag.decompose()
            
            # Extract content using multiple strategies
            content = extract_main_content(soup)
            
            if not content:
                print(f"\nNo main content found for {url}")
                return ""
                
            text = content.get_text(separator='\n', strip=True)
            cleaned_text = clean_text(text)
            
            if len(cleaned_text.split()) < MIN_WORD_COUNT:
                print(f"\nExtracted content too short for {url} ({len(cleaned_text.split())} words < {MIN_WORD_COUNT} required)")
                return ""
                
            return cleaned_text
            
    except TimeoutError:
        print(f"\nTimeout while fetching {url}")
        return ""
    except ClientError as e:
        print(f"\nClient error for {url}: {str(e)}")
        return ""
    except Exception as e:
        print(f"\nUnexpected error extracting content from {url}: {type(e).__name__}: {str(e)}")
        return ""

def extract_main_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Extract the main content from a parsed HTML document."""
    # Try article-specific selectors first
    selectors = [
        'article', 
        '[role="article"]',
        '.article-content',
        '.post-content',
        '.entry-content',
        '.content-body',
        'main article',
        '#article-body',
        '[itemprop="articleBody"]'
    ]
    
    for selector in selectors:
        content = soup.select_one(selector)
        if content and len(content.get_text(strip=True)) > MIN_TEXT_BLOCK_SIZE:
            return content
    
    # Fallback to largest text block
    text_blocks = [
        (len(tag.get_text(strip=True)), tag)
        for tag in soup.find_all(['p', 'div'])
        if len(tag.get_text(strip=True)) > MIN_TEXT_BLOCK_SIZE
    ]
    
    return max(text_blocks, key=lambda x: x[0])[1] if text_blocks else None

def get_domain(url: str) -> str:
    """Extract domain from URL."""
    return urlparse(url).netloc

async def fetch_articles_for_domain(urls: List[str], session: aiohttp.ClientSession) -> List[tuple[str, str]]:
    """Fetch articles for a single domain sequentially."""
    results = []
    for url in urls:
        content = await fetch_article_content(url, session)
        results.append((url, content))
    return results

async def fetch_multiple_articles(urls: List[str]) -> List[str]:
    """Fetch multiple articles concurrently by domain."""
    # Group URLs by domain
    url_groups = []
    for domain, group in groupby(sorted(urls, key=get_domain), key=get_domain):
        url_groups.append(list(group))
    
    async with aiohttp.ClientSession() as session:
        all_results = []
        
        # Process each domain's URLs sequentially, but allow concurrent processing between domains
        tasks = [
            asyncio.create_task(fetch_articles_for_domain(group, session))
            for group in url_groups
        ]
        
        for task in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Processing domains"
        ):
            domain_results = await task
            all_results.extend(domain_results)
        
        # Reorder results to match input URL order
        url_to_content = dict(all_results)
        return [url_to_content.get(url, "") for url in urls]