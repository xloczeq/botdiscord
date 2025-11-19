import discord
import os
import asyncio
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle
from datetime import datetime
from zoneinfo import ZoneInfo
import random

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- On Ready ----------------
@bot.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print("Błąd synchronizacji:", e)

# ---------------- /godzina ----------------
@bot.tree.command(name="godzina", description="Pokazuje aktualną godzinę w Polsce")
async def godzina(interaction: discord.Interaction):
    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    await interaction.response.send_message(
        f"⏰ Jest godzina {now.hour:02d}:{now.minute:02d}", ephemeral=True
    )

# ---------------- /clear ----------------
@bot.tree.command(name="clear", description="Czyści określoną liczbę wiadomości z kanału")
@app_commands.describe(ilosc="Ile wiadomości chcesz usunąć?")
async def clear(interaction: discord.Interaction, ilosc: int):
    if ilosc < 1 or ilosc > 100:
        await interaction.response.send_message("❌ Podaj liczbę od 1 do 100.", ephemeral=True)
        return
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Nie masz uprawnień do czyszczenia wiadomości!", ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
        await interaction.response.send_message("❌ Nie mam uprawnień do usuwania wiadomości!", ephemeral=True)
        return

    await interaction.response.send_message(f"🧹 Usuwam {ilosc} wiadomości...", ephemeral=True)
    deleted = await interaction.channel.purge(limit=ilosc)
    msg = await interaction.channel.send(f"🧹 Usunięto {len(deleted)} wiadomości.")
    await asyncio.sleep(5)
    await msg.delete()

# ---------------- /komendy ----------------
@bot.tree.command(name="komendy", description="Wyświetla listę komend bota")
async def komendy(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Lista Komend Bota",
        description="Oto wszystkie dostępne komendy:",
        color=discord.Color.blurple()
    )
    embed.add_field(name="/godzina", value="Pokazuje aktualną godzinę w Polsce.", inline=False)
    embed.add_field(name="/clear <ilość>", value="Czyści podaną liczbę wiadomości w kanale.", inline=False)
    embed.add_field(name="/komendy", value="Pokazuje listę komend.", inline=False)
    embed.add_field(name="/fish", value="Łowienie ryb! Kliknij przycisk i zdobywaj XP oraz level.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ----------------- Mini gra łowienia ryb -----------------
# player_id: {'xp': int, 'level': int, 'fish': {name: count}}
players = {}

# ryby i XP
fishes = {
    "Karp": 5,
    "Pstrąg": 10,
    "Łosoś": 15,
    "Rekin": 50,
    "Legenda": 100
}

def add_xp(user_id, xp):
    if user_id not in players:
        players[user_id] = {'xp':0, 'level':1, 'fish':{}}
    players[user_id]['xp'] += xp
    # Level co 100 XP
    while players[user_id]['xp'] >= players[user_id]['level'] * 100:
        players[user_id]['xp'] -= players[user_id]['level'] * 100
        players[user_id]['level'] += 1

class FishView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @ui.button(label="🎣 Łów!", style=ButtonStyle.green)
    async def fish_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("To nie Twój fishing!", ephemeral=True)
            return

        # Losowanie ryby wg wag
        fish = random.choices(list(fishes.keys()), weights=[50,30,15,4,1])[0]
        xp = fishes[fish]

        add_xp(self.user_id, xp)

        # dodanie ryby do gracza
        player = players[self.user_id]
        player['fish'][fish] = player['fish'].get(fish, 0) + 1

        # embed aktualizujący info
        embed = discord.Embed(title="🎣 Łowienie Ryb!", color=discord.Color.green())
        embed.add_field(name="Złowiono:", value=f"{fish} (+{xp} XP)", inline=False)
        embed.add_field(name="Poziom", value=f"{player['level']}", inline=True)
        embed.add_field(name="XP", value=f"{player['xp']}/{player['level']*100}", inline=True)
        fish_list = "\n".join([f"{k}: {v}" for k,v in player['fish'].items()])
        embed.add_field(name="Twoje ryby", value=fish_list if fish_list else "Brak", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

# ----------------- /fish -----------------
@bot.tree.command(name="fish", description="Idź połowić ryby!")
async def fish(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in players:
        players[user_id] = {'xp':0, 'level':1, 'fish':{}}

    embed = discord.Embed(
        title="🎣 Łowienie Ryb!",
        description="Kliknij **Łów!** aby spróbować złowić rybę",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Masz 60 sekund na kliknięcie przycisku.")

    view = FishView(user_id)
    await interaction.response.send_message(embed=embed, view=view)

# ---------------- Uruchomienie -----------------
bot.run(TOKEN)
