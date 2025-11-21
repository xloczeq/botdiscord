import discord
import os
import asyncio
from discord.ext import commands
from discord import app_commands, Embed
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- Komendy -----------------
@bot.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print("Błąd synchronizacji:", e)

# godzina
@bot.tree.command(name="godzina", description="Pokazuje aktualną godzinę w Polsce")
async def godzina(interaction: discord.Interaction):
    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    await interaction.response.send_message(f"⏰ Jest godzina {now.hour:02d}:{now.minute:02d}")

# clear
@bot.tree.command(name="clear", description="Czyści wiadomości w kanale")
@app_commands.describe(ilosc="Ile wiadomości usunąć? (max 100)")
async def clear(interaction: discord.Interaction, ilosc: int):
    if ilosc < 1 or ilosc > 100:
        await interaction.response.send_message("❌ Podaj liczbę od 1 do 100.", ephemeral=True)
        return
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Nie masz uprawnień!", ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
        await interaction.response.send_message("❌ Nie mogę usuwać wiadomości!", ephemeral=True)
        return
    await interaction.response.send_message(f"🧹 Usuwam {ilosc} wiadomości...", ephemeral=True)
    deleted = await interaction.channel.purge(limit=ilosc)
    msg = await interaction.channel.send(f"🧹 Usunięto {len(deleted)} wiadomości.")
    await asyncio.sleep(5)
    await msg.delete()

# komendy
@bot.tree.command(name="komendy", description="Lista komend bota")
async def komendy(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 Lista Komend Bota", color=discord.Color.blurple())
    embed.add_field(name="/godzina", value="Pokazuje godzinę.", inline=False)
    embed.add_field(name="/clear <ilość>", value="Czyści wiadomości.", inline=False)
    embed.add_field(name="/odliczanie", value="Tworzy własne odliczanie.", inline=False)
    await interaction.response.send_message(embed=embed)

# ----------------- /odliczanie -----------------
@bot.tree.command(name="odliczanie", description="Tworzy odliczanie do wybranej daty i godziny.")
@app_commands.describe(
    tytul="Tytuł odliczania",
    data="Data i godzina końca (format: RRRR-MM-DD HH:MM)"
)
async def odliczanie(interaction: discord.Interaction, tytul: str, data: str):
    try:
        end_time = datetime.strptime(data, "%Y-%m-%d %H:%M")
    except ValueError:
        await interaction.response.send_message(
            "❌ Błędny format daty! Użyj: `RRRR-MM-DD HH:MM`", ephemeral=True
        )
        return

    now = datetime.now()
    if end_time <= now:
        await interaction.response.send_message(
            "❌ Ta data już minęła!", ephemeral=True
        )
        return

    embed = Embed(title="⏳ Nowe odliczanie!", color=0x00eaff)
    embed.add_field(name="🎯 Tytuł", value=tytul, inline=False)
    embed.add_field(name="⏰ Kończy się", value=f"<t:{int(end_time.timestamp())}:F>", inline=False)
    embed.add_field(name="👤 Utworzone przez", value=interaction.user.mention, inline=False)
    embed.set_footer(text="Odliczanie wystartowało!")

    await interaction.response.send_message(embed=embed)

    seconds = (end_time - now).total_seconds()

    await asyncio.sleep(seconds)

    end_embed = Embed(title="🎉 Odliczanie zakończone!", color=0x00ff62)
    end_embed.add_field(name="▶ Tytuł", value=tytul, inline=False)
    end_embed.add_field(name="👤 Twórca", value=interaction.user.mention, inline=False)
    end_embed.add_field(name="⏱ Zakończono", value=f"<t:{int(end_time.timestamp())}:F>", inline=False)
    end_embed.set_footer(text="Gratulacje, dotrwaliśmy!")

    await interaction.followup.send(embed=end_embed)

# ---------------- Uruchomienie -----------------
bot.run(TOKEN)
