from openai import AsyncOpenAI
from typing import List
import os
from reporter.config import OAI_COMPATIBLE_API_KEY, OAI_COMPATIBLE_MODEL, OAI_COMPATIBLE_API_BASE

def load_prompt(filename: str) -> str:
    """Load prompt from a file."""
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with open(file_path, 'r') as f:
        return f.read().strip()

SUMMARIZE_ARTICLES_PROMPT = load_prompt('summarize_articles_prompt.txt')
GENERATE_NARRATIVE_PROMPT = load_prompt('generate_narrative_prompt.txt')

client = AsyncOpenAI(
    api_key=OAI_COMPATIBLE_API_KEY,
    base_url=OAI_COMPATIBLE_API_BASE
)

async def summarize_single_article(content: str, url: str) -> str:
    """Summarize a single article using the OpenAI API."""
    if not OAI_COMPATIBLE_API_KEY:
        raise ValueError("OAI_COMPATIBLE_API_KEY not set")

    response = await client.chat.completions.create(
        model=OAI_COMPATIBLE_MODEL,
        messages=[{
            "role": "user",
            "content": f"{SUMMARIZE_ARTICLES_PROMPT}\n\nArticle:\nURL: {url}\n{content[:4000]}"
        }],
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

async def summarize_articles(contents: List[tuple[str, str]]) -> List[str]:
    """Summarize multiple articles individually using the OpenAI API."""
    summaries = []
    
    for content, url in contents:
        try:
            summary = await summarize_single_article(content, url)
            summaries.append(summary)
        except Exception as e:
            print(f"Error summarizing article {url}: {e}")
            summaries.append("Failed to generate summary")
            
    return summaries

async def generate_final_narrative(summaries: List[str]) -> str:
    """Generate a final narrative from all the summaries."""
    if not OAI_COMPATIBLE_API_KEY:
        raise ValueError("OAI_COMPATIBLE_API_KEY not set")
    
    max_chars_per_summary = 2000
    truncated_summaries = [s[:max_chars_per_summary] for s in summaries]
    formatted_summaries = "\n\n---\n\n".join(truncated_summaries)
    
    response = await client.chat.completions.create(
        model=OAI_COMPATIBLE_MODEL,
        messages=[{
            "role": "user",
            "content": f"{GENERATE_NARRATIVE_PROMPT}\n\n{formatted_summaries}"
        }],
        max_tokens=4000,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()
