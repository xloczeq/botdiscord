import discord
import os
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1440757951689392300

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {client.user}")

@client.event
async def on_message(message):
    # Ignoruj wiadomości od samego siebie
    if message.author == client.user:
        return

    # Komenda godzina
    if message.content.lower() == "!godzina":
        now = datetime.now(ZoneInfo("Europe/Warsaw"))
        response = f"⏰ Jest godzina {now.hour:02d}:{now.minute:02d}"
        await message.channel.send(response)

    # Komenda czyszczenia czatu
    elif message.content.lower().startswith("!clear"):
        # Sprawdzenie uprawnień użytkownika
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("❌ Nie masz uprawnień do czyszczenia wiadomości!")
            return
        
        # Opcjonalnie podanie liczby wiadomości do usunięcia, np. !clear 5
        try:
            amount = int(message.content.split()[1])
        except (IndexError, ValueError):
            amount = 10  # Domyślnie usuwa 10 wiadomości jeśli brak liczby

        deleted = await message.channel.purge(limit=amount + 1)  # +1 żeby usunąć też komendę
        await message.channel.send(f"🧹 Usunięto {len(deleted)-1} wiadomości.", delete_after=5)

client.run(TOKEN)
