import asyncio
import argparse
from pathlib import Path
import json
from datetime import datetime
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the feed_agent module in the current directory
from reporter.agents.feed_agent import process_feeds
from reporter.services.discord import post_to_discord
from reporter.services.discord_bot import run_discord_bot
from reporter.utils.cache import get_latest_narrative

def save_results(entries, narrative, output_dir: str) -> None:
    """Save the results to JSON and text files in a timestamped folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = Path(output_dir)
    output_path = base_path / timestamp
    output_path.mkdir(parents=True, exist_ok=True)

    # Save entries to JSON
    entries_file = output_path / "entries.json"
    with open(entries_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    # Save narrative to text file
    if narrative:
        narrative_file = output_path / "narrative.md"
        with open(narrative_file, 'w', encoding='utf-8') as f:
            f.write(narrative)

    print(f"\nResults saved to {output_path}")
    print(f"- Entries: entries.json")
    if narrative:
        print(f"- Narrative: narrative.md")

async def main_async(feed_list: str, output_dir: str, fetch_content: bool) -> None:
    """Async main function that processes feeds and saves results."""
    async def generate_content():
        entries, narrative = await process_feeds(feed_list, fetch_full_content=fetch_content)
        save_results(entries, narrative, output_dir)
        return narrative

    print("\nStarting Discord bot...")
    await run_discord_bot(generate_content, output_dir)

def main():
    parser = argparse.ArgumentParser(description='Process RSS feeds and generate summaries')
    parser.add_argument('feed_list', help='Path to file containing RSS feed URLs')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory for results (default: output)')
    parser.add_argument('--no-content', action='store_true',
                       help='Skip fetching full article content')

    args = parser.parse_args()
    print(f"Processing feeds from: {args.feed_list}")
    
    try:
        asyncio.run(main_async(args.feed_list, args.output, not args.no_content))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise

if __name__ == "__main__":
    main()