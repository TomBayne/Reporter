import discord
from discord.ext import commands
from reporter.config import DISCORD_BOT_TOKEN, DISCORD_CHANNEL_IDS, DISCORD_MESSAGE_LIMIT

def split_content(content: str) -> list[str]:
    """Split content into chunks that fit Discord's message limit."""
    if len(content) <= DISCORD_MESSAGE_LIMIT:
        return [content]
    
    chunks = []
    current_chunk = ""
    
    for paragraph in content.split('\n\n'):
        if len(current_chunk) + len(paragraph) + 2 > DISCORD_MESSAGE_LIMIT:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            current_chunk += ('\n\n' if current_chunk else '') + paragraph
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

async def post_to_discord(content: str) -> bool:
    """Post content using Discord bot."""
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_IDS:
        raise ValueError("DISCORD_BOT_TOKEN or DISCORD_CHANNEL_IDS not set")

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    try:
        print("Logging in to Discord...")
        await bot.login(DISCORD_BOT_TOKEN)
        print("Connecting to Discord...")
        await bot.connect()
        
        chunks = split_content(content)
        success = False
        
        for channel_id in DISCORD_CHANNEL_IDS:
            channel = bot.get_channel(channel_id)
            if not channel:
                print(f"Could not find Discord channel with ID: {channel_id}")
                continue
                
            print(f"Posting to channel: #{channel.name} ({channel_id})")
            for chunk in chunks:
                await channel.send(chunk)
            success = True
            
        await bot.close()
        return success
        
    except Exception as e:
        print(f"Error posting to Discord: {type(e).__name__}: {str(e)}")
        try:
            await bot.close()
        except:
            pass
        return False