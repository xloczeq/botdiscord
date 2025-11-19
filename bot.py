import discord
import os
import asyncio
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # opcjonalne
intents.messages = True

# Używamy bot zamiast client — wymagane do slash commands
bot = commands.Bot(command_prefix="!", intents=intents)


# 🔄 Synchronizacja komend
@bot.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"🔧 Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print("Błąd synchronizacji:", e)


# 🕒 /godzina
@bot.tree.command(name="godzina", description="Pokazuje aktualną godzinę w Polsce")
async def godzina(interaction: discord.Interaction):
    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    await interaction.response.send_message(
        f"⏰ Jest godzina {now.hour:02d}:{now.minute:02d}"
    )


# 🧹 /clear
@bot.tree.command(name="clear", description="Czyści określoną liczbę wiadomości z kanału")
@app_commands.describe(ilosc="Ile wiadomości chcesz usunąć?")
async def clear(interaction: discord.Interaction, ilosc: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ Nie masz uprawnień do czyszczenia wiadomości!",
            ephemeral=True
        )
        return

    if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
        await interaction.response.send_message(
            "❌ Nie mam uprawnień do usuwania wiadomości!",
            ephemeral=True
        )
        return

    await interaction.response.send_message(f"🧹 Usuwam {ilosc} wiadomości...", ephemeral=True)

    deleted = await interaction.channel.purge(limit=ilosc)
    
    msg = await interaction.channel.send(f"🧹 Usunięto {len(deleted)} wiadomości.")
    await asyncio.sleep(5)
    await msg.delete()


# 📜 /komendy
@bot.tree.command(name="komendy", description="Wyświetla listę komend bota")
async def komendy(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Lista Komend Bota",
        description="Oto wszystkie dostępne komendy:",
        color=discord.Color.blue()
    )
    embed.add_field(name="/godzina", value="Pokazuje aktualną godzinę w Polsce.", inline=False)
    embed.add_field(name="/clear <ilość>", value="Czyści podaną liczbę wiadomości z kanału.", inline=False)
    embed.add_field(name="/komendy", value="Pokazuje tę listę.", inline=False)

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)
