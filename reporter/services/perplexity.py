import httpx
from typing import List
import asyncio
import os
from reporter.config import PERPLEXITY_API_KEY, PERPLEXITY_MODEL

def load_prompt(filename: str) -> str:
    """Load prompt from a file."""
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with open(file_path, 'r') as f:
        return f.read().strip()

SUMMARIZE_ARTICLES_PROMPT = load_prompt('summarize_articles_prompt.txt')
GENERATE_NARRATIVE_PROMPT = load_prompt('generate_narrative_prompt.txt')

async def summarize_single_article(content: str, url: str) -> str:
    """Summarize a single article using the Perplexity API."""
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY not set")

    data = {
        "model": PERPLEXITY_MODEL,
        "messages": [{
            "role": "user",
            "content": f"{SUMMARIZE_ARTICLES_PROMPT}\n\nArticle:\nURL: {url}\n{content[:4000]}"
        }],
        "max_tokens": 500,
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            json=data,
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
        )
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()

async def summarize_articles(contents: List[tuple[str, str]]) -> List[str]:
    """Summarize multiple articles individually using the Perplexity API."""
    summaries = []
    
    for content, url in contents:
        try:
            summary = await summarize_single_article(content, url)
            summaries.append(summary)
        except Exception as e:
            print(f"Error summarizing article {url}: {e}")
            summaries.append("Failed to generate summary")
            
    return summaries

def parse_summaries(text: str, expected_count: int) -> List[str]:
    """Parse the API response into individual summaries."""
    summary_list = []
    current_summary = ""
    
    for line in text.split('\n'):
        if line.strip().startswith('Summary '):
            if current_summary:
                summary_list.append(current_summary.strip())
            current_summary = line.split(':', 1)[-1].strip()
        else:
            current_summary += "\n" + line.strip()
    
    if current_summary:
        summary_list.append(current_summary.strip())
        
    while len(summary_list) < expected_count:
        summary_list.append("No summary generated")
        
    return summary_list[:expected_count]

async def generate_final_narrative(summaries: List[str]) -> str:
    """Generate a final narrative from all the summaries."""
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY not set")
    
    # Ensure summaries don't exceed a reasonable length
    max_chars_per_summary = 2000
    truncated_summaries = [s[:max_chars_per_summary] for s in summaries]
    formatted_summaries = "\n\n---\n\n".join(truncated_summaries)
    
    data = {
        "model": PERPLEXITY_MODEL,
        "messages": [{
            "role": "user",
            "content": f"{GENERATE_NARRATIVE_PROMPT}\n\n{formatted_summaries}"
        }],
        "max_tokens": 4000,
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            json=data,
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
        )
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()