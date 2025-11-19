import discord
import asyncio
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")  # Twój token bota
CHANNEL_ID = 1440757951689392300  # ID kanału, gdzie bot ma wysyłać wiadomości
INTERVAL = 3600  # co godzinę (3600 sekund)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def send_time_hourly():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Nie znaleziono kanału o podanym ID")
        return

    while True:
        current_hour = datetime.now().hour  # pobranie aktualnej godziny
        message = f"⏰ Jest godzina {current_hour}:00"
        await channel.send(message)
        await asyncio.sleep(INTERVAL)

@client.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {client.user}")
    # Uruchomienie zadania
    asyncio.create_task(send_time_hourly())

client.run(TOKEN)
