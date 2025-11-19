import discord
import os
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1440757951689392300

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {client.user}")

@client.event
async def on_message(message):
    # Ignoruj wiadomości od samego siebie
    if message.author == client.user:
        return

    # Sprawdź, czy wiadomość to nasza komenda
    if message.content.lower() == "!godzina":
        now = datetime.now(ZoneInfo("Europe/Warsaw"))
        response = f"⏰ Jest godzina {now.hour:02d}:{now.minute:02d}"
        await message.channel.send(response)

client.run(TOKEN)
