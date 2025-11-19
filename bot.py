import discord
import asyncio
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")  # Twój token bota
CHANNEL_ID = 1440757951689392300  # ID kanału, gdzie bot ma wysyłać wiadomości
INTERVAL = 60  # co minutę (60 sekund)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def send_time_minutely():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Nie znaleziono kanału o podanym ID")
        return

    while True:
        now = datetime.now()
        message = f"⏰ Jest godzina {now.hour:02d}:{now.minute:02d}"
        await channel.send(message)
        await asyncio.sleep(INTERVAL)

@client.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {client.user}")
    asyncio.create_task(send_time_minutely())

client.run(TOKEN)
