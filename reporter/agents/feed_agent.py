from typing import List, Dict, Tuple
import asyncio
import feedparser
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from tqdm import tqdm
from functools import lru_cache
import requests

from reporter.utils.http import rate_limiter
from reporter.agents.content_agent import fetch_multiple_articles
from reporter.services.oai_compatible import summarize_articles, generate_final_narrative

@lru_cache(maxsize=100)
def get_feed(url: str) -> str:
    """Fetch RSS feed content with caching."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching feed {url}: {e}")
        return ""

def parse_feed(xml_data: str) -> List[Dict]:
    """Parse RSS feed content into structured data."""
    feed = feedparser.parse(xml_data)
    return [{
        'title': entry.get('title', ''),
        'link': entry.get('link', ''),
        'description': entry.get('description', ''),
        'published': entry.get('published', datetime.now().isoformat()),
        'source': feed.feed.get('title', ''),
        'content': entry.get('content', [{'value': ''}])[0].get('value', '')
    } for entry in feed.entries]

def load_feed_urls(filename: str) -> List[str]:
    """Load feed URLs from a file."""
    try:
        with open(filename, 'r') as f:
            return [url.strip() for url in f.readlines() if url.strip()]
    except FileNotFoundError:
        print(f"Feed list file not found: {filename}")
        return []
    except IOError as e:
        print(f"Error reading feed list file: {e}")
        return []

def fetch_and_parse_feed(url: str) -> List[Dict]:
    """Fetch and parse a single feed."""
    try:
        xml_data = get_feed(url)
        return parse_feed(xml_data) if xml_data else []
    except Exception as e:
        print(f"\nError processing feed {url}: {e}")
        return []

def is_article_recent(published: str, max_age_hours: int = 24) -> bool:
    """Check if an article is within the maximum age threshold."""
    try:
        # Try parsing the date directly
        pub_date = datetime.strptime(published, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        try:
            # Fallback to feedparser's date parsing
            pub_date = datetime(*feedparser._parse_date(published)[:6])
        except:
            # If all parsing fails, assume it's current
            return True
    
    age = datetime.now() - pub_date
    return age <= timedelta(hours=max_age_hours)

async def process_feeds(filename: str, fetch_full_content: bool = True) -> Tuple[List[Dict], str]:
    """Main function to process feeds and generate summaries."""
    feed_list = load_feed_urls(filename)
    all_entries = []
    
    # Fetch all feed entries concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {
            executor.submit(fetch_and_parse_feed, url): url 
            for url in feed_list
        }
        
        for future in tqdm(
            concurrent.futures.as_completed(future_to_url),
            total=len(feed_list),
            desc="Fetching feeds"
        ):
            entries = future.result()
            # Filter out old articles
            recent_entries = [
                entry for entry in entries 
                if is_article_recent(entry['published'])
            ]
            all_entries.extend(recent_entries)
    
    # Sort by published date
    all_entries.sort(key=lambda x: x['published'], reverse=True)
    
    if not fetch_full_content:
        return all_entries, ""

    # Fetch full content for entries that need it
    entries_needing_content = [
        entry for entry in all_entries 
        if not entry['content'] and entry['link']
    ]
    
    if entries_needing_content:
        print(f"\nFetching full content for {len(entries_needing_content)} articles...")
        urls = [entry['link'] for entry in entries_needing_content]
        
        # Create progress bar for individual articles
        with tqdm(total=len(urls), desc="Fetching articles") as pbar:
            contents = []
            batch_size = 1  # Process URLs in smaller batches
            for i in range(0, len(urls), batch_size):
                batch_urls = urls[i:i + batch_size]
                batch_contents = await fetch_multiple_articles(batch_urls)
                contents.extend(batch_contents)
                pbar.update(len(batch_contents))
        
        # Filter out entries where content extraction failed
        successful_entries = []
        failed_count = 0
        
        # Keep entries that didn't need content
        for entry in all_entries:
            if entry not in entries_needing_content:
                successful_entries.append(entry)
        
        # Process entries that needed content
        for entry, content in zip(entries_needing_content, contents):
            if content:
                entry['content'] = content
                successful_entries.append(entry)
            else:
                failed_count += 1
                print(f"Failed to extract: {entry['link']}")
        
        all_entries = successful_entries
        print(f"\nContent extraction complete: {len(successful_entries)} succeeded, {failed_count} failed")

    # Generate summaries and final narrative
    print("\nGenerating summaries...")
    entries_with_content = [e for e in all_entries if e.get('content')]
    
    summaries = []
    with tqdm(total=len(entries_with_content), desc="Summarizing articles") as pbar:
        for content, url in [(e['content'], e['link']) for e in entries_with_content]:
            summary = (await summarize_articles([(content, url)]))[0]
            summaries.append(summary)
            pbar.update(1)
    
    for entry, summary in zip(entries_with_content, summaries):
        entry['summary'] = summary

    print("\nGenerating final narrative...")
    narrative = await generate_final_narrative([e['summary'] for e in entries_with_content])
    
    return all_entries, narrative