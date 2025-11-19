import discord
import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1440757951689392300
TICKET_CATEGORY_ID = 1440791486386933781

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
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("❌ Nie masz uprawnień do czyszczenia wiadomości!")
            return

        try:
            amount = int(message.content.split()[1])
        except (IndexError, ValueError):
            amount = 10  # domyślnie 10 wiadomości

        if message.channel.permissions_for(message.guild.me).manage_messages:
            deleted = await message.channel.purge(limit=amount + 1)
            confirmation = await message.channel.send(
                f"🧹 Usunięto {len(deleted)-1} wiadomości."
            )
            await asyncio.sleep(5)
            await confirmation.delete()
        else:
            await message.channel.send(
                "❌ Nie mam uprawnień do zarządzania wiadomościami w tym kanale!"
            )

    # Komenda lista komend
    elif message.content.lower() == "!komendy":
        embed = discord.Embed(
            title="📜 Lista Komend Bota",
            description="Oto wszystkie dostępne komendy i ich opis:",
            color=discord.Color.blue()
        )
        embed.add_field(name="!godzina", value="Wyświetla aktualną godzinę i minutę w Polsce.", inline=False)
        embed.add_field(name="!clear [liczba]", value="Czyści podaną liczbę wiadomości w kanale (domyślnie 10). Wymagane uprawnienie: Manage Messages.", inline=False)
        embed.add_field(name="!komendy", value="Wyświetla tę listę komend.", inline=False)
        
        await message.channel.send(embed=embed)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # ------ ✉️ Tworzenie ticketa ------
    if message.content.lower() == "!ticket":
        guild = message.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        # Sprawdź czy user nie ma już otwartego ticketa
        for channel in category.channels:
            if channel.name == f"ticket-{message.author.id}":
                await message.channel.send("❗ Masz już otwarty ticket!")
                return

        # Tworzenie kanału
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{message.author.id}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                message.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )

        await ticket_channel.send(
            f"🎫 **Ticket otwarty!**\n"
            f"Napisz tutaj w czym mogę pomóc.\n"
            f"Użyj `!close` żeby zamknąć ticket."
        )

        await message.channel.send("📬 Ticket został utworzony!")

    # ------ ❌ Zamknięcie ticketa ------
    if message.content.lower() == "!close":
        if str(message.channel.category_id) != str(TICKET_CATEGORY_ID):
            await message.channel.send("❗ Ta komenda działa tylko w kanale ticketa!")
            return

        await message.channel.send("🗑️ Ticket zamknięty!")
        await asyncio.sleep(2)
        await message.channel.delete()


client.run(TOKEN)
