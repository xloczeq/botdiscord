import discord
import asyncio

import os
TOKEN = os.getenv("TOKEN") # Wklej tu token swojego bota
CHANNEL_ID = 1440757951689392300  # ID kanału, gdzie bot ma wysyłać wiadomości
MESSAGE = "test"  # Treść wiadomości
INTERVAL = 10  # Czas w sekundach (np. 60 = 1 minuta)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def send_message_periodically():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Nie znaleziono kanału o podanym ID")
        return

    while True:
        await channel.send(MESSAGE)
        await asyncio.sleep(INTERVAL)

@client.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {client.user}")
    # Tu startujemy zadanie
    asyncio.create_task(send_message_periodically())

client.run(TOKEN)
