import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import asyncio
from reporter.config import DISCORD_BOT_TOKEN, DISCORD_CHANNEL_IDS, DISCORD_MESSAGE_LIMIT, DISCORD_BOT_ID
from typing import Callable, Awaitable
from reporter.utils.cache import get_latest_narrative

class ReporterBot(commands.Bot):
    def __init__(self, content_generator: Callable[[], Awaitable[str]], output_dir: str):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.content_generator = content_generator
        self.output_dir = output_dir

    async def setup_hook(self) -> None:
        self.scheduled_post.start()
        print("Bot is ready and scheduled posting is active")

    async def post_content(self, content: str, channel=None) -> None:
        """Post content to specified channel or default channels."""
        try:
            embeds = self.create_embeds(content)
            channels = [channel] if channel else [self.get_channel(cid) for cid in DISCORD_CHANNEL_IDS]
            channels = [c for c in channels if c is not None]
            
            for channel in channels:
                print(f"Posting to channel: #{channel.name}")
                for embed in embeds:
                    await channel.send(embed=embed)
                    await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error posting content: {type(e).__name__}: {str(e)}")

    @tasks.loop(time=time(hour=20))  # 8 PM
    async def scheduled_post(self):
        """Daily scheduled post at 8 PM with fresh content."""
        print("Running scheduled post - generating fresh content...")
        try:
            content = await self.content_generator()  # Always generate fresh content at 8 PM
            if content:
                await self.post_content(content)
        except Exception as e:
            print(f"Error in scheduled post: {type(e).__name__}: {str(e)}")

    async def on_message(self, message: discord.Message):
        """Handle bot mentions using cached content when available."""
        if message.author.id == self.user.id:
            return

        if self.user.mentioned_in(message) and f'<@{DISCORD_BOT_ID}>' in message.content:
            async with message.channel.typing():
                try:
                    # Try to use cached content for mentions
                    content = get_latest_narrative(self.output_dir)
                    if not content:
                        print("No cached content available, generating fresh content...")
                        content = await self.content_generator()
                    
                    if content:
                        await self.post_content(content, message.channel)
                    else:
                        await message.channel.send("Sorry, I couldn't generate or find any content to share.")
                except Exception as e:
                    print(f"Error handling mention: {type(e).__name__}: {str(e)}")
                    await message.channel.send("Sorry, something went wrong while processing your request.")

    def create_embeds(self, content: str) -> list[discord.Embed]:
        """Create Discord embeds from content."""
        chunks = []
        current_chunk = ""
        
        for paragraph in content.split('\n\n'):
            if len(current_chunk) + len(paragraph) + 2 > 4000:  # Discord embed limit
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += ('\n\n' if current_chunk else '') + paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())

        embeds = []
        timestamp = datetime.now()
        
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title="Daily News Summary" if i == 0 else "Continued...",
                description=chunk,
                color=discord.Color.blue(),
                timestamp=timestamp
            )
            if len(chunks) > 1:
                embed.set_footer(text=f"Part {i+1}/{len(chunks)}")
            embeds.append(embed)
            
        return embeds

async def run_discord_bot(content_generator: Callable[[], Awaitable[str]], output_dir: str) -> None:
    """Run the Discord bot."""
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_IDS:
        raise ValueError("DISCORD_BOT_TOKEN or DISCORD_CHANNEL_IDS not set")

    bot = ReporterBot(content_generator, output_dir)
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)