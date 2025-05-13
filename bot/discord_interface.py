import os
import discord
from dotenv import load_dotenv

# 📦 Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_IDS = [
    int(cid.strip()) for cid in os.getenv("DISCORD_CHANNEL_IDS", "").split(",") if cid.strip()
]

class DiscordReporter(discord.Client):
    def __init__(self, text, image_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.image_path = image_path

    async def on_ready(self):
        for channel_id in DISCORD_CHANNEL_IDS:
            channel = self.get_channel(channel_id)
            if channel:
                try:
                    if self.image_path and os.path.exists(self.image_path):
                        with open(self.image_path, "rb") as f:
                            file = discord.File(f)
                            await channel.send(content=self.text, file=file)
                    else:
                        await channel.send(content=self.text)
                except Exception as e:
                    print(f"❌ Failed to send to Discord channel {channel_id}: {e}")
            else:
                print(f"⚠️ Channel ID {channel_id} not found.")
        await self.close()

async def send_report_to_discord(text, image_path=None):
    intents = discord.Intents.default()
    client = DiscordReporter(text, image_path, intents=intents)
    try:
        await client.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Discord client failed to start: {e}")
