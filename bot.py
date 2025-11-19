import discord
import os
import asyncio
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle
from datetime import datetime
from zoneinfo import ZoneInfo
import random
import time
import json

TOKEN = os.getenv("TOKEN")
DATA_FILE = "players.json"

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- Baza graczy -----------------
# player_id: {'xp': int, 'level': int, 'fish': {name: count}, 'last_fish': timestamp}
try:
    with open(DATA_FILE, "r") as f:
        players = json.load(f)
        players = {int(k): v for k,v in players.items()}
except FileNotFoundError:
    players = {}

# ryby, XP i emotki
fishes = {
    "Karp": {"xp": 5, "emoji": "🐟"},
    "Pstrąg": {"xp": 10, "emoji": "🐠"},
    "Łosoś": {"xp": 15, "emoji": "🐡"},
    "Rekin": {"xp": 50, "emoji": "🦈"},
    "Legenda": {"xp": 100, "emoji": "🐋"}
}

COOLDOWN = 30  # sekundy

def save_players():
    with open(DATA_FILE, "w") as f:
        # zamieniamy klucze int na string
        json.dump({str(k): v for k,v in players.items()}, f, indent=4)


def add_xp(user_id, xp):
    if user_id not in players:
        players[user_id] = {'xp':0, 'level':1, 'fish':{}, 'last_fish':0}
    players[user_id]['xp'] += xp
    while players[user_id]['xp'] >= players[user_id]['level'] * 100:
        players[user_id]['xp'] -= players[user_id]['level'] * 100
        players[user_id]['level'] += 1
    save_players()  # zapis po dodaniu XP

def xp_bar(player):
    total = player['level']*100
    current = player['xp']
    filled = int((current/total)*20)
    return "🟩"*filled + "⬜"*(20-filled)

# ----------------- Button do łowienia -----------------
class FishView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @ui.button(label="🎣 Łów!", style=ButtonStyle.green)
    async def fish_button(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        now = time.time()

        if user_id != self.user_id:
            await interaction.response.send_message("To nie Twój fishing!", ephemeral=True)
            return

        # cooldown
        last = players.get(user_id, {}).get('last_fish', 0)
        if now - last < COOLDOWN:
            await interaction.response.send_message(f"⏱ Poczekaj {int(COOLDOWN - (now - last))}s przed kolejnym łowieniem.", ephemeral=True)
            return
        players[user_id]['last_fish'] = now

        # Losowanie ryby wg wag
        fish_name = random.choices(list(fishes.keys()), weights=[50,30,15,4,1])[0]
        fish_info = fishes[fish_name]
        base_xp = fish_info['xp']
        emoji = fish_info['emoji']

        # mnożnik XP w zależności od poziomu
        player_level = players[user_id]['level'] if user_id in players else 1
        xp = int(base_xp * (1 + player_level * 0.1))  # +10% XP za każdy poziom

        add_xp(user_id, xp)

        # dodanie ryby
        player = players[user_id]
        player['fish'][fish_name] = player['fish'].get(fish_name, 0) + 1
        save_players()  # zapis po złowieniu ryby

        embed = discord.Embed(title="🎣 Łowienie Ryb!", color=discord.Color.green())
        embed.add_field(name="Złowiono:", value=f"{emoji} {fish_name} (+{xp} XP)", inline=False)
        embed.add_field(name="Poziom", value=f"{player['level']}", inline=True)
        embed.add_field(name="XP", value=f"{player['xp']}/{player['level']*100} {xp_bar(player)}", inline=True)
        fish_list = "\n".join([f"{fishes[f]['emoji']} {f}: {c}" for f,c in player['fish'].items()])
        embed.add_field(name="Twoje ryby", value=fish_list if fish_list else "Brak", inline=False)
        embed.set_footer(text=f"Cooldown: {COOLDOWN}s")

        await interaction.response.edit_message(embed=embed, view=self)

# ----------------- Slash komendy -----------------
@bot.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print("Błąd synchronizacji:", e)
    
    # Zapis początkowy, żeby plik powstał
    save_players()


@bot.tree.command(name="godzina", description="Pokazuje aktualną godzinę w Polsce")
async def godzina(interaction: discord.Interaction):
    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    await interaction.response.send_message(f"⏰ Jest godzina {now.hour:02d}:{now.minute:02d}")

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

@bot.tree.command(name="komendy", description="Lista komend bota")
async def komendy(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 Lista Komend Bota", color=discord.Color.blurple())
    embed.add_field(name="/godzina", value="Pokazuje godzinę.", inline=False)
    embed.add_field(name="/clear <ilość>", value="Czyści wiadomości.", inline=False)
    embed.add_field(name="/fish", value="Łowienie ryb!", inline=False)
    embed.add_field(name="/profile", value="Wyświetla Twój profil i złowione ryby.", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="fish", description="Idź połowić ryby!")
async def fish(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in players:
        players[user_id] = {'xp':0, 'level':1, 'fish':{}, 'last_fish':0}
    embed = discord.Embed(title="🎣 Łowienie Ryb!", description="Kliknij **Łów!** aby spróbować złowić rybę", color=discord.Color.blue())
    embed.set_footer(text=f"Masz 60 sekund na kliknięcie przycisku. Cooldown: {COOLDOWN}s")
    view = FishView(user_id)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="profile", description="Pokazuje Twój profil w grze łowienia ryb")
async def profile(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in players:
        await interaction.response.send_message("Nie złowiłeś jeszcze żadnej ryby!", ephemeral=True)
        return
    player = players[user_id]
    embed = discord.Embed(title=f"🎣 Profil {interaction.user.display_name}", color=discord.Color.orange())
    embed.add_field(name="Poziom", value=f"{player['level']}", inline=True)
    embed.add_field(name="XP", value=f"{player['xp']}/{player['level']*100} {xp_bar(player)}", inline=True)
    fish_list = "\n".join([f"{fishes[f]['emoji']} {f}: {c}" for f,c in player['fish'].items()])
    embed.add_field(name="Twoje ryby", value=fish_list if fish_list else "Brak", inline=False)
    await interaction.response.send_message(embed=embed)

# ---------------- Uruchomienie -----------------
bot.run(TOKEN)
